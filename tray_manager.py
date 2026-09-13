"""System tray integration for DevOTime.

Prefers a native Shell_NotifyIcon tray (shell_tray.ShellTray) so the
icon can render the live timer as wide text, like the system clock.
Falls back to QSystemTrayIcon when the shell API is unavailable.
Keeps MainWindow free of tray plumbing.
"""

from typing import Callable

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from shell_tray import ShellTray


class TrayManager:
    """Tray icon with show/hide, pause, program and quit actions."""

    def __init__(
        self,
        icon_path: str,
        on_toggle_visible: Callable[[], None],
        on_toggle_pause: Callable[[], None],
        on_add_program: Callable[[], None],
        on_remove_program: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        """Create and show the tray icon.

        Args:
            icon_path: QRC path of the application icon
            on_toggle_visible: Show or hide the main window
            on_toggle_pause: Pause or resume the timer
            on_add_program: Start the add-tracked-program flow
            on_remove_program: Start the remove-tracked-program flow
            on_quit: Save state and quit the application
        """
        self._base_icon = QIcon(icon_path)
        self._last_icon_key: tuple[str, str, str] | None = None
        self.shell: ShellTray | None = None
        self.icon: QSystemTrayIcon | None = None

        self.menu = QMenu()
        self._toggle_visible_action = self.menu.addAction("Show / hide window")
        self._toggle_visible_action.triggered.connect(on_toggle_visible)
        self._pause_action = self.menu.addAction("Pause timer")
        self._pause_action.triggered.connect(on_toggle_pause)
        self.menu.addAction("Add program", on_add_program)
        self.menu.addAction("Remove program", on_remove_program)
        self.menu.addSeparator()
        self.menu.addAction("Quit").triggered.connect(on_quit)

        base_pixmap = self._base_icon.pixmap(self._tray_size())
        try:
            self.shell = ShellTray(
                base_pixmap,
                on_double_click=on_toggle_visible,
                on_context=self._show_context_menu,
            )
            self.available = True
            return
        except Exception as e:
            print(f"Native shell tray unavailable ({e}); falling back")
            self.shell = None

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.icon = QSystemTrayIcon(self._base_icon)
            self.icon.setContextMenu(self.menu)
            self.icon.setToolTip("DevOTime")
            self.icon.activated.connect(
                lambda reason: on_toggle_visible()
                if reason == QSystemTrayIcon.ActivationReason.DoubleClick
                else None
            )
            self.icon.show()
            self.available = True
        else:
            self.available = False
            print("System tray is not available on this system")

    # -- internals -----------------------------------------------------------
    def _show_context_menu(self) -> None:
        """Pop up the tray context menu at the cursor (shell tray path)."""
        from PyQt6.QtGui import QCursor

        self.menu.exec(QCursor.pos())

    def _tray_icon_height(self) -> int:
        """Small-icon height in physical pixels for the current DPI."""
        try:
            import ctypes

            h = ctypes.windll.user32.GetSystemMetrics(50)  # SM_CYSMICON
            return max(16, min(48, h))
        except Exception:
            return 16

    def _tray_size(self) -> QSize:
        """Square tray icon size in physical pixels."""
        return QSize(self._tray_icon_height(), self._tray_icon_height())

    # -- public API ----------------------------------------------------------
    def set_pause_label(self, paused: bool) -> None:
        """Update the pause menu entry to reflect the timer state."""
        if self.available:
            self._pause_action.setText("Resume timer" if paused else "Pause timer")

    def set_tooltip(self, text: str) -> None:
        """Update the tray tooltip (live timer display)."""
        if not self.available:
            return
        if self.shell is not None:
            self.shell.set_tooltip(text)
        elif self.icon is not None:
            self.icon.setToolTip(text)

    def set_text_icon(self, text: str, color: str) -> None:
        """Render the timer as a wide taskbar icon, clock-style.

        Only the native shell tray supports non-square icons; the Qt
        fallback keeps the regular icon and relies on the tooltip.
        """
        if not self.available or self.shell is None:
            return
        key = ("text", text, color)
        if key == self._last_icon_key:
            return
        self._last_icon_key = key
        self.shell.set_pixmap(self._render_text_pixmap(text, color))

    def set_normal_icon(self) -> None:
        """Restore the regular application icon."""
        if not self.available:
            return
        key = ("normal", "", "")
        if key == self._last_icon_key:
            return
        self._last_icon_key = key
        if self.shell is not None:
            self.shell.set_pixmap(self._base_icon.pixmap(self._tray_size()))
        elif self.icon is not None:
            self.icon.setIcon(self._base_icon)

    def _render_text_pixmap(self, text: str, color: str) -> QPixmap:
        """Paint the timer text into an ARGB pixmap sized for the tray."""
        height = self._tray_icon_height()
        font = QFont("Segoe UI")
        font.setPixelSize(max(10, height - 2))
        font.setBold(True)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        width = max(int(height * 1.3), text_width + 4)

        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return pixmap

    def show_message(self, title: str, message: str) -> None:
        """Show a balloon notification next to the tray icon."""
        if not self.available:
            return
        if self.shell is not None:
            self.shell.show_balloon(title, message)
        elif self.icon is not None:
            self.icon.showMessage(title, message, self._base_icon, 4000)

    def destroy(self) -> None:
        """Remove the icon from the tray. Safe to call multiple times."""
        if not self.available:
            return
        self.available = False
        try:
            if self.shell is not None:
                self.shell.destroy()
                self.shell = None
            if self.icon is not None:
                self.icon.hide()
                self.icon.setContextMenu(None)
                self.icon.deleteLater()
                self.icon = None
        except Exception:
            pass
