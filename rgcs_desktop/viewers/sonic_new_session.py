"""Frequency Key Studio — New Session page (wizard-style form)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem,
                               QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from rgcs_core.provenance import json_dumps

from rgcs_desktop.services.design_studio import new_object_id
from rgcs_desktop.services.sonic_audio import binaural_pair
from rgcs_desktop.services.sonic_exports import (
    export_bundle, export_recipe_json, export_session_pdf,
    export_youtube_metadata_sheet, render_session_wav, verify_bundle)
from rgcs_desktop.services.sonic_recipes import (USER_NOTE,
                                                 load_beat_targets)
from rgcs_desktop.services.sonic_timeline import (TimelineError,
                                                  standard_session_shape)

SESSION_TYPES = ("binaural", "monaural", "isochronic", "noise_bed",
                 "composite")
CARRIER_FAMILY = [100.0, 110.0, 136.1, 174.0, 200.0, 256.0, 285.0,
                  396.0, 432.0, 512.0, 525.0, 528.0, 587.0, 639.0,
                  640.0, 644.0, 741.0, 852.0, 925.0, 963.0, 963.026,
                  1336.0, 1337.0]
NOISE_LAYERS = ("pink_noise", "brown_noise", "white_noise", "surf_noise")


class NewSessionPage(QWidget):
    """Builds a session dict from form state; renders + exports."""

    def __init__(self, context, status_cb, timeline_provider=None,
                 parent=None):
        super().__init__(parent)
        self.context = context
        self._status_cb = status_cb
        self._timeline_provider = timeline_provider
        self._session: dict | None = None
        self._last_exports: dict = {}
        # v8.5.2 session identity: a stable id (not re-minted per
        # preview), the file it was loaded from / saved to, and a
        # dirty flag for unsaved edits.
        self._session_id: str | None = None
        self._title_override: str | None = None
        self._session_path = None
        self._dirty = False
        self._loading = False
        # v8.5.3: snapshot undo/redo + crash-recovery autosave
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._restoring = False
        self.autosave_cb = None   # panel injects; called when dirty
        from PySide6.QtCore import QTimer
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)
        self._autosave_timer.timeout.connect(self._autosave_tick)
        self._autosave_timer.start()
        from rgcs_desktop.viewers.sonic_playback import PreviewPlayer
        self._player = PreviewPlayer(status_cb)

        layout = QHBoxLayout(self)
        left = QVBoxLayout()

        box = QGroupBox("Session")
        form = QFormLayout(box)
        self.session_type = QComboBox()
        self.session_type.addItems(SESSION_TYPES)
        form.addRow("Type", self.session_type)
        self.carrier = QComboBox()
        for hz in CARRIER_FAMILY:
            self.carrier.addItem(f"{hz:g} Hz", hz)
        self.carrier.setCurrentText("925 Hz")
        form.addRow("Carrier / key", self.carrier)
        self.beat = QComboBox()
        for rec in load_beat_targets():
            self.beat.addItem(
                f"{rec['hz']:g} Hz — {rec['label']} [{rec['status']}]",
                float(rec["hz"]))
        idx = self.beat.findData(7.83)
        if idx >= 0:
            self.beat.setCurrentIndex(idx)
        form.addRow("Beat / modulation target", self.beat)
        self.duty = QDoubleSpinBox()
        self.duty.setRange(0.05, 1.0)
        self.duty.setSingleStep(0.05)
        self.duty.setValue(0.5)
        form.addRow("Duty (isochronic)", self.duty)
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 240)
        self.minutes.setValue(20)
        form.addRow("Duration (min)", self.minutes)
        self.extra_carriers = QLineEdit()
        self.extra_carriers.setPlaceholderText(
            "extra carriers Hz, comma separated (multi-carrier)")
        form.addRow("Extra carriers", self.extra_carriers)
        from rgcs_desktop.services.sonic_recipes import load_wobbles
        self.wobble = QComboBox()
        self.wobble.addItem("None (no wobble)", None)
        for w in load_wobbles():
            self.wobble.addItem(
                f"{w['name']} ({w['stages']} stages)", w["name"])
        form.addRow("Wobble", self.wobble)
        self.wobble_dwell = QDoubleSpinBox()
        self.wobble_dwell.setRange(0.05, 60.0)
        self.wobble_dwell.setValue(1.0)
        self.wobble_dwell.setSingleStep(0.1)
        form.addRow("Wobble dwell (s/stage)", self.wobble_dwell)
        self.wobble_target = QComboBox()
        self.wobble_target.addItems(["carrier", "beat"])
        form.addRow("Wobble target", self.wobble_target)
        left.addWidget(box)

        extras_box = QGroupBox("Voice cue and loudness (v1.1)")
        eform = QFormLayout(extras_box)
        cue_row = QHBoxLayout()
        self.voice_file = QLineEdit()
        self.voice_file.setPlaceholderText("optional voice-cue WAV")
        cue_row.addWidget(self.voice_file, stretch=1)
        browse = QPushButton("…")
        browse.setFixedWidth(28)
        browse.clicked.connect(self._pick_voice_file)
        cue_row.addWidget(browse)
        cue_widget = QWidget()
        cue_widget.setLayout(cue_row)
        eform.addRow("Voice cue", cue_widget)
        self.voice_start = QDoubleSpinBox()
        self.voice_start.setRange(0.0, 14400.0)
        self.voice_start.setValue(30.0)
        eform.addRow("Cue start (s)", self.voice_start)
        self.loudness_on = QCheckBox("Normalize loudness to target RMS")
        eform.addRow(self.loudness_on)
        self.loudness_db = QDoubleSpinBox()
        self.loudness_db.setRange(-60.0, -1.0)
        self.loudness_db.setValue(-20.0)
        eform.addRow("Target RMS (dBFS)", self.loudness_db)
        left.addWidget(extras_box)

        noise_box = QGroupBox("Noise / ambient layers")
        nv = QVBoxLayout(noise_box)
        self.noise_list = QListWidget()
        for kind in NOISE_LAYERS:
            item = QListWidgetItem(kind)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.noise_list.addItem(item)
        self.noise_list.item(0).setCheckState(
            Qt.CheckState.Checked)   # pink on by default
        nv.addWidget(self.noise_list)
        left.addWidget(noise_box)

        self.preview_btn = QPushButton("Preview recipe")
        self.preview_btn.clicked.connect(self.preview)
        left.addWidget(self.preview_btn)
        self.render_btn = QPushButton("Render WAV + export "
                                      "(JSON / PDF / bundle)")
        self.render_btn.clicked.connect(self.render_and_export)
        left.addWidget(self.render_btn)

        export_box = QGroupBox("Export selected types only")
        ev = QVBoxLayout(export_box)
        self.export_kinds = QListWidget()
        for kind, label in (
                ("recipe_json", "Recipe JSON (hashed)"),
                ("session_json", "Session JSON"),
                ("wav_preview", "WAV preview (12 s)"),
                ("wav_full", "WAV full"),
                ("session_pdf", "Session sheet PDF"),
                ("youtube_txt", "YouTube draft TXT"),
                ("bundle_zip", "Bundle ZIP (full set)")):
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, kind)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.export_kinds.addItem(item)
        self.export_kinds.item(3).setCheckState(Qt.CheckState.Checked)
        self.export_kinds.itemChanged.connect(self._update_expected)
        ev.addWidget(self.export_kinds)
        self.expected_label = QLabel("—")
        self.expected_label.setWordWrap(True)
        ev.addWidget(self.expected_label)
        self.export_selected_btn = QPushButton("Export selected types")
        self.export_selected_btn.clicked.connect(self.export_selected)
        ev.addWidget(self.export_selected_btn)
        left.addWidget(export_box)
        play_row = QHBoxLayout()
        self.play_btn = QPushButton("Play 12 s preview")
        self.play_btn.clicked.connect(self.play_preview)
        play_row.addWidget(self.play_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._player.stop)
        play_row.addWidget(self.stop_btn)
        self.spectro_btn = QPushButton("Spectrogram")
        self.spectro_btn.clicked.connect(self.show_spectrogram)
        play_row.addWidget(self.spectro_btn)
        left.addLayout(play_row)
        left.addStretch(1)
        layout.addLayout(left)

        right = QVBoxLayout()
        self.pair_label = QLabel("—")
        self.pair_label.setWordWrap(True)
        right.addWidget(self.pair_label)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(self.detail, stretch=2)
        import pyqtgraph as pg
        self.spectro_view = pg.PlotWidget(title="spectrogram preview")
        self.spectro_view.setLabel("left", "frequency", units="Hz")
        self.spectro_view.setLabel("bottom", "time", units="s")
        self.spectro_view.setVisible(False)
        right.addWidget(self.spectro_view, stretch=1)
        note = QLabel(USER_NOTE + " Use stereo headphones for binaural "
                                  "sessions.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #555; font-style: italic;")
        right.addWidget(note)
        layout.addLayout(right, stretch=1)

        for w in (self.session_type, self.carrier, self.beat):
            w.currentIndexChanged.connect(self.preview)
        self.minutes.valueChanged.connect(self.preview)
        self.preview()

        # dirty tracking: any editing widget change marks the session
        # dirty (title/metadata edits arrive through these too)
        for combo in (self.session_type, self.carrier, self.beat,
                      self.wobble, self.wobble_target):
            combo.currentIndexChanged.connect(self._mark_dirty)
        for spin in (self.duty, self.minutes, self.wobble_dwell,
                     self.voice_start, self.loudness_db):
            spin.valueChanged.connect(self._mark_dirty)
        for edit in (self.extra_carriers, self.voice_file):
            edit.textChanged.connect(self._mark_dirty)
        self.loudness_on.toggled.connect(self._mark_dirty)
        self.noise_list.itemChanged.connect(self._mark_dirty)
        self._reset_history()   # baseline for undo

    # ------------------------------------------------------------------
    def _pick_voice_file(self, *_a) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Voice cue WAV", "", "WAV files (*.wav)")
        if path:
            self.voice_file.setText(path)
            self.preview()

    def _extra_carriers(self) -> list[float]:
        out = []
        for token in self.extra_carriers.text().split(","):
            token = token.strip()
            if not token:
                continue
            try:
                value = float(token)
            except ValueError:
                continue
            if value > 0:
                out.append(value)
        return out

    def build_session(self) -> dict:
        kind = self.session_type.currentText()
        carrier = float(self.carrier.currentData())
        beat = float(self.beat.currentData())
        duration = self.minutes.value() * 60.0
        layers = []
        if kind in ("binaural", "monaural", "isochronic", "composite"):
            layer = {"layer_id": "L1",
                     "type": "binaural" if kind == "composite" else kind,
                     "carrier_hz": carrier, "gain_db": -6.0,
                     "fade_in_s": 2.0, "fade_out_s": 3.0}
            if layer["type"] in ("binaural", "monaural"):
                layer["beat_hz"] = beat
            if layer["type"] == "isochronic":
                layer["duty"] = self.duty.value()
            if self.wobble.currentData():
                layer["wobble"] = {
                    "name": self.wobble.currentData(),
                    "dwell_s": self.wobble_dwell.value(),
                    "target": self.wobble_target.currentText(),
                }
            layers.append(layer)
            for i, extra in enumerate(self._extra_carriers()):
                layers.append({"layer_id": f"C{i + 2}",
                               "type": "binaural", "carrier_hz": extra,
                               "beat_hz": beat, "gain_db": -9.0,
                               "fade_in_s": 2.0, "fade_out_s": 3.0})
        for i in range(self.noise_list.count()):
            item = self.noise_list.item(i)
            if (item.checkState() == Qt.CheckState.Checked
                    or (kind == "noise_bed" and i == 0)):
                layers.append({"layer_id": f"N{i + 1}",
                               "type": item.text(),
                               "gain_db": -18.0, "seed": i,
                               "fade_in_s": 2.0, "fade_out_s": 3.0})
        if self.voice_file.text().strip():
            layers.append({"layer_id": "V1", "type": "voice_cue",
                           "file": self.voice_file.text().strip(),
                           "start_s": self.voice_start.value(),
                           "gain_db": -3.0})
        custom = (self._timeline_provider()
                  if self._timeline_provider else None)
        if custom:
            segments = custom
            duration = sum(s["duration_s"] for s in custom)
        else:
            segments = standard_session_shape(beat, duration)
        if self._session_id is None:
            self._session_id = new_object_id("SES")
        session = {
            "schema_version": "1.0.0",
            "session_id": self._session_id,
            "title": (self._title_override
                      or f"{carrier:g} Hz + {beat:g} Hz {kind} session"),
            "intent": "user session",
            "family": kind,
            "duration_s": duration,
            "sample_rate": 48000,
            "segments": segments,
            "layers": layers,
            "notes": USER_NOTE,
            "source_ids": ["RGCS"],
        }
        if self.loudness_on.isChecked():
            session["loudness"] = {
                "target_rms_db": self.loudness_db.value()}
        return session

    def preview(self, *_a) -> dict | None:
        try:
            session = self.build_session()
        except TimelineError as exc:
            self._session = None
            self.pair_label.setText(f"Refused: {exc}")
            self.detail.setPlainText("")
            return None
        self._session = session
        carrier = float(self.carrier.currentData())
        beat = float(self.beat.currentData())
        left, right = binaural_pair(carrier, beat)
        self.pair_label.setText(
            f"left {left:g} Hz / right {right:g} Hz -> beat {beat:g} Hz "
            f"· {len(session['layers'])} layer(s) · "
            f"{session['duration_s'] / 60:g} min")
        self.detail.setPlainText(
            json_dumps(session, indent=2, sort_keys=True))
        return session

    def current_session(self) -> dict | None:
        return self._session or self.preview()

    # ------------------------------------- v8.5.2 session identity/CRUD
    def _mark_dirty(self, *_a) -> None:
        if self._loading or self._restoring:
            return
        self._dirty = True
        self._session = None    # cached preview is stale after any edit
        self._push_snapshot()

    # ------------------------------------------------ undo/redo (v8.5.3)
    def _snapshot(self) -> dict | None:
        try:
            return self.build_session()
        except TimelineError:
            return None

    def _push_snapshot(self) -> None:
        snap = self._snapshot()
        if snap is None:
            return
        if self._undo_stack and self._undo_stack[-1] == snap:
            return
        self._undo_stack.append(snap)
        del self._undo_stack[:-50]      # bound the stack
        self._redo_stack.clear()

    def _reset_history(self) -> None:
        """New baseline (open/new/close): current state is undo floor."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        snap = self._snapshot()
        if snap is not None:
            self._undo_stack.append(snap)

    def _restore(self, snap: dict) -> None:
        self._restoring = True
        try:
            path = self._session_path
            self.apply_session(snap, path)
            self._dirty = True
        finally:
            self._restoring = False

    def undo(self, *_a) -> bool:
        # the top of the stack is the current state; restore the one
        # beneath it
        current = self._snapshot()
        while self._undo_stack and self._undo_stack[-1] == current:
            self._redo_stack.append(self._undo_stack.pop())
        if not self._undo_stack:
            return False
        if current is not None and (not self._redo_stack
                                    or self._redo_stack[-1] != current):
            self._redo_stack.append(current)
        self._restore(self._undo_stack[-1])
        return True

    def redo(self, *_a) -> bool:
        if not self._redo_stack:
            return False
        snap = self._redo_stack.pop()
        self._undo_stack.append(snap)
        self._restore(snap)
        return True

    # ------------------------------------------------ autosave (v8.5.3)
    def _autosave_tick(self) -> None:
        if self._dirty and self.autosave_cb is not None:
            try:
                self.autosave_cb()
            except Exception:  # noqa: BLE001 — autosave must never crash
                pass

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def session_path(self):
        return self._session_path

    def mark_saved(self, path) -> None:
        self._session_path = path
        self._dirty = False

    def reset_identity(self) -> None:
        """New/Close Session: fresh id, no file, unsaved by definition."""
        self._session_id = None
        self._title_override = None
        self._session_path = None
        self._session = None
        self._dirty = True     # a brand-new session is unsaved
        self.preview()
        self._reset_history()

    def set_title(self, title: str) -> None:
        self._title_override = title
        self._session = None
        self._mark_dirty()

    def apply_session(self, session: dict, path=None) -> None:
        """Inverse of build_session: load a session dict into the form.

        Values outside the stock combo lists are added as items so any
        library/imported session opens editable.
        """
        self._loading = True
        try:
            family = session.get("family", "binaural")
            if family in SESSION_TYPES:
                self.session_type.setCurrentText(family)
            binaurals = [la for la in session.get("layers", [])
                         if la.get("type") in ("binaural", "monaural",
                                               "isochronic")]
            if binaurals:
                first = binaurals[0]
                carrier = float(first.get("carrier_hz", 200.0))
                idx = self.carrier.findData(carrier)
                if idx < 0:
                    self.carrier.addItem(f"{carrier:g} Hz", carrier)
                    idx = self.carrier.count() - 1
                self.carrier.setCurrentIndex(idx)
                beat = float(first.get("beat_hz", 0.0) or 0.0)
                bidx = self.beat.findData(beat)
                if bidx < 0:
                    self.beat.addItem(f"{beat:g} Hz — from session "
                                      f"[imported]", beat)
                    bidx = self.beat.count() - 1
                self.beat.setCurrentIndex(bidx)
                if first.get("type") == "isochronic":
                    self.duty.setValue(float(first.get("duty", 0.5)))
                wobble = first.get("wobble") or {}
                widx = self.wobble.findData(wobble.get("name"))
                self.wobble.setCurrentIndex(max(widx, 0))
                if wobble:
                    self.wobble_dwell.setValue(
                        float(wobble.get("dwell_s", 1.0)))
                    self.wobble_target.setCurrentText(
                        wobble.get("target", "carrier"))
                extras = [f"{la['carrier_hz']:g}"
                          for la in binaurals[1:]
                          if la.get("carrier_hz")]
                self.extra_carriers.setText(", ".join(extras))
            minutes = max(1, round(float(session.get("duration_s", 60))
                                   / 60.0))
            self.minutes.setValue(minutes)
            noise_types = {la.get("type")
                           for la in session.get("layers", [])}
            for i in range(self.noise_list.count()):
                item = self.noise_list.item(i)
                item.setCheckState(
                    Qt.CheckState.Checked if item.text() in noise_types
                    else Qt.CheckState.Unchecked)
            voice = next((la for la in session.get("layers", [])
                          if la.get("type") == "voice_cue"), None)
            self.voice_file.setText((voice or {}).get("file", ""))
            if voice and voice.get("start_s") is not None:
                self.voice_start.setValue(float(voice["start_s"]))
            loudness = session.get("loudness") or {}
            self.loudness_on.setChecked(bool(loudness))
            if loudness.get("target_rms_db") is not None:
                self.loudness_db.setValue(
                    float(loudness["target_rms_db"]))
            self._session_id = session.get("session_id")
            self._title_override = session.get("title")
            self._session_path = path
            self._session = None
            self.preview()
            self._dirty = False
            if not self._restoring:
                self._reset_history()
        finally:
            self._loading = False

    def render_and_export(self, *_a, duration_s: float | None = None):
        session = self.current_session()
        if session is None:
            return None
        from rgcs_desktop.viewers.design_studio_common import (
            export_dir, record_export_safe)
        out = export_dir(self.context) / "sonic"
        sid = session["session_id"]
        try:
            wav = out / f"{sid}.wav"
            receipt = render_session_wav(session, wav,
                                         duration_s=duration_s)
            session["exports"] = {"wav": wav.name}
            recipe_json = export_recipe_json(session,
                                             out / f"{sid}.recipe.json")
            pdf = export_session_pdf(session, receipt,
                                     out / f"{sid}_session_sheet.pdf")
            meta = export_youtube_metadata_sheet(
                session, out / f"{sid}_youtube.txt")
            bundle = export_bundle(session, [wav, recipe_json, pdf, meta],
                                   out / f"{sid}_bundle.zip")
            check = verify_bundle(bundle)
        except (TimelineError, Exception) as exc:  # surface, don't crash
            self._status_cb(f"render failed: {exc}")
            raise
        for kind, path in (("sonic_wav", wav), ("sonic_json", recipe_json),
                           ("sonic_pdf", pdf), ("sonic_bundle", bundle)):
            record_export_safe(self.context, kind, path)
        self._last_exports = {"wav": wav, "json": recipe_json,
                              "pdf": pdf, "youtube": meta,
                              "bundle": bundle}
        self._status_cb(
            f"rendered {sid}: peak {receipt['peak']:.3f}, bundle "
            f"{'OK' if check['ok'] else 'MISMATCH'} -> {out}")
        return self._last_exports

    @property
    def last_exports(self) -> dict:
        return self._last_exports

    # ------------------------------------ v8.5.2: export-type selection
    def checked_export_kinds(self) -> list[str]:
        kinds = []
        for i in range(self.export_kinds.count()):
            item = self.export_kinds.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                kinds.append(item.data(Qt.ItemDataRole.UserRole))
        return kinds

    def _update_expected(self, *_a) -> None:
        from rgcs_desktop.services.sonic_export_selection import (
            ExportSelectionError, expected_export_files)
        session = self.current_session()
        kinds = self.checked_export_kinds()
        if session is None or not kinds:
            self.expected_label.setText("no export types selected")
            return
        try:
            names = expected_export_files(session, kinds)
        except ExportSelectionError as exc:
            self.expected_label.setText(str(exc))
            return
        self.expected_label.setText("will write: " + ", ".join(names))

    def export_selected(self, *_a) -> dict | None:
        """Write only the checked export types (never the full bundle
        unless the bundle itself is checked)."""
        from rgcs_desktop.services.sonic_export_selection import (
            ExportSelectionError, export_selected)
        session = self.current_session()
        if session is None:
            self._status_cb("nothing to export — preview a recipe first")
            return None
        kinds = self.checked_export_kinds()
        from rgcs_desktop.viewers.design_studio_common import (
            export_dir, record_export_safe)
        out = export_dir(self.context) / "sonic"
        try:
            written = export_selected(session, kinds, out)
        except ExportSelectionError as exc:
            self._status_cb(f"export refused: {exc}")
            return None
        except Exception as exc:  # surface, don't crash
            self._status_cb(f"export failed: {exc}")
            raise
        for kind, path in written.items():
            if kind != "receipt":
                record_export_safe(self.context, f"sonic_{kind}", path)
        files = [p.name for k, p in written.items() if k != "receipt"]
        self._status_cb(f"exported {len(files)} file(s): "
                        + ", ".join(sorted(files)))
        return written

    # -------------------------------------------- v1.1: play + spectro
    def _render_preview_wav(self, duration_s: float = 12.0):
        """Short preview render into the workspace exports dir."""
        session = self.current_session()
        if session is None:
            return None, None
        from rgcs_desktop.viewers.design_studio_common import export_dir
        out = (export_dir(self.context) / "sonic"
               / f"{session['session_id']}_preview.wav")
        receipt = render_session_wav(session, out,
                                     duration_s=duration_s)
        return out, receipt

    def play_preview(self, *_a) -> bool:
        from rgcs_desktop.viewers.sonic_playback import \
            playback_available
        ok, reason = playback_available()
        if not ok:
            self._status_cb(f"playback unavailable — {reason}; render "
                            f"and open the WAV in your player instead")
            return False
        wav, _receipt = self._render_preview_wav()
        if wav is None:
            return False
        return self._player.play(wav)

    def teardown(self) -> None:
        """Stop preview playback (workspace close/switch, app exit).
        Unsaved edits get one final autosave so nothing disappears
        silently."""
        self._player.stop()
        self._autosave_tick()

    def show_spectrogram(self, *_a) -> bool:
        from rgcs_desktop.services.sonic_audio import load_wav, \
            spectrogram
        wav, _receipt = self._render_preview_wav()
        if wav is None:
            return False
        audio, rate = load_wav(wav)
        spec = spectrogram(audio, rate)
        import numpy as np
        import pyqtgraph as pg
        self.spectro_view.clear()
        image = pg.ImageItem(spec["db"])
        # map image pixels -> (time s, frequency Hz), display <= 2 kHz
        t_max = float(spec["times_s"][-1]) if len(spec["times_s"]) else 1.0
        f_max = float(spec["freqs_hz"][-1])
        image.setRect(0.0, 0.0, t_max, f_max)
        self.spectro_view.addItem(image)
        self.spectro_view.setYRange(0, 2000)
        self.spectro_view.setXRange(0, t_max)
        self.spectro_view.setVisible(True)
        lo = float(np.percentile(spec["db"], 60))
        hi = float(spec["db"].max())
        image.setLevels((lo, hi))
        self._status_cb("spectrogram rendered (preview segment, "
                        "0–2 kHz view)")
        return True
