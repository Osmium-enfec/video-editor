from PySide6.QtWidgets import QFileDialog, QInputDialog
import os
from ffedit.ffmpeg.black import build_black_command
from ffedit.core.executor import FFmpegExecutor

class BlackScreenFeature:
    def __init__(self, main_window):
        self.main_window = main_window

    def insert_black_screen(self):
        if not self.main_window.input_file:
            file, _ = QFileDialog.getOpenFileName(self.main_window, "Select Video File", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
            if not file:
                self.main_window.layout.log_panel.append("No input file selected.")
                return
            self.main_window.input_file = file
            self.main_window.layout.file_label.setText(file)
        start, ok1 = QInputDialog.getText(self.main_window, "Black Start Time", "Enter start time for black screen (e.g. 00:00:10):", text="00:00:00")
        if not ok1 or not start.strip():
            return
        end, ok2 = QInputDialog.getText(self.main_window, "Black End Time", "Enter end time for black screen (e.g. 00:00:20):")
        if not ok2 or not end.strip():
            return
        out_file, _ = QFileDialog.getSaveFileName(self.main_window, "Save Output Video As", os.path.expanduser("~"), "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if not out_file:
            return
        mute_audio = self.main_window.layout.black_mute_checkbox.isChecked()
        start = start.strip()
        end = end.strip()

        try:
            cmd = build_black_command(
                self.main_window.input_file,
                out_file,
                start_time=start,
                end_time=end,
                mute_audio=mute_audio,
            )
        except ValueError as exc:
            self.main_window.layout.log_panel.append(str(exc))
            return

        executor = FFmpegExecutor(cmd)
        executor.progress.connect(self.main_window.layout.progress.setValue)
        executor.log.connect(self.main_window.layout.log_panel.append)
        executor.finished.connect(self.main_window._on_black_finished)
        self.main_window.executor = executor
        self.main_window.layout.progress.setValue(0)
        mute_text = " (audio muted)" if mute_audio else ""
        self.main_window.layout.log_panel.append(
            f"Starting black screen insert: {start} to {end}{mute_text} -> {out_file}"
        )
        executor.start()
