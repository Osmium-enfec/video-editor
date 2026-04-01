"""
App entry point for ffedit.
Initializes the PySide6 application and main window.
"""

import sys
from PySide6.QtWidgets import QApplication, QProgressDialog
from PySide6.QtCore import Qt, QObject, Signal, QThread
from ffedit.ui.main_window import MainWindow
from ffedit.ffmpeg.installer import ensure_ffmpeg_available, get_ffmpeg_path, save_ffmpeg_path, load_ffmpeg_path
from PySide6.QtWidgets import QMessageBox


class _InstallerWorker(QObject):
    finished = Signal(str)

    def run(self):
        try:
            p = ensure_ffmpeg_available(allow_download=True)
            self.finished.emit(p or "")
        except Exception:
            self.finished.emit("")


def main():
    # Create QApplication first so we can show dialogs during startup.
    app = QApplication(sys.argv)

    # Create and show main window immediately.
    window = MainWindow()
    window.show()

    # Ensure ffmpeg is available (system, bundled, or downloaded).
    try:
        ff = get_ffmpeg_path()
        # Update UI immediately with current status
        window.set_ffmpeg_status(ff)

        if not ff:
            # Prompt the user to provide an ffmpeg path (browse or typed input)
            def prompt_for_ffmpeg_path(parent):
                from PySide6.QtWidgets import QFileDialog, QInputDialog
                while True:
                    dlg = QMessageBox(parent)
                    dlg.setIcon(QMessageBox.Question)
                    dlg.setWindowTitle("Locate ffmpeg")
                    dlg.setText("ffmpeg was not found. Choose how you'd like to provide the ffmpeg executable:")
                    browse_btn = dlg.addButton("Browse...", QMessageBox.ActionRole)
                    type_btn = dlg.addButton("Enter path...", QMessageBox.ActionRole)
                    cancel_btn = dlg.addButton(QMessageBox.Cancel)
                    dlg.exec()
                    clicked = dlg.clickedButton()
                    if clicked == browse_btn:
                        sel, _ = QFileDialog.getOpenFileName(parent, "Locate ffmpeg executable", load_ffmpeg_path() or "~", "ffmpeg (ffmpeg, ffmpeg.exe);;All Files (*)")
                        if not sel:
                            continue
                        candidate = sel
                    elif clicked == type_btn:
                        text, ok = QInputDialog.getText(parent, "Enter ffmpeg path", "Path to ffmpeg:")
                        if not ok or not text:
                            continue
                        candidate = text.strip()
                    else:
                        return None

                    # Validate candidate
                    try:
                        import subprocess
                        p = subprocess.run([candidate, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                        out = (p.stdout or "") + (p.stderr or "")
                        if "ffmpeg" in out.lower():
                            return candidate
                        else:
                            QMessageBox.warning(parent, "Invalid executable", "The selected file does not appear to be ffmpeg. Try again.")
                            continue
                    except Exception:
                        QMessageBox.warning(parent, "Validation failed", "Could not validate the selected path. Try again.")
                        continue

            candidate = prompt_for_ffmpeg_path(window)
            if candidate:
                # Persist and update UI
                save_ffmpeg_path(candidate)
                window.set_ffmpeg_status(candidate)
            else:
                # If user didn't provide a path, offer download/install
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("ffmpeg required")
                msg.setText("ffmpeg is required for some features. Download and install ffmpeg now?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                ret = msg.exec()
                if ret == QMessageBox.Yes:
                    # Run installation in background with a progress dialog
                    progress = QProgressDialog("Installing ffmpeg...", None, 0, 0, window)
                    progress.setWindowModality(Qt.ApplicationModal)
                    progress.setCancelButton(None)
                    progress.setMinimumDuration(0)
                    progress.setWindowTitle("Installing ffmpeg")
                    progress.show()

                    thread = QThread()
                    worker = _InstallerWorker()
                    worker.moveToThread(thread)

                    def _on_finished(path: str):
                        try:
                            progress.cancel()
                        except Exception:
                            pass
                        thread.quit()
                        thread.wait()
                        if path:
                            save_ffmpeg_path(path)
                        window.set_ffmpeg_status(path or None)

                    worker.finished.connect(_on_finished)
                    thread.started.connect(worker.run)
                    thread.start()
    except Exception as exc:
        print(f"ffmpeg check/install failed: {exc}")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
