"""Floating screen-edge handle used to summon the docked timer window.

When the main window docks it slides fully off-screen and this small
translucent pill stays pinned to the screen edge. Idle it is a subtle
tab with a faint dot; hovering smoothly grows the pill and reveals a
stylized arrow. Clicking slides the window back in.
"""

from PyQt6.QtCore import (
    QEasingCurve,
    QPointF,
    QRectF,
    Qt,
    QPropertyAnimation,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget


class EdgeHandle(QWidget):
    """Subtle glassy pill pinned to a screen edge."""

    IDLE_W = 10.0
    HOVER_W = 24.0
    HEIGHT = 64
    MARGIN = 7  # painted room for the soft shadow on the inner side
    HOVER_MS = 160
    FADE_MS = 150

    def __init__(self, edge: str, on_activate) -> None:
        """Create the handle.

        Args:
            edge: "left" or "right" screen edge to pin to
            on_activate: Called when the handle is clicked
        """
        super().__init__()
        self._edge = edge if edge in ("left", "right") else "right"
        self._on_activate = on_activate
        self._hover_t = 0.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setFixedSize(
            int(self.HOVER_W) + self.MARGIN, self.HEIGHT + self.MARGIN * 2
        )

        self._hover_anim = QPropertyAnimation(self, b"hoverT", self)
        self._hover_anim.setDuration(self.HOVER_MS)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(self.FADE_MS)
        self._fade_anim.finished.connect(self._on_faded_out)

    # -- geometry ---------------------------------------------------------------
    def set_edge(self, edge: str) -> None:
        """Switch the pinned screen edge."""
        if edge in ("left", "right") and edge != self._edge:
            self._edge = edge
            self.update()

    def place(self, avail, y: int) -> None:
        """Pin the handle to the screen edge at the given y position."""
        y = int(max(avail.top() + 4, min(y, avail.bottom() - self.height() - 4)))
        if self._edge == "right":
            x = int(avail.right()) + 1 - self.width()
        else:
            x = int(avail.left())
        self.move(x, y)

    # -- animated hover property -------------------------------------------------
    def _get_hover_t(self) -> float:
        return self._hover_t

    def _set_hover_t(self, value: float) -> None:
        self._hover_t = float(value)
        self.update()

    hoverT = pyqtProperty(float, _get_hover_t, _set_hover_t)

    # -- painting -----------------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.IDLE_W + (self.HOVER_W - self.IDLE_W) * self._hover_t
        h = float(self.HEIGHT)
        x = float(self.width() - w) if self._edge == "right" else 0.0
        y = (self.height() - h) / 2.0
        pill = QRectF(x, y, w, h)
        radius = w / 2.0

        # Soft shadow bleeding toward the screen interior
        painter.setPen(Qt.PenStyle.NoPen)
        for grow, alpha in ((2.0, 34), (4.0, 22), (6.0, 13)):
            if self._edge == "right":
                shadow = pill.adjusted(-grow, 0, 0, 0)
            else:
                shadow = pill.adjusted(0, 0, grow, 0)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(shadow, radius + grow, radius + grow)

        # Glassy pill body with a hairline border
        painter.setBrush(QColor(18, 20, 26, 212))
        painter.setPen(QPen(QColor(255, 255, 255, 76), 1.0))
        painter.drawRoundedRect(pill, radius, radius)

        # Top highlight for the glass feel, brighter on hover
        painter.setPen(
            QPen(QColor(255, 255, 255, int(26 + 44 * self._hover_t)), 1.0)
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        highlight = QRectF(pill)
        highlight.adjust(1.5, 1.5, -1.5, -pill.height() / 2)
        painter.drawRoundedRect(highlight, radius, radius)

        center = pill.center()
        if self._hover_t > 0.02:
            self._draw_arrow(painter, center)
        else:
            # Subtle idle dot so the tab is discoverable but quiet
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(235, 240, 255, 95))
            painter.drawEllipse(center, 1.7, 1.7)
        painter.end()

    def _draw_arrow(self, painter: QPainter, center: QPointF) -> None:
        """Paint the chevron pointing away from the screen edge."""
        size = 3.5 + 2.5 * self._hover_t
        direction = -1.0 if self._edge == "right" else 1.0
        pen = QPen(QColor(240, 244, 255, int(235 * self._hover_t)), 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        path = QPainterPath()
        path.moveTo(QPointF(center.x() - direction * size, center.y() - size))
        path.lineTo(QPointF(center.x() + direction * size, center.y()))
        path.lineTo(QPointF(center.x() - direction * size, center.y() + size))
        painter.drawPath(path)

    # -- interaction ----------------------------------------------------------------
    def enterEvent(self, event) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_t)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()

    def leaveEvent(self, event) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_t)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                self._on_activate()
            except Exception:
                pass

    # -- show / hide ------------------------------------------------------------------
    def fade_out(self) -> None:
        """Smoothly fade the handle away before the window slides back."""
        if not self.isVisible():
            return
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def _on_faded_out(self) -> None:
        self.hide()
        self.setWindowOpacity(1.0)
        self._set_hover_t(0.0)

    def showEvent(self, event) -> None:
        self.setWindowOpacity(1.0)
        super().showEvent(event)
