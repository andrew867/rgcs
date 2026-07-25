"""P07 — the protocol runner: compile a frozen plan and run it, honestly.

A frozen :class:`~r15.protocols.Protocol` is a plan; this module executes
it. Execution is deliberately bounded by what the environment can produce:
a synthetic run is deterministic and yields a ``SYNTHETIC_OBSERVATION``,
never a physical measurement, and a real run is not performed at all --- it
is recorded as ``PREREGISTERED_NOT_RUN``, because no apparatus exists here.

**Compile before run.** :func:`compile_plan` takes a sealed protocol and a
configuration, verifies the seal (a broken seal is refused), checks the
configuration is *authorized* for every capability the steps bind to (an
unavailable capability is refused *before* any acquisition), and returns
the ordered sequence of step operations. Nothing is acquired until the
plan compiles.

**Four distinct modes.** :class:`ExecutionMode` keeps ``REAL``, ``REPLAY``,
``SYNTHETIC`` and ``FAULT_INJECTION`` separate and unmixable. ``REAL``
never runs (there is no bench); ``SYNTHETIC`` runs a seeded deterministic
simulator; ``REPLAY`` re-emits caller-supplied recorded frames; ``FAULT_
INJECTION`` deterministically injects a fault and terminates on the
protocol's fault stop condition. A synthetic reading is never labelled a
measurement.

**Determinism.** Given the same sealed protocol, configuration and seed, a
synthetic run produces byte-identical raw artifacts and the same run hash.
Timestamps and epochs are passed in, never read from a clock.

**Stop conditions terminate.** :func:`compile_plan` and :func:`execute`
honour the protocol's stop conditions -- a ``MAX_ACQUISITIONS`` limit ends
the run after N acquisitions, a ``FAULT_DETECTED`` condition ends a fault
run -- so a run's length is fixed by the frozen plan, not chosen mid-run.

The output is an :class:`ExperimentRun` matching
``experiment_run.schema.json``. :func:`protocol_runner_report` records a
claim class of ``SYNTHETIC_OBSERVATION`` and the standing verdict
``PROTOCOL_COMPILED_AND_RUN_SYNTHETIC_NO_PHYSICAL_MEASUREMENT``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import serialize as r13_serialize
from r15 import claims as r15_claims
from r15 import protocols as r15_protocols
from r15.protocols import (Maneuver, Protocol, ProtocolStep, SealedProtocol,
                           StepKind, StopKind, compile_hash)

#: The standing verdict for a compiled-and-synthetically-run protocol.
DEFAULT_VERDICT = (
    "PROTOCOL_COMPILED_AND_RUN_SYNTHETIC_NO_PHYSICAL_MEASUREMENT")

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The claim class a synthetic run is entitled to. A simulator output is a
#: SYNTHETIC_OBSERVATION, never a PHYSICAL_MEASUREMENT.
SYNTHETIC_CLAIM_CLASS = r15_claims.ClaimClass.SYNTHETIC_OBSERVATION.value


class RunnerError(RuntimeError):
    """Raised on a broken seal, an unauthorized configuration, a capability
    the configuration cannot provide, a REPLAY with no frames, or an
    attempt to read a synthetic run as a physical measurement."""


class ExecutionMode(Enum):
    """The four execution modes, kept strictly distinct.

    ``REAL`` is never executed here (no apparatus); ``SYNTHETIC`` runs a
    seeded deterministic simulator; ``REPLAY`` re-emits recorded frames;
    ``FAULT_INJECTION`` injects a deterministic fault. A run carries the
    mode it was produced under, and its claim class follows from that."""

    REAL = "REAL"
    SYNTHETIC = "SYNTHETIC"
    REPLAY = "REPLAY"
    FAULT_INJECTION = "FAULT_INJECTION"


# =======================================================================
# The run configuration
# =======================================================================

@dataclass(frozen=True)
class RunConfig:
    """The configuration a run executes under.

    ``authorized_capabilities`` is the set the operator is cleared for; a
    protocol step whose capability is not in it is refused before
    acquisition. ``calibration_id`` must be present for any step that
    ``requires_calibration``. ``seed`` makes a synthetic run deterministic.
    ``environment`` and ``clock`` are passed-in descriptors (no clock is
    read). ``replay_frames`` supplies the recorded readings a REPLAY mode
    re-emits."""

    specimen_id: str
    fixture_id: str
    calibration_id: str
    authorized_capabilities: frozenset
    mode: ExecutionMode
    seed: int
    environment: dict = field(default_factory=dict)
    clock: dict = field(default_factory=dict)
    replay_frames: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ExecutionMode):
            raise RunnerError("mode must be an ExecutionMode")
        if not isinstance(self.authorized_capabilities, (set, frozenset)):
            object.__setattr__(self, "authorized_capabilities",
                               frozenset(self.authorized_capabilities))

    def authorizes(self, capability: str) -> bool:
        return capability in self.authorized_capabilities


# =======================================================================
# The experiment run record
# =======================================================================

@dataclass(frozen=True)
class ExperimentRun:
    """The record a run produces, matching ``experiment_run.schema.json``.

    ``raw_artifacts`` are the deterministic synthetic readings (empty for a
    REAL run, which is never performed). ``status`` reflects the mode:
    ``PREREGISTERED_NOT_RUN`` for REAL, ``SYNTHETIC_RUN_COMPLETE`` for a
    synthetic run, and so on. ``claim_class`` is never a measurement
    class."""

    run_id: str
    protocol_id: str
    specimen_id: str
    fixture_id: str
    instrument_bindings: tuple
    environment: dict
    clock: dict
    raw_artifacts: tuple
    status: str
    mode: str
    seed: int
    protocol_seal: str
    claim_class: str
    steps_executed: int
    stopped_by: str | None

    def to_record(self) -> dict:
        """The dict matching ``experiment_run.schema.json``."""
        return {
            "run_id": self.run_id,
            "protocol_id": self.protocol_id,
            "specimen_id": self.specimen_id,
            "fixture_id": self.fixture_id,
            "instrument_bindings": list(self.instrument_bindings),
            "environment": dict(self.environment),
            "clock": dict(self.clock),
            "raw_artifacts": list(self.raw_artifacts),
            "status": self.status,
            "mode": self.mode,
            "seed": self.seed,
            "protocol_seal": self.protocol_seal,
            "claim_class": self.claim_class,
            "steps_executed": self.steps_executed,
            "stopped_by": self.stopped_by,
        }

    def run_hash(self) -> str:
        """A stable content hash of the run record (reuses R13 serialize)."""
        return r13_serialize.content_hash(self.to_record())


# =======================================================================
# Compilation: verify the seal, authorize the config, order the steps
# =======================================================================

@dataclass(frozen=True)
class CompiledStep:
    """One authorized operation in a compiled plan."""

    index: int
    kind: str
    capability: str
    maneuver: str | None
    requires_calibration: bool


def compile_plan(sealed: SealedProtocol, config: RunConfig) -> tuple:
    """Verify, authorize and order a frozen protocol into runnable steps.

    Three gates, all before any acquisition. First the seal is verified:
    an edited protocol whose hash no longer matches its seal is refused.
    Second, every step's capability must be authorized by the config, and
    every calibration-requiring step must have a bound calibration; an
    unavailable capability is refused here, not discovered mid-run. Third,
    the steps are returned in index order as :class:`CompiledStep`s."""
    if not isinstance(sealed, SealedProtocol):
        raise RunnerError("first argument must be a SealedProtocol")
    if not isinstance(config, RunConfig):
        raise RunnerError("second argument must be a RunConfig")
    if not sealed.verify():
        raise RunnerError(
            f"refused: the protocol seal is broken. The frozen seal is "
            f"{sealed.seal}, but the carried protocol now hashes to "
            f"{compile_hash(sealed.protocol)}. A protocol edited after "
            f"freezing may not be executed under the old seal; freeze the "
            f"new version and run that.")
    protocol = sealed.protocol
    # Capability authorization -- BEFORE acquisition.
    for step in protocol.steps:
        if not config.authorizes(step.capability):
            raise RunnerError(
                f"refused: step {step.index} ({step.kind.value}) needs "
                f"capability {step.capability!r}, which the configuration is "
                f"not authorized for. The run is refused before any "
                f"acquisition; authorize the capability or remove the step. "
                f"Authorized: {sorted(config.authorized_capabilities)}.")
        if step.requires_calibration and not config.calibration_id.strip():
            raise RunnerError(
                f"refused: step {step.index} requires a bound calibration, "
                f"but the configuration carries no calibration_id. An "
                f"acquisition against an uncalibrated instrument is refused.")
    return tuple(
        CompiledStep(
            index=s.index, kind=s.kind.value,
            capability=s.capability,
            maneuver=s.maneuver.value if s.maneuver else None,
            requires_calibration=s.requires_calibration)
        for s in protocol.steps)


# =======================================================================
# Synthetic acquisition: deterministic under a seed
# =======================================================================

def _synthetic_reading(protocol_seal: str, step: ProtocolStep, seed: int,
                       fault: bool = False) -> dict:
    """A deterministic synthetic reading for one acquisition step.

    The RNG is seeded from the protocol seal, the step index and the config
    seed, so the reading is a pure function of (plan, step, seed): the same
    inputs always yield the same numbers, and different plans or seeds yield
    different ones. When ``fault`` is set, the reading is flagged and its
    value is driven out of band -- the fault-injection maneuver."""
    # Derive a stable integer seed from the plan/step/config seed.
    mix = int(protocol_seal[:8], 16) ^ (step.index * 2654435761) ^ int(seed)
    rng = np.random.default_rng(mix & 0xFFFFFFFF)
    base = rng.normal(0.0, 1.0, size=8)
    setpoint_ref = float(sum(sp.value for sp in step.setpoints))
    values = (base + (0.0 if setpoint_ref == 0.0 else 1.0)).tolist()
    reading = {
        "step_index": step.index,
        "maneuver": step.maneuver.value if step.maneuver else None,
        "setpoint_sum": setpoint_ref,
        "samples": [round(v, 12) for v in values],
        "fault": bool(fault),
    }
    if fault:
        reading["samples"] = [v + 1.0e6 for v in reading["samples"]]
        reading["fault_code"] = "INJECTED_SATURATION"
    return reading


def _stop_limit(protocol: Protocol, kind: StopKind) -> float | None:
    for sc in protocol.stop_conditions:
        if sc.kind is kind:
            return sc.limit
    return None


# =======================================================================
# Execution
# =======================================================================

def execute(sealed: SealedProtocol, config: RunConfig, *,
            run_id: str, epoch: int) -> ExperimentRun:
    """Compile and run a frozen protocol, producing an ExperimentRun.

    ``REAL`` mode returns immediately with status ``PREREGISTERED_NOT_RUN``
    and no artifacts: no apparatus exists, so the plan is recorded as ready
    but unrun. The other three modes compile the plan (seal + authorization
    gates) and then walk the acquisition steps deterministically, honouring
    the ``MAX_ACQUISITIONS`` and ``FAULT_DETECTED`` stop conditions. A
    synthetic run's readings are a pure function of (plan, config, seed)."""
    if not isinstance(config, RunConfig):
        raise RunnerError("config must be a RunConfig")
    protocol = sealed.protocol
    bindings = tuple(protocol.required_capabilities())

    if config.mode is ExecutionMode.REAL:
        # No bench exists. Verify the seal so a broken plan is still caught,
        # but perform nothing and claim nothing.
        if not sealed.verify():
            raise RunnerError(
                "refused: the protocol seal is broken; a REAL run cannot be "
                "preregistered against an edited plan.")
        return ExperimentRun(
            run_id=run_id, protocol_id=protocol.protocol_id,
            specimen_id=config.specimen_id, fixture_id=config.fixture_id,
            instrument_bindings=bindings, environment=dict(config.environment),
            clock=dict(config.clock, epoch=int(epoch)), raw_artifacts=(),
            status="PREREGISTERED_NOT_RUN", mode=config.mode.value,
            seed=int(config.seed), protocol_seal=sealed.seal,
            claim_class="PREREGISTERED_NOT_RUN", steps_executed=0,
            stopped_by="REAL_MODE_NOT_RUN_NO_APPARATUS")

    # SYNTHETIC / REPLAY / FAULT_INJECTION all compile first.
    plan = compile_plan(sealed, config)
    max_acq = _stop_limit(protocol, StopKind.MAX_ACQUISITIONS)

    artifacts: list = []
    acquisitions = 0
    steps_executed = 0
    stopped_by: str | None = None
    fault_mode = config.mode is ExecutionMode.FAULT_INJECTION

    for compiled, step in zip(plan, protocol.steps):
        steps_executed += 1
        if step.kind is not StepKind.ACQUIRE:
            continue
        acquisitions += 1
        if config.mode is ExecutionMode.REPLAY:
            if acquisitions - 1 >= len(config.replay_frames):
                raise RunnerError(
                    f"refused: REPLAY mode ran out of recorded frames at "
                    f"acquisition {acquisitions}; supply a replay_frame per "
                    f"acquisition step or use SYNTHETIC mode.")
            reading = dict(config.replay_frames[acquisitions - 1])
            reading.setdefault("step_index", step.index)
        else:
            # FAULT_INJECTION drives a fault on the first acquisition.
            inject = fault_mode and acquisitions == 1
            reading = _synthetic_reading(sealed.seal, step, config.seed,
                                         fault=inject)
        artifacts.append(reading)

        # Stop conditions, evaluated as the run proceeds.
        if fault_mode and reading.get("fault"):
            stopped_by = "FAULT_DETECTED"
            break
        if max_acq is not None and acquisitions >= int(max_acq):
            stopped_by = "MAX_ACQUISITIONS"
            break

    if config.mode is ExecutionMode.SYNTHETIC:
        status = "SYNTHETIC_RUN_COMPLETE"
        claim_class = SYNTHETIC_CLAIM_CLASS
    elif config.mode is ExecutionMode.REPLAY:
        status = "REPLAY_RUN_COMPLETE"
        claim_class = SYNTHETIC_CLAIM_CLASS
    else:  # FAULT_INJECTION
        status = "FAULT_INJECTION_RUN_COMPLETE"
        claim_class = SYNTHETIC_CLAIM_CLASS

    return ExperimentRun(
        run_id=run_id, protocol_id=protocol.protocol_id,
        specimen_id=config.specimen_id, fixture_id=config.fixture_id,
        instrument_bindings=bindings, environment=dict(config.environment),
        clock=dict(config.clock, epoch=int(epoch)),
        raw_artifacts=tuple(artifacts), status=status, mode=config.mode.value,
        seed=int(config.seed), protocol_seal=sealed.seal,
        claim_class=claim_class, steps_executed=steps_executed,
        stopped_by=stopped_by)


def dry_run(sealed: SealedProtocol, config: RunConfig) -> dict:
    """Validate a protocol against a configuration without acquiring.

    A dry run compiles the plan -- verifying the seal and authorizing every
    capability -- and reports what a real compilation would do, but touches
    no simulator and produces no artifacts. It is the no-hardware validation
    path: it answers "would this run compile?" deterministically."""
    plan = compile_plan(sealed, config)
    return {
        "compiles": True,
        "seal_verified": sealed.verify(),
        "protocol_id": sealed.protocol.protocol_id,
        "seal": sealed.seal,
        "n_steps": len(plan),
        "n_acquisitions": sum(1 for s in plan if s.kind == "ACQUIRE"),
        "required_capabilities":
            list(sealed.protocol.required_capabilities()),
        "authorized": sorted(config.authorized_capabilities),
        "mode": config.mode.value,
    }


# =======================================================================
# The refusals
# =======================================================================

def refuse_synthetic_as_measurement(run: ExperimentRun | None = None,
                                    *_a, **_k) -> None:
    """Refuse to read a synthetic (or replay) run as a physical measurement.

    The runner operated a deterministic simulator, not an instrument on a
    specimen. Its readings are a SYNTHETIC_OBSERVATION -- reproducible from
    the seed -- and there is no promotion from that to PHYSICAL_MEASUREMENT
    in R15. This delegates to the claim taxonomy's standing refusal."""
    r15_claims.refuse_synthetic_as_physical()


def refuse_run_unauthorized(*_a, **_k) -> None:
    """Refuse to run a configuration authorized for none of the steps.

    Executing a protocol against a configuration that is not cleared for
    the capabilities its steps bind to would acquire under an authority the
    operator does not hold. The gate is in :func:`compile_plan`; this names
    the refusal for the red team."""
    raise RunnerError(
        "refused: a protocol may not be executed under a configuration that "
        "is not authorized for the capabilities its steps require. "
        "Authorization is checked at compile time, before any acquisition.")


# =======================================================================
# The report
# =======================================================================

def protocol_runner_report() -> dict:
    sealed = r15_protocols.example_seal()
    authorized = frozenset(sealed.protocol.required_capabilities())
    config = RunConfig(
        specimen_id="SYN_SPECIMEN_0", fixture_id="SYN_FIXTURE_0",
        calibration_id="SYN_CAL_0", authorized_capabilities=authorized,
        mode=ExecutionMode.SYNTHETIC, seed=20260724,
        environment={"T_K": 300.0, "note": "synthetic"},
        clock={"tick_hz": 1.0})
    run_a = execute(sealed, config, run_id="RUN_A", epoch=1000)
    run_b = execute(sealed, config, run_id="RUN_A", epoch=1000)
    real_cfg = RunConfig(
        specimen_id="SYN_SPECIMEN_0", fixture_id="SYN_FIXTURE_0",
        calibration_id="SYN_CAL_0", authorized_capabilities=authorized,
        mode=ExecutionMode.REAL, seed=0)
    real_run = execute(sealed, real_cfg, run_id="RUN_REAL", epoch=1000)
    return {
        "what_this_is": (
            "a runner that compiles a frozen protocol -- verifying its seal "
            "and authorizing every capability before acquisition -- and "
            "executes it deterministically against synthetic devices, "
            "keeping REAL, SYNTHETIC, REPLAY and FAULT_INJECTION modes "
            "distinct"),
        "modes": [m.value for m in ExecutionMode],
        "example_protocol_id": sealed.protocol.protocol_id,
        "example_seal": sealed.seal,
        "synthetic_run_status": run_a.status,
        "synthetic_run_claim_class": run_a.claim_class,
        "synthetic_run_n_artifacts": len(run_a.raw_artifacts),
        "synthetic_run_stopped_by": run_a.stopped_by,
        "determinism_same_seed": run_a.run_hash() == run_b.run_hash(),
        "real_run_status": real_run.status,
        "real_run_is_not_run": real_run.status == "PREREGISTERED_NOT_RUN",
        "real_run_n_artifacts": len(real_run.raw_artifacts),
        "refusals": [
            "refuse_synthetic_as_measurement",
            "refuse_run_unauthorized",
        ],
        "claim_class": SYNTHETIC_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not measure anything. A synthetic run operates a seeded "
            "deterministic simulator and yields a SYNTHETIC_OBSERVATION, "
            "reproducible from the seed and never a PHYSICAL_MEASUREMENT. A "
            "REAL run is not performed at all -- there is no apparatus in "
            "this environment -- so it is recorded as PREREGISTERED_NOT_RUN "
            "with no artifacts. The runner enforces that a plan is frozen "
            "and a configuration authorized before it will acquire, and "
            "refuses any promotion of a simulator output to a measurement."),
    }
