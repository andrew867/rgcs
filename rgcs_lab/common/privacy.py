"""Privacy-safe local defaults for the lab server and static hub."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrivacyDefaults:
    """Defaults that keep the demonstrator local and telemetry-free."""

    bind_host: str = "127.0.0.1"
    bind_port: int = 8765
    allow_remote_bind: bool = False
    telemetry: bool = False
    outbound_network: bool = False
    persist_operator_transcripts: bool = False
    share_location_corpus: bool = False


def privacy_banner() -> str:
    d = PrivacyDefaults()
    return (
        f"privacy: host={d.bind_host} telemetry={d.telemetry} "
        f"outbound={d.outbound_network} "
        "no private operator transcripts in public builds"
    )
