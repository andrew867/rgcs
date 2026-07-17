"""Safety state machine + simulated CYD device (Agents A19, A15-sim,
A21).

Fail-off is the design center: output is off at boot, only a fresh
arm lease reaches ARMED, only explicit start before expiry reaches
RUNNING, every abnormal path lands in output-off, and faults latch
until acknowledged WHILE off. There is no auto-arm and no override.

The simulator implements the exact same state machine and API surface
the firmware does, so the desktop bridge and demos exercise the real
contract before hardware exists (A21 gate: the master demo runs
entirely in simulator mode)."""

from __future__ import annotations

import hashlib
import json
import time

from .boards import BACKENDS, board_profile, pin_conflicts

STATES = ("BOOT_SAFE", "SELF_TEST", "SAFE_OFF", "RECIPE_VALID",
          "ARMED", "RUNNING", "COOLDOWN", "FAULT_LATCHED")

FAULT_CAUSES = (
    "ARM_EXPIRY", "INVALID_RECIPE", "WATCHDOG", "OVERTEMP",
    "OVERCURRENT", "SUPPLY_FAULT", "SENSOR_SATURATION",
    "RECIPE_TIMEOUT", "QUEUE_OVERFLOW", "PIN_CONFLICT",
    "BOARD_PROFILE_MISMATCH", "EMERGENCY_STOP", "FIRMWARE_EXCEPTION",
    "BROWNOUT",
)


class SafetyError(RuntimeError):
    pass


class SimDevice:
    """The simulated instrument. Every identifier and log entry
    carries SYNTHETIC; the output flag can only be True in RUNNING."""

    def __init__(self, profile: str = "SIMULATOR",
                 clock=None):
        self.profile_name = profile
        self.profile = board_profile(profile)
        self.state = "BOOT_SAFE"
        self.output_on = False
        self.recipe = None
        self.arm = None                    # {"token", "expires"}
        self.faults: list = []
        self.log: list = []
        self._prev_hash = "0"
        self._clock = clock or time.monotonic
        self._log("boot", {"profile": profile, "output": "OFF"})
        # boot -> self test -> safe off (explicit order, A15)
        self._to("SELF_TEST")
        self._log("self_test", self.self_test())
        self._to("SAFE_OFF")

    # --- logging with hash chain (A15/A13 verify) ----------------------

    def _log(self, event: str, payload: dict) -> None:
        entry = {"seq": len(self.log), "event": event,
                 "state": self.state, "synthetic": True,
                 "payload": payload, "prev": self._prev_hash}
        entry["hash"] = hashlib.sha256(json.dumps(
            {k: v for k, v in entry.items() if k != "hash"},
            sort_keys=True, default=str).encode()).hexdigest()
        self._prev_hash = entry["hash"]
        self.log.append(entry)

    def verify_log_chain(self) -> dict:
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
        return {"intact": True, "n": len(self.log)}

    # --- state machine -------------------------------------------------

    def _to(self, new: str) -> None:
        if new not in STATES:
            raise SafetyError(f"unknown state {new}")
        self.state = new
        if new != "RUNNING":
            self.output_on = False         # output only in RUNNING

    def self_test(self) -> dict:
        return {"chip": "SYNTHETIC-ESP32", "flash_mb": 4,
                "psram": False,
                "display_id": None if self.profile.get("simulated")
                else "SYNTHETIC-ILI9341",
                "board_verified": self.profile.get("verified",
                                                   False),
                "synthetic": True}

    def fault(self, cause: str, detail: str = "") -> None:
        """Any fault: output off IMMEDIATELY, state latches."""
        if cause not in FAULT_CAUSES:
            raise SafetyError(f"unknown fault cause {cause}")
        self.output_on = False
        self.faults.append({"cause": cause, "detail": detail,
                            "acknowledged": False})
        self._to("FAULT_LATCHED")
        self._log("fault", {"cause": cause, "detail": detail,
                            "output": "OFF"})

    def acknowledge_faults(self) -> dict:
        """Faults clear only while output is off (it always is in
        FAULT_LATCHED) and only by explicit acknowledgement."""
        if self.state != "FAULT_LATCHED":
            raise SafetyError("no latched fault to acknowledge")
        for f in self.faults:
            f["acknowledged"] = True
        self._to("SAFE_OFF")
        self._log("faults_acknowledged", {"n": len(self.faults)})
        return {"cleared": len(self.faults)}

    # --- recipe / arm / run --------------------------------------------

    def load_recipe(self, recipe: dict, validator) -> dict:
        """Validation happens BEFORE the state advances; an invalid
        recipe faults rather than half-loading (A12 gate: invalid
        JSON never reaches the output driver)."""
        if self.state not in ("SAFE_OFF", "RECIPE_VALID"):
            raise SafetyError(f"cannot load in {self.state}")
        result = validator(recipe)
        if not result["valid"]:
            self.fault("INVALID_RECIPE", "; ".join(result["errors"]))
            return {"loaded": False, **result}
        # pin conflicts are a load-time fault (A19 list)
        pins = recipe.get("device_requirements", {}).get(
            "output_pins", [])
        if pins:
            pc = pin_conflicts(self.profile_name, pins)
            if pc["conflicts"]:
                self.fault("PIN_CONFLICT", str(pc["conflicts"]))
                return {"loaded": False,
                        "errors": [str(pc["conflicts"])]}
        self.recipe = json.loads(json.dumps(recipe))
        self._to("RECIPE_VALID")
        self._log("recipe_loaded",
                  {"recipe_id": recipe["recipe_id"]})
        return {"loaded": True, "errors": []}

    def request_arm(self, ttl_s: float = 30.0) -> dict:
        """A fresh lease; single use; expires. There is no auto-arm
        path anywhere in this class (orchestrator prohibition)."""
        if self.state != "RECIPE_VALID":
            raise SafetyError(f"arm refused in {self.state}: load a "
                              "valid recipe first")
        token = hashlib.sha256(
            f"{self.recipe['recipe_id']}|{self._clock()}".encode()
        ).hexdigest()[:16]
        self.arm = {"token": token,
                    "expires": self._clock() + ttl_s}
        self._to("ARMED")
        self._log("armed", {"ttl_s": ttl_s})
        return {"token": token, "ttl_s": ttl_s}

    def start(self, token: str) -> dict:
        if self.state != "ARMED":
            raise SafetyError(f"start refused in {self.state}")
        if self.arm is None or token != self.arm["token"]:
            self.fault("INVALID_RECIPE", "wrong arm token")
            return {"started": False}
        if self._clock() > self.arm["expires"]:
            self.fault("ARM_EXPIRY", "lease expired before start")
            return {"started": False}
        self.arm = None                    # single use
        self._to("RUNNING")
        self.output_on = True
        self._log("run_start",
                  {"recipe_id": self.recipe["recipe_id"],
                   "output": "ON(SYNTHETIC)"})
        return {"started": True}

    def stop(self) -> dict:
        if self.state == "RUNNING":
            self.output_on = False
            self._to("COOLDOWN")
            self._log("run_stop", {"output": "OFF"})
            self._to("SAFE_OFF")
            return {"stopped": True}
        return {"stopped": False, "state": self.state}

    def emergency_stop(self) -> None:
        self.fault("EMERGENCY_STOP", "operator")

    def simulate_reset(self) -> None:
        """Watchdog/brownout/reset: the device reboots into BOOT_SAFE
        with output off — verified by test (A15 gate)."""
        self.output_on = False
        self.recipe = None
        self.arm = None
        self.state = "BOOT_SAFE"
        self._log("reset", {"output": "OFF"})
        self._to("SELF_TEST")
        self._to("SAFE_OFF")

    # --- telemetry ------------------------------------------------------

    def status(self) -> dict:
        return {"state": self.state, "output_on": self.output_on,
                "profile": self.profile_name,
                "board_verified": self.profile.get("verified",
                                                   False),
                "faults": [f for f in self.faults
                           if not f["acknowledged"]],
                "synthetic": True,
                "banner": "SYNTHETIC DEVICE — no hardware exists"}

    def capabilities(self) -> dict:
        from .boards import capability_report
        return {"profile": self.profile_name,
                "backends": capability_report(),
                "frequency_min_hz": 1,
                "frequency_max_hz": 200_000,
                "max_duty": 0.5, "max_continuous_s": 60,
                "synthetic": True}

    def run_segments(self, plant=None, seed: int = 0) -> dict:
        """Execute the loaded recipe against the synthetic plant while
        RUNNING; returns per-segment realized-frequency records."""
        if self.state != "RUNNING":
            raise SafetyError("not running")
        out = []
        elapsed = 0.0
        for seg in self.recipe["segments"]:
            backend = BACKENDS.get(seg.get("backend", "SIMULATOR"))
            real = backend.realize(str(seg["frequency_hz"]))
            elapsed += float(seg["duration_s"])
            limit = self.recipe["limits"]["max_continuous_s"]
            if elapsed > limit:
                self.fault("RECIPE_TIMEOUT",
                           f"{elapsed}s > {limit}s")
                return {"completed": False, "segments": out}
            out.append({"segment": seg.get("label", "?"),
                        "requested_hz": str(real["requested_hz"]),
                        "calculated_realized_hz":
                            str(real["calculated_realized_hz"]),
                        "measured_realized_hz": None,
                        "synthetic": True})
            self._log("segment", out[-1])
        self.stop()
        return {"completed": True, "segments": out,
                "synthetic": True}
