import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl

class MinimalVideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Video Player Test")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        self.video_widget = QVideoWidget(self)
        layout.addWidget(self.video_widget)
        self.open_btn = QPushButton("Open Video", self)
        layout.addWidget(self.open_btn)
        self.open_btn.clicked.connect(self.open_file)
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if file:
            self.media_player.setSource(QUrl.fromLocalFile(file))
            self.media_player.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MinimalVideoPlayer()
    player.show()
    sys.exit(app.exec())
