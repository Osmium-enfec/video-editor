from PySide6.QtWidgets import QFileDialog, QInputDialog
import os
from ffedit.ffmpeg.cut import build_cut_command
from ffedit.core.executor import FFmpegExecutor

class CutFeature:
    def __init__(self, main_window):
        self.main_window = main_window

    def cut_video(self):
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append("No input file selected.")
            return
        start, ok1 = QInputDialog.getText(self.main_window, "Start Time", "Enter start time (e.g. 00:01:00):")
        if not ok1 or not start:
            return
        end, ok2 = QInputDialog.getText(self.main_window, "End Time", "Enter end time (e.g. 00:02:00):")
        if not ok2 or not end:
            return
        out_file, _ = QFileDialog.getSaveFileName(self.main_window, "Save Cut Video As", os.path.expanduser("~"), "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if not out_file:
            return
        cmd = build_cut_command(self.main_window.input_file, start, end, out_file)
        executor = FFmpegExecutor(cmd)
        executor.progress.connect(self.main_window.layout.progress.setValue)
        executor.log.connect(self.main_window.layout.log_panel.append)
        executor.finished.connect(self.main_window._on_cut_finished)
        self.main_window.executor = executor
        self.main_window.layout.progress.setValue(0)
        self.main_window.layout.log_panel.append(f"Starting cut: {start} to {end} -> {out_file}")
        executor.start()
