
from PySide6.QtWidgets import QFileDialog, QInputDialog
import os
from ffedit.ffmpeg.blur import build_blur_command
from ffedit.core.executor import FFmpegExecutor

class BlurFeature:
    def __init__(self, main_window):
        self.main_window = main_window

    def blur_video(self):
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append("No input file selected.")
            return
        blur_types = ["Full-frame blur", "Region-based blur"]
        blur_type, ok = QInputDialog.getItem(self.main_window, "Blur Type", "Select blur type:", blur_types, 0, False)
        if not ok:
            return
        if blur_type == "Region-based blur":
            player = self.main_window.layout.player_widget
            player.pause()
            player.show_region_selector_with_default()
            self.main_window.layout.log_panel.append(
                "Region blur enabled: adjust the rectangle, then use the Select button in the bottom controls to confirm."
            )
            return

        strength, ok5 = QInputDialog.getInt(
            self.main_window,
            "Blur Strength",
            "Enter blur strength (1-50):",
            10,
            1,
            50,
        )
        if not ok5:
            return

        start_time, ok_start = QInputDialog.getText(
            self.main_window,
            "Blur Start Time",
            "Enter blur start time (in seconds or hh:mm:ss):",
            text="0",
        )
        if not ok_start:
            return
        start_time = start_time.strip() or "0"

        end_time, ok_end = QInputDialog.getText(
            self.main_window,
            "Blur End Time",
            "Enter blur end time (in seconds or hh:mm:ss):",
            text="",
        )
        if not ok_end:
            return
        end_time = end_time.strip() or None

        out_file, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Blurred Video As",
            os.path.expanduser("~"),
            "Video Files (*.mp4 *.mov *.avi *.mkv)",
        )
        if not out_file:
            return

        cmd = build_blur_command(
            self.main_window.input_file,
            out_file,
            region=None,
            strength=strength,
            start_time=start_time,
            end_time=end_time,
        )
        executor = FFmpegExecutor(cmd)
        executor.progress.connect(self.main_window.layout.progress.setValue)
        executor.log.connect(self.main_window.layout.log_panel.append)
        executor.finished.connect(self.main_window._on_blur_finished)
        self.main_window.executor = executor
        self.main_window.layout.progress.setValue(0)
        self.main_window.layout.log_panel.append(
            f"Starting blur: {blur_type} (strength={strength}, start={start_time}, end={end_time}) -> {out_file}"
        )
        executor.start()
