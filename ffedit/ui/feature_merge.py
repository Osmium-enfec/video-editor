from PySide6.QtWidgets import QFileDialog, QInputDialog
import os
from ffedit.ffmpeg.merge import build_merge_command
from ffedit.core.executor import FFmpegExecutor
import tempfile

class MergeFeature:
    def __init__(self, main_window):
        self.main_window = main_window

    def merge_videos(self):
        files, _ = QFileDialog.getOpenFileNames(self.main_window, "Select Videos to Merge", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if not files or len(files) < 2:
            self.main_window.layout.log_panel.append("Select at least two video files to merge.")
            return
        out_file, _ = QFileDialog.getSaveFileName(self.main_window, "Save Merged Video As", os.path.expanduser("~"), "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if not out_file:
            return
        filelist_path = tempfile.mktemp(suffix="_ffedit_merge.txt")
        with open(filelist_path, "w") as f:
            for path in files:
                f.write(f"file '{path}'\n")
        cmd = build_merge_command(filelist_path, out_file)
        executor = FFmpegExecutor(cmd)
        executor.progress.connect(self.main_window.layout.progress.setValue)
        executor.log.connect(self.main_window.layout.log_panel.append)
        executor.finished.connect(lambda code, msg: self.main_window._on_merge_finished(code, msg, filelist_path))
        self.main_window.executor = executor
        self.main_window.layout.progress.setValue(0)
        self.main_window.layout.log_panel.append(f"Starting merge: {len(files)} files -> {out_file}")
        executor.start()
