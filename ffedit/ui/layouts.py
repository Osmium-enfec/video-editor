from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
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
from ffedit.ui.widgets import ClickableLabel, MarkerSlider


class MainWindowLayout:
    def __init__(self, main_window):
        self.main_window = main_window
        self.player_widget = PlayerWidget(main_window)
        self.player_widget.set_main_window(main_window)
        self.file_label = QLabel("No file selected")
        self.ffmpeg_status = QLabel("ffmpeg: unknown")
        self.ffmpeg_icon = QLabel()
        self.ffmpeg_icon.setFixedSize(16, 16)
        self.pick_file_btn = QPushButton("Pick Video File")
        self.add_video_btn = QPushButton("Add Video")
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
        self._apply_button_dimensions()
        self.update_responsive_controls(self.main_window.width())

    def _build_options_column(self):
        options_container = QWidget()
        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignTop)
        options_layout.addWidget(self.file_label)
        # ffmpeg status row (icon + label)
        from PySide6.QtWidgets import QHBoxLayout
        ff_row = QHBoxLayout()
        ff_row.setSpacing(6)
        ff_row.addWidget(self.ffmpeg_icon)
        ff_row.addWidget(self.ffmpeg_status)
        options_layout.addLayout(ff_row)
        options_layout.addWidget(self.pick_file_btn)
        options_layout.addWidget(self.add_video_btn)
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
        self.timer_label = ClickableLabel("00:00:00.000 / 00:00:00.000")
        self.timer_label.setCursor(Qt.PointingHandCursor)
        self.timer_label.setToolTip("Click to jump to a specific time")
        self.timer_label.clicked.connect(self._prompt_seek_to_time)

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
            "primary": self._build_button_style("#4b5563", "#3f4853", "#323840"),
            "accent": self._build_button_style("#444c57", "#383f47", "#2a2f36"),
            "danger": self._build_button_style("#3b424a", "#30363d", "#24282e"),
            "neutral": self._build_button_style("#353b43", "#2b3036", "#1f2327"),
            "muted": self._build_button_style("#2b3036", "#25292e", "#1a1d20"),
        }

        self._control_button_styles = {
            "play_idle": self._build_button_style("#22c55e", "#16a34a", "#15803d"),
            "play_active": self._build_button_style("#f59e0b", "#d97706", "#b45309"),
            "stop": self._build_button_style("#ef4444", "#dc2626", "#b91c1c"),
            "mark": self._build_button_style("#8b5cf6", "#7c3aed", "#6d28d9"),
            "select": self._build_button_style("#1f2937", "#19212f", "#131924"),
        }
        self._play_idle_style = self._control_button_styles["play_idle"]
        self._play_active_style = self._control_button_styles["play_active"]

    def _apply_button_styles(self) -> None:
        self.pick_file_btn.setStyleSheet(self._button_styles["primary"])
        self.add_video_btn.setStyleSheet(self._button_styles["primary"])
        self.cut_btn.setStyleSheet(self._button_styles["danger"])
        self.merge_btn.setStyleSheet(self._button_styles["accent"])
        self.blur_btn.setStyleSheet(self._button_styles["primary"])
        self.black_btn.setStyleSheet(self._button_styles["muted"])
        self.audio_btn.setStyleSheet(self._button_styles["neutral"])

        self.play_btn.setStyleSheet(self._play_idle_style)
        self.stop_btn.setStyleSheet(self._control_button_styles["stop"])
        self.mark_btn.setStyleSheet(self._control_button_styles["mark"])
        self.select_btn.setStyleSheet(self._control_button_styles["select"])

    def _apply_button_dimensions(self) -> None:
        option_buttons = [
            self.pick_file_btn,
            self.add_video_btn,
            self.cut_btn,
            self.merge_btn,
            self.blur_btn,
            self.black_btn,
            self.audio_btn,
        ]
        for btn in option_buttons:
            btn.setFixedHeight(32)

        control_buttons = [self.play_btn, self.stop_btn, self.mark_btn, self.select_btn]
        for btn in control_buttons:
            btn.setFixedHeight(40)

    @staticmethod
    def _build_button_style(base: str, hover: str, pressed: str) -> str:
        return (
            "QPushButton {"
            f"background-color: {base};"
            "color: #f3f4f6;"
            "border: 1px solid rgba(255, 255, 255, 0.05);"
            "border-radius: 6px;"
            "padding: 4px 10px;"
            "font-weight: 500;"
            "font-size: 13px;"
            "min-width: 0;"
            "}"
            "QPushButton:hover {"
            f"background-color: {hover};"
            "}"
            "QPushButton:pressed {"
            f"background-color: {pressed};"
            "}"
            "QPushButton:disabled {"
            "background-color: #16181d;"
            "color: #4b5563;"
            "border-color: #111216;"
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
        duration_ms = self.player_widget.media_player.duration()
        position_ms = self.player_widget.media_player.position()
        self.timer_label.setText(
            f"{self._format_timestamp(position_ms)} / {self._format_timestamp(duration_ms)}"
        )

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

    def set_cut_markers(
        self,
        active: list[float],
        archived: list[float] | None = None,
    ) -> None:
        """Display cut markers with separate colors for active vs archived segments."""

        marker_payload = []
        for ratio in archived or []:
            marker_payload.append(
                {
                    "ratio": ratio,
                    "color": "#22c55e",
                    "removable": False,
                }
            )
        for ratio in active:
            marker_payload.append(
                {
                    "ratio": ratio,
                    "color": "#ff3b30",
                    "removable": True,
                }
            )
        self.seek_slider.set_markers(marker_payload)

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

    def _prompt_seek_to_time(self) -> None:
        duration_ms = self.player_widget.media_player.duration()
        if duration_ms <= 0:
            self.log_panel.append("Load a video before jumping to a specific time.")
            return

        current_text = self._format_timestamp(self.player_widget.media_player.position())
        text, ok = QInputDialog.getText(
            self.main_window,
            "Go To Time",
            "Enter a time (seconds or hh:mm:ss:cc / hh:mm:ss.mmm):",
            text=current_text,
        )
        if not ok:
            return
        value = text.strip()
        if not value:
            return

        try:
            target_ms = self._parse_time_input(value)
        except ValueError:
            self.log_panel.append(
                "Invalid time. Use seconds or hh:mm:ss with optional milliseconds/frames."
            )
            return

        clamped = max(0, min(target_ms, duration_ms))
        self.player_widget.media_player.setPosition(clamped)
        self._update_timer_label()

    @staticmethod
    def _format_timestamp(ms: int) -> str:
        ms = max(0, int(ms or 0))
        h = ms // 3_600_000
        m = (ms % 3_600_000) // 60_000
        s = (ms % 60_000) // 1000
        rem_ms = ms % 1000
        return f"{h:02}:{m:02}:{s:02}.{rem_ms:03}"

    @staticmethod
    def _parse_time_input(text: str) -> int:
        stripped = (text or "").strip()
        if not stripped:
            raise ValueError("empty time value")
        try:
            if ":" not in stripped:
                seconds = float(stripped)
            else:
                parts = stripped.split(":")
                if len(parts) == 4:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds_part = float(parts[2])
                    fraction = parts[3]
                    frac_seconds = float(fraction) / (10 ** len(fraction)) if fraction else 0.0
                    seconds = hours * 3600 + minutes * 60 + seconds_part + frac_seconds
                else:
                    float_parts = [float(part) for part in parts]
                    while len(float_parts) < 3:
                        float_parts.insert(0, 0.0)
                    hours, minutes, seconds_part = float_parts[-3:]
                    seconds = hours * 3600 + minutes * 60 + seconds_part
        except ValueError as exc:
            raise ValueError("invalid time format") from exc
        return int(max(0.0, seconds) * 1000)
