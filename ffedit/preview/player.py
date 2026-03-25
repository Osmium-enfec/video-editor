"""Video preview widget with draggable region selection overlay."""

from __future__ import annotations

import os
from typing import Optional, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, QUrl, QEvent, QObject
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QRubberBand


class RegionSelector(QObject):
    """Rubber-band driven selection manager attached to the video widget."""

    MIN_SIZE = 12

    def __init__(self, target_widget: QWidget) -> None:
        super().__init__(target_widget)
        self.target = target_widget
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, target_widget)
        self.rubber_band.setStyleSheet(
            "border: 2px solid #ff3b30; background-color: rgba(255,255,0,60);"
        )
        self.selection_rect = QRect()
        self.active = False
        self.dragging = False
        self.drawing = False
        self.drag_offset = QPoint(0, 0)
        self.origin = QPoint(0, 0)
        target_widget.installEventFilter(self)

    def start_selection(self, initial_rect: QRect) -> None:
        self.active = True
        self.selection_rect = self._clamp_rect(initial_rect)
        self.rubber_band.setGeometry(self.selection_rect)
        self.rubber_band.show()

    def stop_selection(self) -> None:
        self.active = False
        self.dragging = False
        self.drawing = False
        self.rubber_band.hide()

    def is_active(self) -> bool:
        return self.active

    def get_rect(self) -> Optional[Tuple[int, int, int, int]]:
        if self.selection_rect.isNull():
            return None
        rect = self.selection_rect.normalized()
        return (rect.x(), rect.y(), rect.width(), rect.height())

    def eventFilter(self, watched, event):  # type: ignore[override]
        if watched is not self.target or not self.active:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._handle_mouse_press(self._event_point(event))
            return True

        if event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
            self._handle_mouse_move(self._event_point(event))
            return True

        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.dragging = False
            self.drawing = False
            return True

        if event.type() == QEvent.Resize:
            if not self.selection_rect.isNull():
                self.selection_rect = self._clamp_rect(self.selection_rect)
                self.rubber_band.setGeometry(self.selection_rect)
            return False

        return False

    def _handle_mouse_press(self, pos: QPoint) -> None:
        pos = self._clamp_point(pos)
        if self.selection_rect.contains(pos):
            self.dragging = True
            self.drawing = False
            self.drag_offset = pos - self.selection_rect.topLeft()
        else:
            self.drawing = True
            self.dragging = False
            self.origin = pos
            self.selection_rect = QRect(pos, pos)
        self.rubber_band.setGeometry(self.selection_rect.normalized())
        self.rubber_band.show()

    def _handle_mouse_move(self, pos: QPoint) -> None:
        pos = self._clamp_point(pos)
        if self.dragging:
            new_top_left = pos - self.drag_offset
            new_rect = QRect(new_top_left, self.selection_rect.size())
            self.selection_rect = self._clamp_rect(new_rect)
        elif self.drawing:
            rect = QRect(self.origin, pos).normalized()
            self.selection_rect = self._ensure_min_size(rect)
        else:
            return
        self.rubber_band.setGeometry(self.selection_rect)

    @staticmethod
    def _event_point(event) -> QPoint:
        try:
            return event.position().toPoint()
        except AttributeError:
            return event.pos()

    def _clamp_point(self, point: QPoint) -> QPoint:
        bounds = self.target.rect()
        return QPoint(
            max(bounds.left(), min(point.x(), bounds.right())),
            max(bounds.top(), min(point.y(), bounds.bottom())),
        )

    def _clamp_rect(self, rect: QRect) -> QRect:
        bounds = self.target.rect()
        rect = rect.normalized()
        max_w = max(1, bounds.width())
        max_h = max(1, bounds.height())
        x = max(bounds.left(), min(rect.x(), bounds.left() + max_w - self.MIN_SIZE))
        y = max(bounds.top(), min(rect.y(), bounds.top() + max_h - self.MIN_SIZE))
        w = max(self.MIN_SIZE, min(rect.width(), bounds.left() + max_w - x))
        h = max(self.MIN_SIZE, min(rect.height(), bounds.top() + max_h - y))
        return QRect(x, y, w, h)

    def _ensure_min_size(self, rect: QRect) -> QRect:
        rect = rect.normalized()
        if rect.width() < self.MIN_SIZE:
            rect.setWidth(self.MIN_SIZE)
        if rect.height() < self.MIN_SIZE:
            rect.setHeight(self.MIN_SIZE)
        return self._clamp_rect(rect)


class PlayerWidget(QWidget):
    def __init__(self, main_window=None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.main_window = main_window
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self._last_file: Optional[str] = None

        self.video_widget = QVideoWidget(self)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.region_selector = RegionSelector(self.video_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)

        self.media_player.setVideoOutput(self.video_widget)

    def set_main_window(self, main_window) -> None:
        self.main_window = main_window

    def play(self, file_path: str) -> None:
        self._last_file = file_path
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()

    def resume(self) -> None:
        if self._last_file:
            self.media_player.play()

    def pause(self) -> None:
        self.media_player.pause()

    def stop(self) -> None:
        self.media_player.stop()

    def seek_to_ratio(self, ratio: float) -> None:
        duration = self.media_player.duration()
        if duration > 0:
            ratio = max(0.0, min(1.0, ratio))
            self.media_player.setPosition(int(duration * ratio))

    def set_volume(self, value: float) -> None:
        self.audio_output.setVolume(max(0.0, min(1.0, value)))

    def show_region_selector_with_default(self) -> None:
        if not self._last_file:
            self._log("Load a video before selecting a region blur.")
            return
        video_rect = self.video_widget.rect()
        if video_rect.width() == 0 or video_rect.height() == 0:
            self._log("Video area is not ready yet. Try again once playback is visible.")
            return
        rect_w = max(60, video_rect.width() // 4)
        rect_h = max(60, video_rect.height() // 4)
        start_x = (video_rect.width() - rect_w) // 2
        start_y = (video_rect.height() - rect_h) // 2
        self.region_selector.start_selection(QRect(start_x, start_y, rect_w, rect_h))
        self._set_select_button_enabled(True)

    def confirm_region_selection(self) -> None:
        if not self.region_selector.is_active():
            self._log("Region blur is not active. Choose region-based blur first.")
            return
        if not self._last_file:
            self._log("Load a video before confirming a region blur.")
            return
        raw_region = self.region_selector.get_rect()
        if not raw_region:
            self._log("Select a valid rectangle before confirming.")
            return
        region = self._clamp_region_to_widget(raw_region)
        mapped_region = self._map_region_to_video_resolution(region)
        from PySide6.QtWidgets import QFileDialog, QInputDialog

        strength, ok_strength = QInputDialog.getInt(
            self,
            "Blur Strength",
            "Enter blur strength (1-50):",
            10,
            1,
            50,
        )
        if not ok_strength:
            return

        start_time, ok_start = QInputDialog.getText(
            self,
            "Blur Start Time",
            "Enter blur start time (in seconds or hh:mm:ss):",
            text="0",
        )
        if not ok_start:
            return
        start_time = start_time.strip() or "0"

        end_time, ok_end = QInputDialog.getText(
            self,
            "Blur End Time",
            "Enter blur end time (in seconds or hh:mm:ss):",
            text="",
        )
        if not ok_end:
            return
        end_time = end_time.strip() or None

        out_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Blurred Video As",
            os.path.expanduser("~"),
            "Video Files (*.mp4 *.mov *.avi *.mkv)",
        )
        if not out_file:
            return

        from ffedit.ffmpeg.blur import build_blur_command
        from ffedit.core.executor import FFmpegExecutor

        try:
            cmd = build_blur_command(
                self._last_file,
                out_file,
                region=mapped_region,
                strength=strength,
                start_time=start_time,
                end_time=end_time,
            )
        except ValueError as exc:
            self._log(f"Blur configuration error: {exc}")
            return

        window, layout = self._resolve_main_window()
        if not window or not layout:
            return

        progress = layout.progress
        log_panel = layout.log_panel
        self._log_region_details(region, mapped_region)
        log_panel.append(
            f"Starting region blur: strength={strength}, start={start_time}, end={end_time} -> {out_file}"
        )

        executor = FFmpegExecutor(cmd)
        executor.progress.connect(progress.setValue)
        executor.log.connect(log_panel.append)
        executor.finished.connect(window._on_blur_finished)  # type: ignore[attr-defined]
        window.executor = executor
        progress.setValue(0)
        executor.start()

        self.stop_region_selection()

    def stop_region_selection(self) -> None:
        self.region_selector.stop_selection()
        self._set_select_button_enabled(False)

    def _clamp_region_to_widget(self, region: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        x, y, w, h = region
        max_w = max(1, self.video_widget.width())
        max_h = max(1, self.video_widget.height())
        x = max(0, min(x, max_w))
        y = max(0, min(y, max_h))
        w = max(10, min(w, max_w - x))
        h = max(10, min(h, max_h - y))
        return (x, y, w, h)

    def _map_region_to_video_resolution(self, region: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        display_w = max(1, self.video_widget.width())
        display_h = max(1, self.video_widget.height())
        video_w, video_h = self._get_video_resolution()
        x, y, w, h = region
        scale_x = video_w / display_w
        scale_y = video_h / display_h
        mapped = (
            int(x * scale_x),
            int(y * scale_y),
            int(w * scale_x),
            int(h * scale_y),
        )
        return mapped

    def _get_video_resolution(self) -> Tuple[int, int]:
        import ffmpeg  # lazy import

        if not self._last_file:
            return (1, 1)
        try:
            probe = ffmpeg.probe(self._last_file)
            stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
            return int(stream.get("width", 1)), int(stream.get("height", 1))
        except Exception:
            return (1, 1)

    def _resolve_main_window(self):
        window = self.main_window
        if window is None:
            parent = self.parent()
            while parent and not hasattr(parent, "layout"):
                parent = parent.parent()
            window = parent
        layout = getattr(window, "layout", None) if window else None
        return window, layout

    def _log(self, message: str) -> None:
        _, layout = self._resolve_main_window()
        if layout and hasattr(layout, "log_panel"):
            layout.log_panel.append(message)

    def _set_select_button_enabled(self, enabled: bool) -> None:
        _, layout = self._resolve_main_window()
        if layout and hasattr(layout, "select_btn"):
            layout.select_btn.setEnabled(enabled)

    def _log_region_details(
        self,
        ui_region: Tuple[int, int, int, int],
        px_region: Tuple[int, int, int, int],
    ) -> None:
        display_w = max(1, self.video_widget.width())
        display_h = max(1, self.video_widget.height())
        x, y, w, h = ui_region
        ui_msg = (
            f"UI region: x={x/display_w*100:.1f}%, y={y/display_h*100:.1f}% "
            f"w={w/display_w*100:.1f}%, h={h/display_h*100:.1f}%"
        )
        px_msg = f"Video pixels: x={px_region[0]}, y={px_region[1]}, w={px_region[2]}, h={px_region[3]}"
        self._log(f"{ui_msg} | {px_msg}")
