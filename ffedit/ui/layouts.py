from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ffedit.preview.player import PlayerWidget


class MainWindowLayout:
    def __init__(self, main_window):
        self.main_window = main_window
        self.player_widget = PlayerWidget(main_window)
        self.player_widget.set_main_window(main_window)
        self.file_label = QLabel("No file selected")
        self.pick_file_btn = QPushButton("Pick Video File")
        self.cut_btn = QPushButton("Cut Video")
        self.merge_btn = QPushButton("Merge Videos")
        self.blur_btn = QPushButton("Blur Video")
        self.black_btn = QPushButton("Insert Black Screen")
        self.black_mute_checkbox = QCheckBox("Mute audio during black")
        self.audio_btn = QPushButton("Audio Controls")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)

        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setRowStretch(0, 3)
        self.grid.setRowStretch(1, 3)
        self.grid.setRowStretch(2, 1)
        self.grid.setColumnStretch(0, 3)
        self.grid.setColumnStretch(1, 3)
        self.grid.setColumnStretch(2, 1)

        self.grid.addWidget(self.player_widget, 0, 0, 2, 2)

        self._build_options_column()
        self._build_controls_row()
        self.grid.addWidget(self.log_panel, 2, 2, 1, 1)

        self.top_layout = self.grid

    def _build_options_column(self):
        options_container = QWidget()
        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignTop)
        options_layout.addWidget(self.file_label)
        options_layout.addWidget(self.pick_file_btn)
        options_layout.addWidget(self.cut_btn)
        options_layout.addWidget(self.merge_btn)
        options_layout.addWidget(self.blur_btn)
        options_layout.addWidget(self.black_btn)
        options_layout.addWidget(self.black_mute_checkbox)
        options_layout.addWidget(self.audio_btn)
        options_layout.addStretch(1)
        options_layout.addWidget(self.progress)
        options_container.setLayout(options_layout)
        self.grid.addWidget(options_container, 0, 2, 2, 1)

    def _build_controls_row(self):
        from PySide6.QtGui import QIcon
        self.play_btn = QPushButton()
        self.pause_btn = QPushButton()
        self.stop_btn = QPushButton()
        self.play_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        self.pause_btn.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.select_btn = QPushButton("Select Region")
        self.select_btn.setEnabled(False)
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)


        # Speed control dropdown
        from PySide6.QtWidgets import QComboBox
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "1.5x", "2x"])
        self.speed_combo.setCurrentIndex(1)  # Default to 1x

        # Timer label (to be placed above progress bar)
        self.timer_label = QLabel("00:00:00 / 00:00:00")

        # --- Timer label above seek bar ---
        # Create a vertical layout for timer label and seek bar
        from PySide6.QtWidgets import QVBoxLayout
        self.timer_and_progress = QVBoxLayout()
        self.timer_and_progress.setSpacing(2)
        self.timer_and_progress.addWidget(self.timer_label)
        self.timer_and_progress.addWidget(self.seek_slider)

        controls_container = QWidget()
        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.play_btn)
        self.controls_layout.addWidget(self.pause_btn)
        self.controls_layout.addWidget(self.stop_btn)
        self.controls_layout.addWidget(self.select_btn)
        self.controls_layout.addLayout(self.timer_and_progress, stretch=1)
        self.controls_layout.addWidget(self.speed_combo)
        self.controls_layout.addWidget(QLabel("Volume"))
        self.controls_layout.addWidget(self.volume_slider)
        controls_container.setLayout(self.controls_layout)
        self.grid.addWidget(controls_container, 2, 0, 1, 2)

        self.play_btn.clicked.connect(self.player_widget.resume)
        self.pause_btn.clicked.connect(self.player_widget.pause)
        self.stop_btn.clicked.connect(self.player_widget.stop)
        self.select_btn.clicked.connect(self.player_widget.confirm_region_selection)
        self.seek_slider.sliderMoved.connect(self._seek_video)
        self.player_widget.media_player.positionChanged.connect(self._sync_seek_slider)
        self.player_widget.media_player.durationChanged.connect(self._sync_seek_slider)
        self.volume_slider.valueChanged.connect(
            lambda value: self.player_widget.set_volume(value / 100.0)
        )
        # Speed control connection (dropdown)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)

    def _on_speed_changed(self, idx):
        rates = [0.5, 1.0, 1.5, 2.0]
        self.player_widget.set_speed(rates[idx])

        # Timer update connection
        self.player_widget.media_player.positionChanged.connect(self._update_timer_label)
        self.player_widget.media_player.durationChanged.connect(self._update_timer_label)

        # (No-op: timer_and_progress is now added directly in controls row)

    def _update_timer_label(self, _value=None):
        duration = self.player_widget.media_player.duration() // 1000
        position = self.player_widget.media_player.position() // 1000
        def fmt(secs):
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h:02}:{m:02}:{s:02}"
        self.timer_label.setText(f"{fmt(position)} / {fmt(duration)}")

    def _seek_video(self, slider_value: int):
        max_value = self.seek_slider.maximum() or 1
        ratio = slider_value / max_value
        self.player_widget.seek_to_ratio(ratio)

    def _sync_seek_slider(self, _value):
        duration = self.player_widget.media_player.duration()
        position = self.player_widget.media_player.position()
        self.seek_slider.blockSignals(True)
        if duration > 0:
            ratio = position / duration
            max_value = self.seek_slider.maximum() or 1
            self.seek_slider.setValue(int(ratio * max_value))
        else:
            self.seek_slider.setValue(0)
        self.seek_slider.blockSignals(False)
