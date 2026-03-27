"""Video preview widget with draggable region selection overlay."""

from __future__ import annotations

import os
from typing import Optional, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, QUrl, QEvent, QObject
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QLabel,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QRubberBand,
)


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
    def set_speed(self, rate: float) -> None:
        """Set playback speed (rate: 0.5, 1.0, 1.5, 2.0)."""
        self.media_player.setPlaybackRate(rate)

    def __init__(self, main_window=None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.main_window = main_window
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self._last_file = None
        self._drop_enabled = True

        self.setAcceptDrops(True)
        self.video_widget = QVideoWidget(self)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.region_selector = RegionSelector(self.video_widget)
        self.video_widget.setAcceptDrops(True)
        self.video_widget.installEventFilter(self)

        self._drop_hint_label = QLabel(
            "Drag a video into this preview area or use Pick Video File.\n"
            "Only the first dropped file will be accepted."
        )
        self._drop_hint_label.setAlignment(Qt.AlignCenter)
        self._drop_hint_label.setWordWrap(True)
        self._drop_hint_label.setStyleSheet(
            "color: #f0f0f0; background-color: #141414;"
            "padding: 20px; border: 1px dashed rgba(255, 255, 255, 120);"
            "font-size: 15px;"
        )
        self._drop_hint_label.setAcceptDrops(True)
        self._drop_hint_label.installEventFilter(self)

        placeholder_layout = QVBoxLayout()
        placeholder_layout.setContentsMargins(32, 32, 32, 32)
        placeholder_layout.addStretch()
        placeholder_layout.addWidget(self._drop_hint_label)
        placeholder_layout.addStretch()

        self._drop_placeholder = QWidget(self)
        self._drop_placeholder.setLayout(placeholder_layout)
        self._drop_placeholder.setStyleSheet("background-color: #000000;")
        self._drop_placeholder.setAcceptDrops(True)
        self._drop_placeholder.installEventFilter(self)

        self._stack = QStackedLayout()
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._drop_placeholder)
        self._stack.addWidget(self.video_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self._stack)
        self.setLayout(layout)
        self._set_drop_hint_visible(True)

        self.media_player.setVideoOutput(self.video_widget)

    def set_main_window(self, main_window) -> None:
        self.main_window = main_window

    def play(self, file_path: str) -> None:
        self._last_file = file_path
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()
        was_enabled = self._drop_enabled
        self.disable_drag_drop()
        if was_enabled:
            self._log("Drag-and-drop disabled after video load.")

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

    def seek_by(self, delta_ms: int) -> None:
        """Seek relative to the current position, clamped within media bounds."""
        duration = self.media_player.duration()
        if duration <= 0:
            return
        new_position = self.media_player.position() + delta_ms
        new_position = max(0, min(new_position, duration))
        self.media_player.setPosition(new_position)

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

    def _set_drop_hint_visible(self, visible: bool) -> None:
        placeholder = getattr(self, "_drop_placeholder", None)
        stack = getattr(self, "_stack", None)
        if not placeholder or not stack:
            return
        should_show = visible and self._drop_enabled
        target = self._drop_placeholder if should_show else self.video_widget
        stack.setCurrentWidget(target)
        self._drop_hint_label.setVisible(should_show)

    def eventFilter(self, watched, event):  # type: ignore[override]
        placeholder = getattr(self, "_drop_placeholder", None)
        overlay = getattr(self, "_drop_hint_label", None)
        if watched in (self.video_widget, placeholder, overlay) and event.type() in (
            QEvent.DragEnter,
            QEvent.DragMove,
            QEvent.Drop,
        ):
            return self._handle_drag_drop_event(event)
        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):  # type: ignore[override]
        if not self._handle_drag_drop_event(event):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):  # type: ignore[override]
        if not self._handle_drag_drop_event(event):
            super().dragMoveEvent(event)

    def dropEvent(self, event):  # type: ignore[override]
        if not self._handle_drag_drop_event(event):
            super().dropEvent(event)

    def disable_drag_drop(self) -> None:
        self._drop_enabled = False
        self._set_drop_hint_visible(False)

    def _handle_drag_drop_event(self, event) -> bool:
        if event.type() in (QEvent.DragEnter, QEvent.DragMove):
            if self._can_accept_drag(event):
                event.setDropAction(Qt.CopyAction)
                event.acceptProposedAction()
            else:
                event.ignore()
            return True
        if event.type() == QEvent.Drop:
            self._handle_drop(event)
            return True
        return False

    def _can_accept_drag(self, event) -> bool:
        if not self._drop_enabled:
            return False
        mime_data = getattr(event, "mimeData", lambda: None)()
        if not mime_data:
            return False
        return bool(self._extract_first_video_path(mime_data))

    def _handle_drop(self, event) -> None:
        if not self._drop_enabled:
            self._log(
                "Drag-and-drop works only before a video is loaded. Use Pick Video File after that."
            )
            event.ignore()
            return
        mime_data = getattr(event, "mimeData", lambda: None)()
        file_path = self._extract_first_video_path(mime_data) if mime_data else None
        if not file_path:
            self._log(
                "Dropped item is not a supported local video (.mp4, .mov, .avi, .mkv)."
            )
            event.ignore()
            return
        self._apply_dropped_file(file_path)
        event.acceptProposedAction()

    def _extract_first_video_path(self, mime_data) -> Optional[str]:
        urls = mime_data.urls() if hasattr(mime_data, "urls") else []
        if not urls:
            return None
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if self._is_supported_video(path):
                    return path
        return None

    @staticmethod
    def _is_supported_video(path: str) -> bool:
        valid_ext = {".mp4", ".mov", ".avi", ".mkv"}
        _, ext = os.path.splitext(path.lower())
        return ext in valid_ext and os.path.isfile(path)

    def _apply_dropped_file(self, file_path: str) -> None:
        window, layout = self._resolve_main_window()
        if not window or not layout:
            return
        layout.file_label.setText(file_path)
        layout.log_panel.append(f"Dropped file: {file_path}")
        window.input_file = file_path
        self.play(file_path)
        layout.log_panel.append("Note: drag-and-drop is now disabled for safety.")
