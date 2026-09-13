"""Native Shell_NotifyIcon tray icon supporting wide text icons.

QSystemTrayIcon always scales icons to a square, which mangles wide
clock-style text icons. This module talks to the Windows notification
area directly so the tray button can show the live timer like the
system clock does, while still exposing a small Qt-friendly API.
"""

import ctypes
from ctypes import wintypes

from PyQt6.QtGui import QImage, QPixmap

user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# 64-bit safe return types (default c_int would truncate handles/HWNDs)
kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
user32.RegisterClassExW.restype = ctypes.c_ushort
user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_void_p, wintypes.HINSTANCE, ctypes.c_void_p,
]
user32.DefWindowProcW.restype = ctypes.c_long  # LRESULT
user32.DefWindowProcW.argtypes = [
    wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM
]
user32.CreateIconIndirect.restype = ctypes.c_void_p
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = [ctypes.c_void_p]
user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.PostMessageW.argtypes = [
    ctypes.c_void_p, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM
]
user32.DestroyWindow.argtypes = [ctypes.c_void_p]
user32.DestroyIcon.argtypes = [ctypes.c_void_p]
gdi32.CreateDIBSection.restype = ctypes.c_void_p
gdi32.CreateBitmap.restype = ctypes.c_void_p
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL

WM_TRAY = 0x8000 + 7
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_DESTROY = 0x0002

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIF_SHOWTIP = 0x00000020

SM_CXSMICON = 49
SM_CYSMICON = 50

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM
)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("hWnd", wintypes.HWND),
        ("uID", ctypes.c_uint),
        ("uFlags", ctypes.c_uint),
        ("uCallbackMessage", ctypes.c_uint),
        ("hIcon", wintypes.HICON),
        ("szTip", ctypes.c_wchar * 64),
        ("dwState", ctypes.c_uint),
        ("dwStateMask", ctypes.c_uint),
        ("szInfo", ctypes.c_wchar * 256),
        ("uTimeout", ctypes.c_uint),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.c_uint),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", wintypes.HICON),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", ctypes.c_ushort),
        ("biBitCount", ctypes.c_ushort),
        ("biCompression", ctypes.c_uint),
        ("biSizeImage", ctypes.c_uint),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", ctypes.c_uint),
        ("biClrImportant", ctypes.c_uint),
    ]


gdi32.CreateDIBSection.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(BITMAPINFOHEADER),
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p,
    ctypes.c_uint,
]
shell32.Shell_NotifyIconW.argtypes = [ctypes.c_uint, ctypes.POINTER(NOTIFYICONDATAW)]


def _make_hicon(pixmap: QPixmap):
    """Convert an ARGB pixmap into an HICON preserving alpha and size."""
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    w, h = image.width(), image.height()

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    hdc = user32.GetDC(0)
    bits = ctypes.c_void_p()
    hbm_color = gdi32.CreateDIBSection(
        hdc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0
    )
    user32.ReleaseDC(0, hdc)
    if not hbm_color:
        raise OSError("CreateDIBSection failed")

    void_ptr = image.constBits()
    void_ptr.setsize(image.sizeInBytes())
    pixel_bytes = bytes(void_ptr)
    ctypes.memmove(bits.value, pixel_bytes, min(w * h * 4, len(pixel_bytes)))

    mask_bits = ctypes.create_string_buffer(((w + 7) // 8) * h)
    hbm_mask = gdi32.CreateBitmap(w, h, 1, 1, mask_bits)

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", wintypes.BOOL),
            ("xHotspot", wintypes.DWORD),
            ("yHotspot", wintypes.DWORD),
            ("hbmMask", ctypes.c_void_p),
            ("hbmColor", ctypes.c_void_p),
        ]

    ii = ICONINFO(True, 0, 0, hbm_mask, hbm_color)
    hicon = user32.CreateIconIndirect(ctypes.byref(ii))
    gdi32.DeleteObject(hbm_mask)
    gdi32.DeleteObject(hbm_color)
    if not hicon:
        raise OSError("CreateIconIndirect failed")
    return hicon


class ShellTray:
    """Tray icon with wide text rendering via Shell_NotifyIconW."""

    CLASS_NAME = "DevOTimeShellTrayWnd"

    def __init__(self, base_pixmap: QPixmap, on_double_click, on_context) -> None:
        self._on_double_click = on_double_click
        self._on_context = on_context
        self._hicon: int = 0
        self._hwnd = None
        self._create_window()
        self._add_icon(base_pixmap)

    # -- window + registration -------------------------------------------------
    def _create_window(self) -> None:
        self._wndproc = WNDPROC(self._window_proc)
        hinst = kernel32.GetModuleHandleW(None)

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinst
        wc.lpszClassName = self.CLASS_NAME
        if not user32.RegisterClassExW(ctypes.byref(wc)):
            err = ctypes.get_last_error()
            if err != 1410:  # ERROR_CLASS_ALREADY_USED
                raise ctypes.WinError(err)
        self._class_registered = True

        hwnd = user32.CreateWindowExW(
            0,
            self.CLASS_NAME,
            "DevOTime",
            0,
            0,
            0,
            0,
            0,
            wintypes.HWND(-3),  # HWND_MESSAGE
            None,
            hinst,
            None,
        )
        if not hwnd:
            raise ctypes.WinError()
        self._hwnd = hwnd

    def _window_proc(self, hwnd, msg, wparam, lparam) -> int:
        if msg == WM_TRAY:
            if lparam == WM_LBUTTONDBLCLK:
                try:
                    self._on_double_click()
                except Exception:
                    pass
            elif lparam == WM_RBUTTONUP:
                try:
                    user32.SetForegroundWindow(hwnd)
                    self._on_context()
                    user32.PostMessageW(hwnd, 0x0000, 0, 0)  # WM_NULL
                except Exception:
                    pass
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    # -- tray operations ---------------------------------------------------------
    def _base_nid(self, flags: int) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = flags
        return nid

    def _add_icon(self, pixmap: QPixmap) -> None:
        self._hicon = _make_hicon(pixmap)
        nid = self._base_nid(NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_SHOWTIP)
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = self._hicon
        nid.szTip = "DevOTime"
        if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            raise OSError("Shell_NotifyIcon NIM_ADD failed")
        nid.uVersion = 4
        shell32.Shell_NotifyIconW(0x00000004, ctypes.byref(nid))  # NIM_SETVERSION

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Replace the displayed icon with a freshly rendered pixmap."""
        new_hicon = _make_hicon(pixmap)
        nid = self._base_nid(NIF_ICON)
        nid.hIcon = new_hicon
        if shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid)):
            if self._hicon:
                user32.DestroyIcon(self._hicon)
            self._hicon = new_hicon
        else:
            user32.DestroyIcon(new_hicon)

    def set_tooltip(self, text: str) -> None:
        nid = self._base_nid(NIF_TIP)
        nid.szTip = text[:63]
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def show_balloon(self, title: str, message: str) -> None:
        nid = self._base_nid(NIF_INFO)
        nid.szInfo = message[:255]
        nid.szInfoTitle = title[:63]
        nid.dwInfoFlags = 1  # NIIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def destroy(self) -> None:
        try:
            nid = self._base_nid(0)
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            if self._hicon:
                user32.DestroyIcon(self._hicon)
                self._hicon = 0
            if getattr(self, "_hwnd", None):
                user32.DestroyWindow(self._hwnd)
                self._hwnd = None
        except Exception:
            pass
