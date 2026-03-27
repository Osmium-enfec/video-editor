"""Custom widgets for ffedit UI."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QSlider, QStyle, QStyleOptionSlider


class MarkerSlider(QSlider):
    """QSlider subclass that can render marker dots along the groove."""

    marker_removed = Signal(float)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._marker_ratios: list[float] = []

    def set_markers(self, ratios: list[float]) -> None:
        self._marker_ratios = [max(0.0, min(1.0, r)) for r in ratios]
        self.update()

    def remove_marker_at_position(self, ratio: float, threshold: float = 0.02) -> float | None:
        """Remove marker near ratio (if any) and return its exact ratio."""
        if not self._marker_ratios:
            return None
        threshold = abs(threshold)
        for idx, marker in enumerate(self._marker_ratios):
            if abs(marker - ratio) <= threshold:
                removed = self._marker_ratios.pop(idx)
                self.update()
                self.marker_removed.emit(removed)
                return removed
        return None

    def paintEvent(self, event):  # type: ignore[override]
        super().paintEvent(event)
        if not self._marker_ratios:
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
        for ratio in self._marker_ratios:
            x = min_x + int(ratio * (max_x - min_x))
            painter.drawEllipse(x - radius, center_y - radius, radius * 2, radius * 2)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):  # type: ignore[override]
        if event.button() == Qt.LeftButton and self._marker_ratios:
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
