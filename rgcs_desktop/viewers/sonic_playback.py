"""Live playback for Frequency Key Studio previews (QtMultimedia).

Playback is optional: when the Qt multimedia backend is unavailable
(minimal CI images, stripped frozen builds) every entry point degrades
to a stated message instead of crashing."""
from __future__ import annotations

from pathlib import Path


def playback_available() -> tuple[bool, str]:
    try:
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment specific
        return False, f"QtMultimedia unavailable: {exc}"
    return True, ""


class PreviewPlayer:
    """Plays a rendered WAV file; keeps Qt objects alive; reports
    errors through the status callback instead of raising."""

    def __init__(self, status_cb):
        self._status_cb = status_cb
        self._player = None
        self._output = None

    def play(self, wav_path: str | Path) -> bool:
        ok, reason = playback_available()
        if not ok:
            self._status_cb(f"playback unavailable — {reason}")
            return False
        from PySide6.QtCore import QUrl
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
        self.stop()
        self._player = QMediaPlayer()
        self._output = QAudioOutput()
        self._output.setVolume(0.6)
        self._player.setAudioOutput(self._output)
        self._player.errorOccurred.connect(
            lambda _err, text="": self._status_cb(
                f"playback error: {text or _err}"))
        self._player.setSource(QUrl.fromLocalFile(str(Path(wav_path))))
        self._player.play()
        self._status_cb(f"playing {Path(wav_path).name} (comfortable "
                        f"volume; stereo headphones for binaural)")
        return True

    def stop(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._player = None
            self._output = None

    @property
    def active(self) -> bool:
        return self._player is not None
