"""
FFmpeg subprocess runner for ffedit.
Runs FFmpeg commands in a separate thread and captures progress.
"""
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
        self.log.emit(f"Running: {' '.join(self.cmd)}")
        self._process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        for line in self._process.stderr:
            self.log.emit(line.strip())
            # Progress parsing can be added here
        self._process.wait()
        self.finished.emit(self._process.returncode, "Done" if self._process.returncode == 0 else "Error")

    def terminate(self):
        if self._process:
            self._process.terminate()
