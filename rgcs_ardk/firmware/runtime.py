"""Default-off firmware state model with interlock and heartbeat gating."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

from rgcs_ardk.drive import AuthorityBundle


class RuntimeRefused(RuntimeError):
    """Raised when reference firmware cannot enter the armed state."""


def _config_digest(authority: AuthorityBundle) -> str:
    joined = "".join(f"{name}:{authority.hashes[name]}\n" for name in sorted(authority.hashes))
    return hashlib.sha256(joined.encode("ascii")).hexdigest()


@dataclass
class ReferenceRuntime:
    authority: AuthorityBundle
    heartbeat_timeout_s: float = 0.25
    enabled: bool = False
    fault_flags: set[str] = field(default_factory=set)
    _last_heartbeat_s: float | None = None

    @property
    def config_hash(self) -> str:
        return _config_digest(self.authority)

    def arm(
        self,
        *,
        supplied_config_hash: str,
        now_s: float,
        enclosure_closed: bool,
        sensors_valid: bool,
        hardware_limit_present: bool,
    ) -> None:
        if supplied_config_hash != self.config_hash:
            raise RuntimeRefused("configuration hash mismatch")
        if not enclosure_closed or not sensors_valid or not hardware_limit_present:
            raise RuntimeRefused("required hardware interlock is not satisfied")
        self.fault_flags.clear()
        self._last_heartbeat_s = now_s
        self.enabled = True

    def heartbeat(self, now_s: float) -> None:
        if self.enabled:
            self._last_heartbeat_s = now_s

    def tick(
        self,
        *,
        now_s: float,
        enclosure_closed: bool = True,
        sensors_valid: bool = True,
        overtemperature: bool = False,
    ) -> None:
        if not self.enabled:
            return
        if not enclosure_closed:
            self.disarm("ENCLOSURE_OPEN")
        elif not sensors_valid:
            self.disarm("SENSOR_INVALID")
        elif overtemperature:
            self.disarm("OVERTEMPERATURE")
        elif self._last_heartbeat_s is None or now_s - self._last_heartbeat_s > self.heartbeat_timeout_s:
            self.disarm("HEARTBEAT_TIMEOUT")

    def disarm(self, reason: str | None = None) -> None:
        self.enabled = False
        if reason:
            self.fault_flags.add(reason)
