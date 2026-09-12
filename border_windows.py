from PyQt6.QtCore import QEvent, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QGuiApplication
from PyQt6.QtWidgets import QWidget


class BorderWindow(QWidget):
    """A frameless window that draws a colored border around the entire screen.

    This widget is used to create a visual indicator around the screen edges,
    typically used to indicate when the system has detected user idleness.

    The window is completely transparent except for the border, and stays
    on top of all other windows.
    """

    def __init__(self, geometry: QRect) -> None:
        """Initialize the border window with the specified screen geometry.

        Args:
            geometry: The QRect defining the screen area to surround with a border
        """
        super().__init__()
        self.setGeometry(geometry)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # NOTE: caller decides when to show(); do not auto-show here so
        # hidden/destroyed state is fully controlled by BorderWindows.

    def paintEvent(self, a0: QEvent) -> None:
        event = a0
        painter: QPainter = QPainter()
        painter.begin(self)
        self.drawBorder(painter)
        painter.end()

    def drawBorder(self, painter: QPainter) -> None:
        color: QColor = QColor(240, 112, 112)
        painter.setPen(QPen(color, 8))  # Set pen color and width
        painter.drawRect(0, 0, self.width(), self.height())  # Draw border rectangle


class BorderWindows:
    def __init__(self) -> None:
        self.border_windows: list = []
        self.is_visible: bool = False

    def create_border_windows(self) -> None:
        screens = QGuiApplication.screens()
        if screens:
            for screen in screens:
                geometry: QRect = screen.geometry()
                border_window: BorderWindow = BorderWindow(geometry)
                self.border_windows.append(border_window)
        else:
            print("Error: No screens available")

    def hide(self) -> None:
        for border_window in self.border_windows:
            border_window.hide()
        self.is_visible = False

    def show(self) -> None:
        if not self.border_windows:
            self.create_border_windows()
        for border_window in self.border_windows:
            border_window.show()
        self.is_visible = True

    def destroy(self) -> None:
        """Permanently close and delete all border windows.

        Must be called on application exit. hide() alone leaves top-level
        widgets alive, which keeps the QApplication event loop running and
        can leave a red border on screen if quit is interrupted.
        """
        for border_window in self.border_windows:
            try:
                border_window.hide()
                border_window.close()
                border_window.deleteLater()
            except Exception:
                pass
        self.border_windows = []
        self.is_visible = False

    def isVisible(self) -> bool:
        return self.is_visible
