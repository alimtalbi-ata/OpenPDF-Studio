"""Windows window probe: verify an actual visible top-level application window."""
import sys

def visible_windows(pid):
    if sys.platform != 'win32':
        raise RuntimeError('Native window enumeration requires Windows')
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    windows = []
    CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    @CALLBACK
    def visit(hwnd, unused):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if buf.value.strip(): windows.append({'hwnd': int(hwnd), 'title': buf.value})
        return True
    if not user32.EnumWindows(visit, 0):
        raise OSError('EnumWindows failed')
    return windows

def matching_window(pid, expected='OpenPDF Studio', enumerate_windows=None):
    finder = enumerate_windows or visible_windows
    return next((item for item in finder(pid) if expected.lower() in item['title'].lower()), None)


def window_rectangle(hwnd):
    """Return validated on-screen rectangle for a previously verified HWND (Windows only)."""
    if sys.platform != 'win32':
        raise RuntimeError('Windows required for window bounds')
    import ctypes
    from ctypes import wintypes
    class RECT(ctypes.Structure):
        _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]
    rect = RECT()
    if not ctypes.windll.user32.IsWindow(wintypes.HWND(hwnd)):
        return None
    if not ctypes.windll.user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        return None
    if rect.right <= rect.left or rect.bottom <= rect.top:
        return None
    return (rect.left, rect.top, rect.right, rect.bottom)
