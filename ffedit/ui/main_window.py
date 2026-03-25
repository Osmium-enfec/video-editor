"""
Main window for ffedit video editor.
"""
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

        # Connect buttons
        self.layout.pick_file_btn.clicked.connect(self.pick_file)
        self.layout.cut_btn.clicked.connect(self.cut_feature.cut_video)
        self.layout.merge_btn.clicked.connect(self.merge_feature.merge_videos)
        self.layout.blur_btn.clicked.connect(self.blur_feature.blur_video)
        self.layout.black_btn.clicked.connect(self.black_feature.insert_black_screen)
        self.layout.audio_btn.clicked.connect(self.audio_feature.audio_controls)
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

    # Cut feature logic moved to feature_cut.py

    def _on_cut_finished(self, code, msg):
        if code == 0:
            self.layout.log_panel.append("Cut finished successfully.")
            self.layout.progress.setValue(100)
        else:
            self.layout.log_panel.append(f"Cut failed: {msg}")
