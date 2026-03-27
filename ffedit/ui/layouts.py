from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QSlider

from ffedit.preview.player import PlayerWidget
from ffedit.ui.widgets import MarkerSlider


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

        self._init_button_styles()
        self._build_options_column()
        self._build_controls_row()
        self.grid.addWidget(self.log_panel, 2, 2, 1, 1)

        self.top_layout = self.grid
        self._apply_button_styles()
        self.update_responsive_controls(self.main_window.width())

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
        self.stop_btn = QPushButton()
        self.mark_btn = QPushButton("Mark Cut")
        self.mark_btn.setEnabled(False)
        self.mark_btn.setVisible(False)
        cut_icon = QIcon.fromTheme("edit-cut")
        if cut_icon.isNull():
            cut_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)
        self.mark_btn.setIcon(cut_icon)
        self.mark_btn.setIconSize(QSize(18, 18))
        self._play_icon = QIcon.fromTheme("media-playback-start")
        self._pause_icon = QIcon.fromTheme("media-playback-pause")
        self.play_btn.setIcon(self._play_icon)
        self.stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.select_btn = QPushButton("Select Region")
        self.select_btn.setEnabled(False)
        self.seek_slider = MarkerSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)


        # Speed control dropdown
        from PySide6.QtWidgets import QComboBox
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "1.5x", "2x"])
        self.speed_combo.setCurrentIndex(1)  # Default to 1x

        self.skip_combo = QComboBox()
        for label, millis in (("2s", 2_000), ("5s", 5_000), ("10s", 10_000), ("20s", 20_000), ("50s", 50_000)):
            self.skip_combo.addItem(label, millis)
        self.skip_combo.setCurrentIndex(2)

        # Timer label (to be placed above progress bar)
        self.timer_label = QLabel("00:00:00 / 00:00:00")

        # --- Timer label above seek bar ---
        # Create a vertical layout for timer label and seek bar
        from PySide6.QtWidgets import QVBoxLayout
        self.timer_and_progress = QVBoxLayout()
        self.timer_and_progress.setSpacing(6)
        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignHCenter)
        button_row.setSpacing(8)
        button_row.addWidget(self.play_btn)
        button_row.addWidget(self.stop_btn)
        button_row.addWidget(self.mark_btn)
        self.timer_and_progress.addLayout(button_row)
        self.timer_and_progress.addWidget(self.timer_label, alignment=Qt.AlignHCenter)
        self.timer_and_progress.addWidget(self.seek_slider)

        controls_container = QWidget()
        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.select_btn)
        self.controls_layout.addLayout(self.timer_and_progress, stretch=1)
        self.controls_layout.addWidget(self.speed_combo)
        self.controls_layout.addWidget(QLabel("Skip"))
        self.controls_layout.addWidget(self.skip_combo)
        self.controls_layout.addWidget(QLabel("Volume"))
        self.controls_layout.addWidget(self.volume_slider)
        controls_container.setLayout(self.controls_layout)
        self.grid.addWidget(controls_container, 2, 0, 1, 2)

        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.stop_btn.clicked.connect(self.player_widget.stop)
        self.select_btn.clicked.connect(self.player_widget.confirm_region_selection)
        self.seek_slider.sliderMoved.connect(self._seek_video)
        self.player_widget.media_player.positionChanged.connect(self._sync_seek_slider)
        self.player_widget.media_player.durationChanged.connect(self._sync_seek_slider)
        self.player_widget.media_player.positionChanged.connect(self._update_timer_label)
        self.player_widget.media_player.durationChanged.connect(self._update_timer_label)
        self.player_widget.media_player.playbackStateChanged.connect(self._refresh_play_button)
        self._refresh_play_button()
        self._update_timer_label()
        self.volume_slider.valueChanged.connect(
            lambda value: self.player_widget.set_volume(value / 100.0)
        )
        # Speed control connection (dropdown)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)

    def _init_button_styles(self) -> None:
        self._button_styles = {
            "primary": self._build_button_style("#2563eb", "#1d4ed8", "#1e40af"),
            "accent": self._build_button_style("#8b5cf6", "#7c3aed", "#6d28d9"),
            "danger": self._build_button_style("#f97316", "#ea580c", "#c2410c"),
            "neutral": self._build_button_style("#374151", "#2f3542", "#252932"),
            "muted": self._build_button_style("#1f2937", "#19212f", "#131924"),
        }
        self._play_idle_style = self._build_button_style("#22c55e", "#16a34a", "#15803d")
        self._play_active_style = self._build_button_style("#f59e0b", "#d97706", "#b45309")

    def _apply_button_styles(self) -> None:
        self.pick_file_btn.setStyleSheet(self._button_styles["primary"])
        self.cut_btn.setStyleSheet(self._button_styles["danger"])
        self.merge_btn.setStyleSheet(self._button_styles["accent"])
        self.blur_btn.setStyleSheet(self._button_styles["primary"])
        self.black_btn.setStyleSheet(self._button_styles["muted"])
        self.audio_btn.setStyleSheet(self._button_styles["neutral"])
        self.play_btn.setStyleSheet(self._play_idle_style)
        self.stop_btn.setStyleSheet(self._button_styles["danger"])
        self.mark_btn.setStyleSheet(self._button_styles["accent"])
        self.select_btn.setStyleSheet(self._button_styles["muted"])

    @staticmethod
    def _build_button_style(base: str, hover: str, pressed: str) -> str:
        return (
            "QPushButton {"
            f"background-color: {base};"
            "color: #f8fafc;"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 10px;"
            "padding: 8px 16px;"
            "font-weight: 600;"
            "letter-spacing: 0.3px;"
            "min-width: 0;"
            "}"
            "QPushButton:hover {"
            f"background-color: {hover};"
            "}"
            "QPushButton:pressed {"
            f"background-color: {pressed};"
            "}"
            "QPushButton:disabled {"
            "background-color: #1c1f29;"
            "color: #5f6b7c;"
            "border-color: #1c1f29;"
            "}"
        )

    def update_responsive_controls(self, width: int) -> None:
        if width < 900:
            self.mark_btn.setText("")
            self.mark_btn.setToolTip("Mark Cut")
        else:
            self.mark_btn.setText("Mark Cut")

    def _on_speed_changed(self, idx):
        rates = [0.5, 1.0, 1.5, 2.0]
        self.player_widget.set_speed(rates[idx])

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

    def seek_step_ms(self) -> int:
        data = self.skip_combo.currentData()
        try:
            return int(data)
        except (TypeError, ValueError):
            return 10_000

    def set_cut_markers(self, ratios: list[float]) -> None:
        """Display cut markers on the seek slider."""
        self.seek_slider.set_markers(ratios)

    def toggle_play_pause(self) -> None:
        from PySide6.QtMultimedia import QMediaPlayer

        state = self.player_widget.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player_widget.pause()
        else:
            self.player_widget.resume()

    def _refresh_play_button(self) -> None:
        from PySide6.QtMultimedia import QMediaPlayer

        state = self.player_widget.media_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setIcon(self._pause_icon)
            self.play_btn.setToolTip("Pause")
            self.play_btn.setStyleSheet(self._play_active_style)
        else:
            self.play_btn.setIcon(self._play_icon)
            self.play_btn.setToolTip("Play")
            self.play_btn.setStyleSheet(self._play_idle_style)
