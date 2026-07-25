"""P26 — the ESP32 / embedded experiment runner: a deterministic twin.

This module is a *software model* of an embedded controller (an ESP32-class
board driving a DDS-style output stage) that executes a compiled protocol
recipe. **No firmware is compiled and no board is flashed** -- there is no
toolchain and no hardware in this environment -- so the runner is a
deterministic simulator that implements the exact state machine, safety
interlocks and event contract the firmware would, and nothing more. It lets
the host evidence ledger exercise the real embedded contract before any
board exists.

**Fail-off is the design center.** Output is off at boot; only a fresh
single-use arm lease reaches ``ARMED``; only an explicit ``start`` before
the lease expires reaches ``RUNNING``; and every abnormal path -- a lost
heartbeat, a watchdog timeout, an over-range setpoint, an over-temperature
reading, an emergency stop -- drives the output off and latches a fault
that clears only by explicit acknowledgement while the output is already
off. There is no auto-arm and no override.

**Loss of heartbeat stops safely.** The controller is driven by explicit
integer epochs (never a wall clock). While ``RUNNING`` it expects a
heartbeat each watchdog window; when the gap since the last heartbeat
exceeds ``watchdog_timeout_ticks`` the watchdog fires, the output goes off,
and the controller latches a ``HEARTBEAT_LOST`` fault. Nothing keeps the
output on without a live heartbeat.

**Bounded outputs, refused when exceeded.** Every commanded setpoint is
checked against conservative, configurable :class:`SafetyLimits`
(frequency band, amplitude ceiling, duty ceiling). An out-of-band command
is *refused* -- :func:`refuse_unsafe_output` raises before the output stage
is touched -- and an out-of-band recipe faults at load rather than
half-loading.

**Hash-chained event log.** Every state transition and safety event is
appended to a tamper-evident log whose entries chain by SHA-256;
:meth:`EmbeddedController.verify_log_chain` recomputes the chain and reports
the first break.

**A twin is not a board.** A recipe run against the twin is a
``SYNTHETIC_OBSERVATION`` reproducible from a seed -- never a
``PHYSICAL_MEASUREMENT``. Reading a twin run as a hardware measurement is
refused (:func:`refuse_twin_as_hardware_run`), and a real deployment to a
board is ``BLOCKED_MISSING_INPUT``: no board exists to flash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import serialize as r13_serialize
from r15 import claims as r15_claims

#: The standing verdict for this module.
VERDICT = "EMBEDDED_RUNNER_TWIN_FAIL_OFF_NO_HARDWARE"

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: A recipe run against the twin is a synthetic observation, never a
#: measurement.
TWIN_CLAIM_CLASS = r15_claims.ClaimClass.SYNTHETIC_OBSERVATION.value

#: The status a real board deployment is recorded under: there is no board.
NO_BOARD_STATUS = "BLOCKED_MISSING_INPUT"


# =======================================================================
# Typed errors
# =======================================================================

class EmbeddedRunnerError(RuntimeError):
    """Base for every embedded-runner refusal and safety violation."""


class SafetyError(EmbeddedRunnerError):
    """An illegal state transition or an unknown fault/state."""


class UnsafeOutputError(EmbeddedRunnerError):
    """A commanded setpoint or recipe segment is outside the safety limits."""


class ArmLeaseError(EmbeddedRunnerError):
    """A run was attempted without a valid, unexpired arm lease."""


class TwinAsHardwareError(EmbeddedRunnerError):
    """A twin (simulator) run was read as a physical hardware measurement."""


# =======================================================================
# States, faults, modes
# =======================================================================

class EmbeddedState(Enum):
    """The controller state machine. Output can be on only in ``RUNNING``."""

    BOOT_SAFE = "BOOT_SAFE"
    SELF_TEST = "SELF_TEST"
    SAFE_OFF = "SAFE_OFF"
    RECIPE_VALID = "RECIPE_VALID"
    ARMED = "ARMED"
    RUNNING = "RUNNING"
    COOLDOWN = "COOLDOWN"
    FAULT_LATCHED = "FAULT_LATCHED"


class FaultCause(Enum):
    """Every latched fault cause. Each drives the output off immediately."""

    INVALID_RECIPE = "INVALID_RECIPE"
    ARM_EXPIRY = "ARM_EXPIRY"
    HEARTBEAT_LOST = "HEARTBEAT_LOST"
    WATCHDOG = "WATCHDOG"
    OVER_RANGE = "OVER_RANGE"
    OVERTEMP = "OVERTEMP"
    RECIPE_TIMEOUT = "RECIPE_TIMEOUT"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    TWIN_ASSERTED_AS_HARDWARE = "TWIN_ASSERTED_AS_HARDWARE"


class RunMode(Enum):
    """The four modes, kept strictly distinct.

    ``TWIN`` runs the deterministic simulator; ``REPLAY`` re-emits recorded
    frames; ``FAULT_INJECTION`` injects a deterministic fault; ``REAL`` is
    never run here -- there is no board to flash."""

    TWIN = "TWIN"
    REPLAY = "REPLAY"
    FAULT_INJECTION = "FAULT_INJECTION"
    REAL = "REAL"


# =======================================================================
# Safety limits and setpoints
# =======================================================================

@dataclass(frozen=True)
class SafetyLimits:
    """Conservative, configurable output and interlock limits.

    The defaults are deliberately small: a narrow frequency band, a
    fractional amplitude ceiling, a duty ceiling well under continuous, a
    short maximum continuous run, a modest over-temperature trip, and a
    tight watchdog window. Every commanded setpoint and every recipe
    segment is checked against these before the output stage is engaged."""

    min_frequency_hz: float = 1.0
    max_frequency_hz: float = 100_000.0
    max_amplitude: float = 1.0
    max_duty: float = 0.5
    max_continuous_ticks: int = 60
    max_temp_c: float = 70.0
    watchdog_timeout_ticks: int = 5

    def violations(self, setpoint: "OutputSetpoint") -> list[str]:
        """List every way a setpoint violates these limits (empty == safe)."""
        v: list[str] = []
        if not (self.min_frequency_hz <= setpoint.frequency_hz
                <= self.max_frequency_hz):
            v.append(
                f"frequency {setpoint.frequency_hz} Hz outside "
                f"[{self.min_frequency_hz}, {self.max_frequency_hz}]")
        if not (0.0 <= setpoint.amplitude <= self.max_amplitude):
            v.append(
                f"amplitude {setpoint.amplitude} outside "
                f"[0, {self.max_amplitude}]")
        if not (0.0 <= setpoint.duty <= self.max_duty):
            v.append(f"duty {setpoint.duty} outside [0, {self.max_duty}]")
        return v

    def to_record(self) -> dict:
        return {
            "min_frequency_hz": self.min_frequency_hz,
            "max_frequency_hz": self.max_frequency_hz,
            "max_amplitude": self.max_amplitude,
            "max_duty": self.max_duty,
            "max_continuous_ticks": self.max_continuous_ticks,
            "max_temp_c": self.max_temp_c,
            "watchdog_timeout_ticks": self.watchdog_timeout_ticks,
        }


@dataclass(frozen=True)
class OutputSetpoint:
    """A DDS-style output setpoint: frequency, amplitude, duty."""

    frequency_hz: float
    amplitude: float
    duty: float

    def to_record(self) -> dict:
        return {"frequency_hz": self.frequency_hz,
                "amplitude": self.amplitude, "duty": self.duty}


@dataclass(frozen=True)
class RecipeSegment:
    """One segment of a recipe: hold a setpoint for a number of ticks."""

    label: str
    setpoint: OutputSetpoint
    duration_ticks: int

    def to_record(self) -> dict:
        return {"label": self.label, "setpoint": self.setpoint.to_record(),
                "duration_ticks": int(self.duration_ticks)}


@dataclass(frozen=True)
class EmbeddedRecipe:
    """A compiled protocol/DDS recipe: an ordered list of bounded segments
    plus the safety limits they are checked against."""

    recipe_id: str
    segments: tuple
    limits: SafetyLimits = field(default_factory=SafetyLimits)

    def to_record(self) -> dict:
        return {"recipe_id": self.recipe_id,
                "segments": [s.to_record() for s in self.segments],
                "limits": self.limits.to_record()}

    def compile_hash(self) -> str:
        """A stable content hash of the compiled recipe (reuses R13)."""
        return r13_serialize.content_hash(self.to_record())

    def validate(self) -> dict:
        """Validate every segment against the limits, before any run.

        A recipe with an out-of-band setpoint or a total duration over the
        maximum continuous run is invalid and must never reach the output
        driver."""
        errors: list[str] = []
        if not self.segments:
            errors.append("recipe has no segments")
        total = 0
        for i, seg in enumerate(self.segments):
            if seg.duration_ticks <= 0:
                errors.append(f"segment {i} ({seg.label}): non-positive "
                              f"duration {seg.duration_ticks}")
            total += int(seg.duration_ticks)
            for msg in self.limits.violations(seg.setpoint):
                errors.append(f"segment {i} ({seg.label}): {msg}")
        if total > self.limits.max_continuous_ticks:
            errors.append(
                f"total duration {total} ticks exceeds max continuous "
                f"{self.limits.max_continuous_ticks}")
        return {"valid": not errors, "errors": errors}


# =======================================================================
# The run record (experiment_run.schema.json shaped)
# =======================================================================

@dataclass(frozen=True)
class TwinRun:
    """The record a twin run produces, matching experiment_run.schema.json.

    ``raw_artifacts`` are the deterministic per-segment realized setpoints.
    ``claim_class`` is a synthetic observation and never a measurement
    class; ``status`` reflects how the run ended."""

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
    recipe_hash: str
    claim_class: str
    stopped_by: str | None
    log_chain_head: str

    def to_record(self) -> dict:
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
            "recipe_hash": self.recipe_hash,
            "claim_class": self.claim_class,
            "stopped_by": self.stopped_by,
            "log_chain_head": self.log_chain_head,
        }

    def run_hash(self) -> str:
        return r13_serialize.content_hash(self.to_record())


# =======================================================================
# The controller twin
# =======================================================================

class EmbeddedController:
    """The deterministic embedded-controller twin.

    It implements the same fail-off state machine and safety interlocks the
    firmware would, driven entirely by explicit integer epochs. Every
    identifier and log entry carries ``synthetic``; the output flag can only
    be True in ``RUNNING``."""

    def __init__(self, boot_epoch: int = 0,
                 limits: SafetyLimits | None = None,
                 profile: str = "SYNTHETIC-ESP32"):
        self.profile = profile
        self.limits = limits or SafetyLimits()
        self.state = EmbeddedState.BOOT_SAFE
        self.output_on = False
        self.recipe: EmbeddedRecipe | None = None
        self.arm: dict | None = None            # {"token", "expires"}
        self.last_heartbeat: int = int(boot_epoch)
        self.faults: list = []
        self.log: list = []
        self._prev_hash = "0"
        self._log(int(boot_epoch), "boot",
                  {"profile": profile, "output": "OFF"})
        self._to(EmbeddedState.SELF_TEST, int(boot_epoch))
        self._log(int(boot_epoch), "self_test", self.self_test())
        self._to(EmbeddedState.SAFE_OFF, int(boot_epoch))

    # --- hash-chained event log ----------------------------------------

    def _log(self, epoch: int, event: str, payload: dict) -> None:
        entry = {"seq": len(self.log), "epoch": int(epoch), "event": event,
                 "state": self.state.value, "output_on": self.output_on,
                 "synthetic": True, "payload": payload,
                 "prev": self._prev_hash}
        entry["hash"] = hashlib.sha256(json.dumps(
            {k: v for k, v in entry.items() if k != "hash"},
            sort_keys=True, default=str).encode()).hexdigest()
        self._prev_hash = entry["hash"]
        self.log.append(entry)

    def verify_log_chain(self) -> dict:
        """Recompute the chain; report the first break, if any."""
        prev = "0"
        for e in self.log:
            if e["prev"] != prev:
                return {"intact": False, "broken_at": e["seq"]}
            h = hashlib.sha256(json.dumps(
                {k: v for k, v in e.items() if k != "hash"},
                sort_keys=True, default=str).encode()).hexdigest()
            if h != e["hash"]:
                return {"intact": False, "broken_at": e["seq"]}
            prev = e["hash"]
        return {"intact": True, "n": len(self.log), "head": self._prev_hash}

    # --- state machine -------------------------------------------------

    def _to(self, new: EmbeddedState, epoch: int) -> None:
        if not isinstance(new, EmbeddedState):
            raise SafetyError(f"unknown state {new!r}")
        self.state = new
        if new is not EmbeddedState.RUNNING:
            self.output_on = False              # output only in RUNNING

    def self_test(self) -> dict:
        return {"chip": self.profile, "firmware_compiled": False,
                "board_flashed": False, "synthetic": True}

    def fault(self, cause: FaultCause, epoch: int, detail: str = "") -> None:
        """Any fault: output off immediately, state latches until acked."""
        if not isinstance(cause, FaultCause):
            raise SafetyError(f"unknown fault cause {cause!r}")
        self.output_on = False
        self.arm = None
        self.faults.append({"cause": cause.value, "detail": detail,
                            "acknowledged": False})
        self._to(EmbeddedState.FAULT_LATCHED, epoch)
        self._log(epoch, "fault", {"cause": cause.value, "detail": detail,
                                   "output": "OFF"})

    def acknowledge_faults(self, epoch: int) -> dict:
        """Faults clear only while output is off (always so in
        FAULT_LATCHED) and only by explicit acknowledgement."""
        if self.state is not EmbeddedState.FAULT_LATCHED:
            raise SafetyError("no latched fault to acknowledge")
        n = len(self.faults)
        for f in self.faults:
            f["acknowledged"] = True
        self._to(EmbeddedState.SAFE_OFF, epoch)
        self._log(epoch, "faults_acknowledged", {"n": n})
        return {"cleared": n}

    # --- recipe / arm / run --------------------------------------------

    def load_recipe(self, recipe: EmbeddedRecipe, epoch: int) -> dict:
        """Validate before advancing; an invalid recipe faults rather than
        half-loading, so an out-of-band segment never reaches the output."""
        if self.state not in (EmbeddedState.SAFE_OFF,
                               EmbeddedState.RECIPE_VALID):
            raise SafetyError(f"cannot load recipe in {self.state.value}")
        result = recipe.validate()
        if not result["valid"]:
            self.fault(FaultCause.INVALID_RECIPE, epoch,
                       "; ".join(result["errors"]))
            return {"loaded": False, **result}
        self.recipe = recipe
        self._to(EmbeddedState.RECIPE_VALID, epoch)
        self._log(epoch, "recipe_loaded",
                  {"recipe_id": recipe.recipe_id,
                   "recipe_hash": recipe.compile_hash()})
        return {"loaded": True, "errors": []}

    def request_arm(self, epoch: int, ttl_ticks: int = 10) -> dict:
        """A fresh single-use lease that expires. No auto-arm path exists."""
        if self.state is not EmbeddedState.RECIPE_VALID:
            raise ArmLeaseError(
                f"arm refused in {self.state.value}: load a valid recipe "
                f"first")
        token = hashlib.sha256(
            f"{self.recipe.recipe_id}|{epoch}|{self.recipe.compile_hash()}"
            .encode()).hexdigest()[:16]
        self.arm = {"token": token, "expires": int(epoch) + int(ttl_ticks)}
        self._to(EmbeddedState.ARMED, epoch)
        self._log(epoch, "armed", {"ttl_ticks": int(ttl_ticks)})
        return {"token": token, "expires": self.arm["expires"]}

    def start(self, token: str, epoch: int) -> dict:
        """Reach RUNNING only from ARMED, with a matching, unexpired lease."""
        if self.state is not EmbeddedState.ARMED:
            raise ArmLeaseError(
                f"start refused in {self.state.value}: no arm lease held")
        if self.arm is None or token != self.arm["token"]:
            self.fault(FaultCause.ARM_EXPIRY, epoch, "wrong arm token")
            raise ArmLeaseError("start refused: wrong arm token")
        if int(epoch) > self.arm["expires"]:
            self.fault(FaultCause.ARM_EXPIRY, epoch,
                       "lease expired before start")
            raise ArmLeaseError("start refused: arm lease expired")
        self.arm = None                          # single use
        self.last_heartbeat = int(epoch)
        self._to(EmbeddedState.RUNNING, epoch)
        self.output_on = True
        self._log(epoch, "run_start",
                  {"recipe_id": self.recipe.recipe_id,
                   "output": "ON(SYNTHETIC)"})
        return {"started": True}

    def heartbeat(self, epoch: int) -> None:
        """Refresh the watchdog. Only meaningful while RUNNING."""
        if self.state is EmbeddedState.RUNNING:
            self.last_heartbeat = int(epoch)
            self._log(epoch, "heartbeat", {"epoch": int(epoch)})

    def check_watchdog(self, epoch: int) -> bool:
        """Fail off if the heartbeat gap exceeds the watchdog window.

        Returns True if the watchdog fired. This is the loss-of-heartbeat
        interlock: without a live heartbeat the output cannot stay on."""
        if self.state is not EmbeddedState.RUNNING:
            return False
        if int(epoch) - self.last_heartbeat > self.limits.watchdog_timeout_ticks:
            self.fault(FaultCause.HEARTBEAT_LOST, epoch,
                       f"no heartbeat for "
                       f"{int(epoch) - self.last_heartbeat} ticks")
            return True
        return False

    def report_temperature(self, temp_c: float, epoch: int) -> bool:
        """Over-temperature interlock: trip to safe state if too hot."""
        if temp_c > self.limits.max_temp_c and \
                self.state is EmbeddedState.RUNNING:
            self.fault(FaultCause.OVERTEMP, epoch,
                       f"{temp_c} C > {self.limits.max_temp_c} C")
            return True
        return False

    def command_output(self, setpoint: OutputSetpoint, epoch: int) -> dict:
        """Apply a setpoint while RUNNING; refuse anything out of band.

        An out-of-band command is refused before the output stage is
        touched -- the output is driven off and the run is faulted."""
        if self.state is not EmbeddedState.RUNNING:
            raise SafetyError(
                f"cannot command output in {self.state.value}; "
                f"the output is off")
        violations = self.limits.violations(setpoint)
        if violations:
            self.fault(FaultCause.OVER_RANGE, epoch, "; ".join(violations))
            raise UnsafeOutputError(
                f"refused: setpoint out of bounds ({'; '.join(violations)}); "
                f"the output stage is not engaged and the run is faulted")
        self._log(epoch, "output_command", setpoint.to_record())
        return {"applied": True, "setpoint": setpoint.to_record()}

    def emergency_stop(self, epoch: int) -> None:
        self.fault(FaultCause.EMERGENCY_STOP, epoch, "operator")

    def stop(self, epoch: int) -> dict:
        if self.state is EmbeddedState.RUNNING:
            self.output_on = False
            self._to(EmbeddedState.COOLDOWN, epoch)
            self._log(epoch, "run_stop", {"output": "OFF"})
            self._to(EmbeddedState.SAFE_OFF, epoch)
            return {"stopped": True}
        return {"stopped": False, "state": self.state.value}

    def status(self) -> dict:
        return {"state": self.state.value, "output_on": self.output_on,
                "profile": self.profile,
                "faults": [f for f in self.faults
                           if not f["acknowledged"]],
                "synthetic": True,
                "banner": "SYNTHETIC TWIN — no board exists, no firmware "
                          "compiled"}


# =======================================================================
# Running a recipe deterministically
# =======================================================================

def _realized_setpoint(recipe_hash: str, seg_index: int, seed: int,
                       setpoint: OutputSetpoint, fault: bool) -> dict:
    """A deterministic realized setpoint for one segment.

    The RNG is seeded from the recipe hash, the segment index and the run
    seed, so the realized values are a pure function of (recipe, segment,
    seed). The tiny deterministic offset models DDS quantization; a fault
    drives the amplitude out of band."""
    mix = int(recipe_hash[:8], 16) ^ (seg_index * 2654435761) ^ int(seed)
    rng = np.random.default_rng(mix & 0xFFFFFFFF)
    quant = float(rng.normal(0.0, 1.0)) * 1e-6
    realized = {
        "segment_index": seg_index,
        "requested": setpoint.to_record(),
        "realized_frequency_hz": round(setpoint.frequency_hz + quant, 9),
        "measured_frequency_hz": None,
        "fault": bool(fault),
        "synthetic": True,
    }
    if fault:
        realized["realized_amplitude"] = setpoint.amplitude + 1.0e6
        realized["fault_code"] = "INJECTED_OVER_RANGE"
    return realized


def run_recipe(recipe: EmbeddedRecipe, *, run_id: str, seed: int,
               epoch: int, mode: RunMode = RunMode.TWIN,
               specimen_id: str = "SYN_SPECIMEN",
               fixture_id: str = "SYN_FIXTURE",
               environment: dict | None = None,
               replay_frames: tuple = (),
               limits: SafetyLimits | None = None) -> TwinRun:
    """Compile and run a recipe on the twin, producing a TwinRun.

    ``REAL`` mode is never executed here: it returns a
    ``BLOCKED_MISSING_INPUT`` run with no artifacts, because there is no
    board to flash. The other three modes drive a fresh controller through
    boot -> load -> arm -> start -> per-segment output -> stop, feeding a
    heartbeat each segment so the watchdog is satisfied, and record the
    realized setpoints. A ``FAULT_INJECTION`` run drives the first segment
    out of band and terminates on the over-range interlock. The run is a
    pure function of (recipe, seed, epoch, mode)."""
    environment = dict(environment or {"T_K": 300.0, "note": "synthetic"})
    bindings = ("SYNTHETIC-ESP32", "DDS-OUTPUT-STAGE(SYNTHETIC)")
    clock = {"epoch": int(epoch), "tick": "integer", "wall_clock": False}

    if mode is RunMode.REAL:
        # No board exists. Record the blocked state honestly; flash nothing.
        return TwinRun(
            run_id=run_id, protocol_id=recipe.recipe_id,
            specimen_id=specimen_id, fixture_id=fixture_id,
            instrument_bindings=bindings, environment=environment,
            clock=clock, raw_artifacts=(), status=NO_BOARD_STATUS,
            mode=mode.value, seed=int(seed),
            recipe_hash=recipe.compile_hash(),
            claim_class=NO_BOARD_STATUS, stopped_by="NO_BOARD_TO_FLASH",
            log_chain_head="0")

    ctrl = EmbeddedController(boot_epoch=epoch, limits=limits or recipe.limits)
    loaded = ctrl.load_recipe(recipe, epoch)
    if not loaded["loaded"]:
        raise UnsafeOutputError(
            f"refused: recipe {recipe.recipe_id} failed validation: "
            f"{loaded['errors']}")
    lease = ctrl.request_arm(epoch, ttl_ticks=max(10, len(recipe.segments)))
    ctrl.start(lease["token"], epoch)

    artifacts: list = []
    stopped_by: str | None = None
    tick = int(epoch)
    fault_mode = mode is RunMode.FAULT_INJECTION
    for i, seg in enumerate(recipe.segments):
        ctrl.heartbeat(tick)                     # keep the watchdog satisfied
        inject = fault_mode and i == 0
        if mode is RunMode.REPLAY:
            if i >= len(replay_frames):
                raise EmbeddedRunnerError(
                    f"refused: REPLAY ran out of frames at segment {i}")
            realized = dict(replay_frames[i])
            realized.setdefault("segment_index", i)
        else:
            realized = _realized_setpoint(recipe.compile_hash(), i, seed,
                                          seg.setpoint, inject)
        artifacts.append(realized)
        ctrl._log(tick, "segment", realized)
        if inject:
            ctrl.fault(FaultCause.OVER_RANGE, tick, "injected over-range")
            stopped_by = "FAULT_INJECTED_OVER_RANGE"
            break
        tick += int(seg.duration_ticks)
    else:
        ctrl.stop(tick)
        stopped_by = "RECIPE_COMPLETE"

    status = ("FAULT_INJECTION_RUN_COMPLETE" if fault_mode
              else "REPLAY_RUN_COMPLETE" if mode is RunMode.REPLAY
              else "TWIN_RUN_COMPLETE")
    chain = ctrl.verify_log_chain()
    return TwinRun(
        run_id=run_id, protocol_id=recipe.recipe_id, specimen_id=specimen_id,
        fixture_id=fixture_id, instrument_bindings=bindings,
        environment=environment, clock=clock, raw_artifacts=tuple(artifacts),
        status=status, mode=mode.value, seed=int(seed),
        recipe_hash=recipe.compile_hash(), claim_class=TWIN_CLAIM_CLASS,
        stopped_by=stopped_by, log_chain_head=chain.get("head", "0"))


# =======================================================================
# The refusals
# =======================================================================

def refuse_unsafe_output(setpoint: OutputSetpoint,
                         limits: SafetyLimits) -> None:
    """Refuse a setpoint outside the safety limits.

    A commanded output beyond the frequency band, amplitude ceiling, or
    duty ceiling is refused before the output stage is engaged. The named
    refusal for the red team; the live gate is in
    :meth:`EmbeddedController.command_output`."""
    violations = limits.violations(setpoint)
    if violations:
        raise UnsafeOutputError(
            f"refused: output setpoint out of bounds: "
            f"{'; '.join(violations)}. The output stage is never engaged "
            f"outside its conservative limits.")


def refuse_run_without_arm_lease(controller: EmbeddedController) -> None:
    """Refuse to run without a fresh, unexpired, single-use arm lease.

    Output can be engaged only from ``ARMED`` with a matching lease. A run
    without an arm lease would engage the output stage with no explicit
    single-use authorization; that is refused."""
    if controller.state is not EmbeddedState.ARMED or controller.arm is None:
        raise ArmLeaseError(
            "refused: a recipe may not run without a fresh single-use arm "
            "lease. Load a valid recipe, request an arm lease, and start "
            "before it expires; there is no auto-arm path.")


def refuse_twin_as_hardware_run(run: TwinRun | None = None,
                                *_a, **_k) -> None:
    """Refuse to read a twin run as a physical hardware measurement.

    The runner operated a deterministic software model of an embedded
    controller, not a flashed board driving a real output stage on a
    specimen. Its realized setpoints are a ``SYNTHETIC_OBSERVATION``,
    reproducible from the seed, and there is no promotion from that to a
    ``PHYSICAL_MEASUREMENT`` -- no firmware was compiled and no board
    exists. Delegates to the claim taxonomy's standing refusal."""
    raise TwinAsHardwareError(
        "refused: a twin (simulator) run is not a hardware measurement. No "
        "firmware was compiled and no board was flashed; the realized "
        "setpoints are a SYNTHETIC_OBSERVATION reproducible from the seed, "
        "never a PHYSICAL_MEASUREMENT.")


def deploy_to_board(recipe: EmbeddedRecipe, *_a, **_k) -> dict:
    """A real deployment to a board: BLOCKED_MISSING_INPUT.

    There is no board and no toolchain in this environment, so nothing is
    compiled or flashed. The recipe and twin are complete; only the
    physical deployment is blocked."""
    return {
        "deployed": False,
        "status": NO_BOARD_STATUS,
        "recipe_id": recipe.recipe_id,
        "recipe_hash": recipe.compile_hash(),
        "reason": ("no ESP32/embedded board and no build toolchain are "
                   "present; firmware is not compiled and no board is "
                   "flashed"),
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
    }


# =======================================================================
# An example recipe
# =======================================================================

def example_recipe() -> EmbeddedRecipe:
    """A small, in-bounds three-segment DDS recipe for demos and tests."""
    limits = SafetyLimits()
    return EmbeddedRecipe(
        recipe_id="TWIN_RECIPE_0",
        segments=(
            RecipeSegment("ramp_lo",
                          OutputSetpoint(1_000.0, 0.2, 0.25), 5),
            RecipeSegment("hold_mid",
                          OutputSetpoint(10_000.0, 0.4, 0.30), 10),
            RecipeSegment("ramp_hi",
                          OutputSetpoint(50_000.0, 0.5, 0.40), 5),
        ),
        limits=limits)


# =======================================================================
# The report
# =======================================================================

def embedded_runner_report() -> dict:
    recipe = example_recipe()
    run_a = run_recipe(recipe, run_id="RUN_A", seed=20260724, epoch=1000)
    run_b = run_recipe(recipe, run_id="RUN_A", seed=20260724, epoch=1000)
    fault_run = run_recipe(recipe, run_id="RUN_F", seed=1, epoch=1000,
                           mode=RunMode.FAULT_INJECTION)
    real_run = run_recipe(recipe, run_id="RUN_REAL", seed=0, epoch=1000,
                          mode=RunMode.REAL)

    # Fail-off on lost heartbeat, driven by explicit epochs.
    ctrl = EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(recipe, 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    watchdog_fired = ctrl.check_watchdog(
        ctrl.limits.watchdog_timeout_ticks + 1)

    return {
        "what_this_is": (
            "a deterministic software twin of an ESP32/embedded controller "
            "that executes a compiled DDS recipe under a fail-off state "
            "machine, with arm leases, a heartbeat watchdog, latched faults, "
            "bounded outputs and a hash-chained event log; no firmware is "
            "compiled and no board is flashed"),
        "states": [s.value for s in EmbeddedState],
        "fault_causes": [c.value for c in FaultCause],
        "modes": [m.value for m in RunMode],
        "example_recipe_id": recipe.recipe_id,
        "example_recipe_hash": recipe.compile_hash(),
        "twin_run_status": run_a.status,
        "twin_run_claim_class": run_a.claim_class,
        "twin_run_n_artifacts": len(run_a.raw_artifacts),
        "twin_run_stopped_by": run_a.stopped_by,
        "determinism_same_seed": run_a.run_hash() == run_b.run_hash(),
        "log_chain_intact": (
            run_a.log_chain_head != "0"),
        "fault_run_stopped_by": fault_run.stopped_by,
        "fault_run_output_never_measured": (
            fault_run.claim_class == TWIN_CLAIM_CLASS),
        "watchdog_fires_on_lost_heartbeat": watchdog_fired,
        "output_off_after_watchdog": not ctrl.output_on,
        "state_after_watchdog": ctrl.state.value,
        "real_deploy_status": real_run.status,
        "real_deploy_is_blocked": real_run.status == NO_BOARD_STATUS,
        "real_deploy_n_artifacts": len(real_run.raw_artifacts),
        "refusals": [
            "refuse_unsafe_output",
            "refuse_run_without_arm_lease",
            "refuse_twin_as_hardware_run",
        ],
        "firmware_compiled": False,
        "board_flashed": False,
        "claim_class": TWIN_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not measure anything and it does not run on a board. "
            "The twin is a deterministic software model of an embedded "
            "controller: a recipe run yields a SYNTHETIC_OBSERVATION "
            "reproducible from the seed, never a PHYSICAL_MEASUREMENT. No "
            "firmware is compiled and no board is flashed; a real deployment "
            "is BLOCKED_MISSING_INPUT. The runner enforces fail-off safety -- "
            "output off at boot, a single-use arm lease to arm, a heartbeat "
            "watchdog and over-range/over-temperature interlocks that drive "
            "the output off and latch a fault -- and refuses any promotion "
            "of a twin run to a hardware measurement."),
    }
