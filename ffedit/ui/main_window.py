"""
Main window for ffedit video editor.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QWidget, QFileDialog, QInputDialog, QApplication
from ffedit.ui.layouts import MainWindowLayout
from ffedit.ui.feature_cut import CutFeature
from ffedit.ui.feature_merge import MergeFeature
from ffedit.ui.feature_blur import BlurFeature
from ffedit.ui.feature_black import BlackScreenFeature
from ffedit.ui.feature_audio import AudioFeature

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ffedit - Minimal Video Editor")
        self.setGeometry(100, 100, 900, 600)
        self.layout = MainWindowLayout(self)
        central = QWidget()
        central.setLayout(self.layout.top_layout)
        self.setCentralWidget(central)

        self.input_file = None
        self.executor = None

        # Feature delegates
        self.cut_feature = CutFeature(self)
        self.merge_feature = MergeFeature(self)
        self.blur_feature = BlurFeature(self)
        self.black_feature = BlackScreenFeature(self)
        self.audio_feature = AudioFeature(self)

        self._setup_shortcuts()
        self.layout.log_panel.append(
            "Hint: Drag a video into the dark preview area or click Pick Video File."
        )

        # Initialize ffmpeg status indicator
        self.set_ffmpeg_status(None)

        # Connect buttons
        self.layout.pick_file_btn.clicked.connect(self.pick_file)
        self.layout.add_video_btn.clicked.connect(self._reset_video_state)
        self.layout.cut_btn.clicked.connect(self.cut_feature.cut_video)
        self.layout.mark_btn.clicked.connect(self.cut_feature.add_multi_cut_segment)
        self.layout.merge_btn.clicked.connect(self.merge_feature.merge_videos)
        self.layout.blur_btn.clicked.connect(self.blur_feature.blur_video)
        self.layout.black_btn.clicked.connect(self.black_feature.insert_black_screen)
        self.layout.audio_btn.clicked.connect(self.audio_feature.audio_controls)
        self.layout.seek_slider.marker_removed.connect(self.cut_feature.remove_segment_marker)
        # Removed preview_btn wiring



    # Audio feature logic moved to feature_audio.py

    def _on_audio_finished(self, code, msg):
        if code == 0:
            self.layout.log_panel.append("Audio operation finished successfully.")
            self.layout.progress.setValue(100)
        else:
            self.layout.log_panel.append(f"Audio operation failed: {msg}")
    # Black screen feature logic moved to feature_black.py

    def _on_black_finished(self, code, msg):
        if code == 0:
            self.layout.log_panel.append("Black screen video created successfully.")
            self.layout.progress.setValue(100)
        else:
            self.layout.log_panel.append(f"Black screen failed: {msg}")

    # Blur feature logic moved to feature_blur.py

    def _on_blur_finished(self, code, msg):
        if code == 0:
            self.layout.log_panel.append("Blur finished successfully.")
            self.layout.progress.setValue(100)
        else:
            self.layout.log_panel.append(f"Blur failed: {msg}")
    # Merge feature logic moved to feature_merge.py

    def _on_merge_finished(self, code, msg, filelist_path):
        import os
        try:
            os.remove(filelist_path)
        except Exception:
            pass
        if code == 0:
            self.layout.log_panel.append("Merge finished successfully.")
            self.layout.progress.setValue(100)
        else:
            self.layout.log_panel.append(f"Merge failed: {msg}")

    def pick_file(self):
        dialog = QFileDialog(self, "Select Video File", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        if dialog.exec():
            files = dialog.selectedFiles()
            if files:
                file = files[0]
                self.layout.file_label.setText(file)
                self.layout.log_panel.append(f"Selected file: {file}")
                self.input_file = file
                self.layout.player_widget.play(file)

    def _reset_video_state(self) -> None:
        had_file = bool(self.input_file)
        self.layout.player_widget.reset_to_initial_state()
        self.input_file = None
        self.layout.file_label.setText("No file selected")
        self.layout.seek_slider.setValue(0)
        self.layout.set_cut_markers([], [])
        self.cut_feature.reset_for_new_video()
        message = "Video cleared. Ready to add a new file." if had_file else "Ready to add a video."
        self.layout.log_panel.append(message)

    # Cut feature logic moved to feature_cut.py

    def _on_cut_finished(self, code, msg):
        if code == 0:
            self.layout.log_panel.append("Cut finished successfully.")
            self.layout.progress.setValue(100)
        else:
            self.layout.log_panel.append(f"Cut failed: {msg}")

    def _setup_shortcuts(self) -> None:
        """Bind navigation and editing shortcuts to player and cut actions."""
        self._forward_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        self._forward_shortcut.activated.connect(self._seek_forward)
        self._backward_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self._backward_shortcut.activated.connect(self._seek_backward)
        self._space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self._space_shortcut.activated.connect(self.layout.toggle_play_pause)
        self._single_cut_shortcut = QShortcut(QKeySequence(Qt.Key_C), self)
        self._single_cut_shortcut.activated.connect(self.cut_feature.start_single_cut_shortcut)
        self._multi_cut_shortcut = QShortcut(QKeySequence(Qt.Key_M), self)
        self._multi_cut_shortcut.activated.connect(self.cut_feature.start_multiple_cut_shortcut)
        self._apply_cut_shortcut = QShortcut(QKeySequence(Qt.Key_B), self)
        self._apply_cut_shortcut.activated.connect(
            self.cut_feature.apply_current_time_cut_shortcut
        )

    def set_ffmpeg_status(self, path: str | None) -> None:
        """Update the ffmpeg availability status in the UI.

        If `path` is truthy, show it as available; otherwise indicate missing.
        """
        label = getattr(self.layout, "ffmpeg_status", None)
        icon_label = getattr(self.layout, "ffmpeg_icon", None)
        if label is None:
            return
        if path:
            label.setText(f"ffmpeg: available")
            label.setStyleSheet("color: #22c55e;")
            label.setToolTip(f"ffmpeg available at: {path}")
            self.layout.log_panel.append(f"ffmpeg available at: {path}")
            if icon_label is not None:
                from PySide6.QtGui import QIcon
                icon = QIcon.fromTheme("emblem-default")
                if icon.isNull():
                    icon = self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton)
                icon_label.setPixmap(icon.pixmap(16, 16))
        else:
            label.setText("ffmpeg: not found")
            label.setStyleSheet("color: #ef4444;")
            label.setToolTip("ffmpeg not found; download/install to enable all features")
            self.layout.log_panel.append("ffmpeg not found; some features may be limited.")
            if icon_label is not None:
                from PySide6.QtGui import QIcon
                icon = QIcon.fromTheme("dialog-error")
                if icon.isNull():
                    icon = self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxCritical)
                icon_label.setPixmap(icon.pixmap(16, 16))

    def _seek_forward(self) -> None:
        step = self.layout.seek_step_ms()
        self.layout.player_widget.seek_by(step)

    def _seek_backward(self) -> None:
        step = self.layout.seek_step_ms()
        self.layout.player_widget.seek_by(-step)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "layout"):
            self.layout.update_responsive_controls(self.width())
