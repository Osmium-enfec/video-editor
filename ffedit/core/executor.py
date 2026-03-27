"""FFmpeg subprocess runner for ffedit.
Runs FFmpeg commands in a separate thread and captures progress."""

import shutil
import subprocess
from PySide6.QtCore import QThread, Signal

class FFmpegExecutor(QThread):
    progress = Signal(float)
    finished = Signal(int, str)
    log = Signal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self._process = None

    def run(self):
        binary = self.cmd[0] if self.cmd else "ffmpeg"
        if not shutil.which(binary):
            self.log.emit(f"Cannot run '{binary}': binary not found. Please install ffmpeg and ensure it is on PATH.")
            self.finished.emit(1, f"{binary} not found")
            return

        self.log.emit(f"Running: {' '.join(self.cmd)}")
        try:
            self._process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
        except FileNotFoundError as exc:
            self.log.emit(f"Failed to start process: {exc}")
            self.finished.emit(1, "Process start failed")
            return

        for line in self._process.stderr:
            self.log.emit(line.strip())
            # Progress parsing can be added here
        self._process.wait()
        self.finished.emit(self._process.returncode, "Done" if self._process.returncode == 0 else "Error")

    def terminate(self):
        if self._process:
            self._process.terminate()
