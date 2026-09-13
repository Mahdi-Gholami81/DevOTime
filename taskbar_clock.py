"""A taskbar strip that shows the DevOTime timer at full taskbar size.

A borderless, click-through-friendly topmost strip glued to the taskbar
immediately left of the notification area (the "show hidden icons"
arrow), drawing the live timer like a native clock widget. Tray icons
are capped at ~16px, so this is the only way to get a readable timer
in the taskbar itself.
"""

import ctypes
from ctypes import wintypes

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import QWidget

user32 = ctypes.windll.user32
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowExW.restype = wintypes.HWND
user32.SetWindowPos.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_uint,
]


class TaskbarClockStrip(QWidget):
    """Timer display rendered inside the taskbar, left of the tray."""

    PADDING = 8
    GAP = 4  # gap kept between the strip and the notification area

    def __init__(self, on_left_click, on_right_click, dark_taskbar: bool) -> None:
        """Create the strip.

        Args:
            on_left_click: Called when the strip is clicked with LMB
            on_right_click: Called when the strip is clicked with RMB
            dark_taskbar: True when the taskbar uses a dark theme
        """
        super().__init__()
        self.on_left_click = on_left_click
        self.on_right_click = on_right_click
        self.text_color = "#E6E6E6" if dark_taskbar else "#1A1A1A"

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._text = ""
        self._last_rect: tuple[int, int, int, int] | None = None
        self._max_width = 96
        self._apply_font(48)
        self.setFixedSize(self._max_width, 48)

    # -- display ---------------------------------------------------------------
    def _apply_font(self, taskbar_height: int) -> None:
        size = max(12, min(18, int(taskbar_height * 0.30)))
        if getattr(self, "_font_size", None) == size:
            return
        self._font_size = size
        self._font = QFont("Segoe UI")
        self._font.setPixelSize(size)
        self._font.setBold(True)
        # Fixed width sized for the widest possible text, so per-second
        # updates never resize or reposition the window (flicker source).
        self._max_width = (
            QFontMetrics(self._font).horizontalAdvance("00:00:00") + self.PADDING * 2
        )

    def set_display(self, text: str) -> None:
        """Update the shown timer text (repaint only, never resize)."""
        if text == self._text:
            return
        self._text = text
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(self._font)
        painter.setPen(QColor(self.text_color))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()

    # -- placement ---------------------------------------------------------------
    def ensure_position(self, reassert_topmost: bool = False) -> bool:
        """Glue the strip to the taskbar left of the notification area.

        Args:
            reassert_topmost: Force the topmost z-order refresh even when
                the geometry did not change (periodic keep-alive)

        Returns:
            True when the strip is placed on a visible taskbar.
        """
        tray = user32.FindWindowW("Shell_TrayWnd", None)
        if not tray:
            self.hide()
            return False
        notify = user32.FindWindowExW(tray, None, "TrayNotifyWnd", None)

        tb = wintypes.RECT()
        user32.GetWindowRect(tray, ctypes.byref(tb))
        nt = wintypes.RECT()
        if notify:
            user32.GetWindowRect(notify, ctypes.byref(nt))

        tb_w, tb_h = tb.right - tb.left, tb.bottom - tb.top
        bottom_taskbar = tb_w >= tb_h

        self._apply_font(tb_h if bottom_taskbar else tb_w)
        width = self._max_width

        if bottom_taskbar:
            right_edge = (nt.left if notify else tb.right) - self.GAP
            x = right_edge - width
            y, height = tb.top, tb_h
        else:
            # Vertical taskbar on the left/right edge
            if tb.left > 0:  # taskbar on the right side of the screen
                x = tb.left
            else:  # taskbar on the left side
                x = tb.right + self.GAP
            top_edge = (nt.top if notify else tb.top) - self.GAP
            y = max(tb.top, top_edge - self.height())
            height = tb_w

        if self.size() != QSize(width, height):
            self.setFixedSize(width, height)

        rect = (x, y, width, height)
        if rect != self._last_rect:
            self._last_rect = rect
            self.move(x, y)
            self._reassert_topmost()
        elif reassert_topmost:
            self._reassert_topmost()
        if not self.isVisible():
            self.show()
        return True

    def _reassert_topmost(self) -> None:
        """Re-assert the topmost z-order so the strip stays above the taskbar."""
        hwnd = int(self.winId())
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0010)

    # -- interaction -------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_left_click()
        elif event.button() == Qt.MouseButton.RightButton:
            self.on_right_click()
