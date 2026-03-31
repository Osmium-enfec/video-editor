"""Custom widgets for ffedit UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QLabel, QSlider, QStyle, QStyleOptionSlider


class MarkerSlider(QSlider):
    """QSlider subclass that can render marker dots along the groove."""

    marker_removed = Signal(float)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._marker_data: list[tuple[float, QColor, bool]] = []

    def set_markers(self, markers) -> None:
        """Accepts floats, (ratio, color, removable) tuples, or dicts with keys."""
        parsed: list[tuple[float, QColor, bool]] = []
        for marker in markers:
            ratio = 0.0
            color = QColor("#ff3b30")
            removable = True
            if isinstance(marker, dict):
                ratio = float(marker.get("ratio", 0.0))
                color = QColor(marker.get("color", "#ff3b30"))
                removable = bool(marker.get("removable", True))
            elif isinstance(marker, (list, tuple)):
                if marker:
                    ratio = float(marker[0])
                if len(marker) > 1:
                    color = QColor(marker[1])
                if len(marker) > 2:
                    removable = bool(marker[2])
            else:
                ratio = float(marker)
            ratio = max(0.0, min(1.0, ratio))
            parsed.append((ratio, color, removable))
        self._marker_data = parsed
        self.update()

    def remove_marker_at_position(self, ratio: float, threshold: float = 0.02) -> float | None:
        """Remove nearest removable marker near ratio (if any)."""
        if not self._marker_data:
            return None
        threshold = abs(threshold)
        closest_idx = None
        closest_diff = threshold
        for idx, (marker_ratio, _color, removable) in enumerate(self._marker_data):
            if not removable:
                continue
            diff = abs(marker_ratio - ratio)
            if diff <= closest_diff:
                closest_idx = idx
                closest_diff = diff
        if closest_idx is None:
            return None
        removed_ratio, _, _ = self._marker_data.pop(closest_idx)
        self.update()
        self.marker_removed.emit(removed_ratio)
        return removed_ratio

    def paintEvent(self, event):  # type: ignore[override]
        super().paintEvent(event)
        if not self._marker_data:
            return

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(
            QStyle.ComplexControl.CC_Slider,
            opt,
            QStyle.SubControl.SC_SliderGroove,
            self,
        )
        if groove.width() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ff3b30"))

        center_y = groove.center().y()
        radius = 4
        min_x = groove.left()
        max_x = groove.right()
        for ratio, color, _ in self._marker_data:
            painter.setBrush(color)
            x = min_x + int(ratio * (max_x - min_x))
            painter.drawEllipse(x - radius, center_y - radius, radius * 2, radius * 2)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):  # type: ignore[override]
        if event.button() == Qt.LeftButton and self._marker_data:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            groove = self.style().subControlRect(
                QStyle.ComplexControl.CC_Slider,
                opt,
                QStyle.SubControl.SC_SliderGroove,
                self,
            )
            if groove.width() > 0:
                ratio = (event.position().x() - groove.left()) / max(1, groove.width())
                removed = self.remove_marker_at_position(ratio)
                if 0.0 <= ratio <= 1.0 and removed is not None:
                    event.accept()
                    return
        super().mousePressEvent(event)


class ClickableLabel(QLabel):
    """Simple QLabel that emits a signal when clicked."""

    clicked = Signal()

    def mousePressEvent(self, event: QMouseEvent):  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
