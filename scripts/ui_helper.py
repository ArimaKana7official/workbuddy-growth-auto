# UI automation helper for WorkBuddy client (screenshot + mouse/keyboard)
# All coordinates are physical pixels. DPI aware is declared at import.
import ctypes
import sys
import time

ctypes.windll.user32.SetProcessDPIAware()

import win32con
import win32gui
from PIL import ImageGrab


def find_workbuddy_window():
    """Return the main WorkBuddy client window handle."""
    candidates = []

    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return
        title = win32gui.GetWindowText(h)
        cls = win32gui.GetClassName(h)
        if title in ("腾讯WorkBuddy", "WorkBuddy") and cls.startswith("Chrome_WidgetWin"):
            candidates.append((h, title, cls))

    win32gui.EnumWindows(cb, None)
    if not candidates:
        return None
    # Prefer the larger window
    best = max(candidates, key=lambda c: _area(c[0]))
    return best[0]


def _area(h):
    l, t, r, b = win32gui.GetWindowRect(h)
    return max(0, r - l) * max(0, b - t)


def focus(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        # fallback: minimize/maximize trick
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    time.sleep(0.6)


def rect(hwnd):
    return win32gui.GetWindowRect(hwnd)


def shot(path, hwnd=None):
    if hwnd:
        box = win32gui.GetWindowRect(hwnd)
        img = ImageGrab.grab(bbox=box, all_screens=True)
    else:
        img = ImageGrab.grab(all_screens=True)
    img.save(path)
    print("SHOT:", path)


def click(x, y):
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)


def scroll(x, y, delta):
    """delta negative = scroll down"""
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(delta), 0)
    time.sleep(0.3)


def scroll_bottom(x, y, steps=30):
    for _ in range(steps):
        scroll(x, y, -600)
        time.sleep(0.12)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "focus":
        h = find_workbuddy_window()
        print("HWND:", h)
        focus(h)
        print("RECT:", rect(h))
        shot(sys.argv[2], h)
    elif cmd == "shot":
        h = find_workbuddy_window()
        shot(sys.argv[2], h)
    elif cmd == "click":
        click(int(sys.argv[2]), int(sys.argv[3]))
        time.sleep(1.0)
        h = find_workbuddy_window()
        shot(sys.argv[4], h)
    elif cmd == "scroll":
        scroll(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        time.sleep(0.5)
        h = find_workbuddy_window()
        shot(sys.argv[5], h)
    elif cmd == "scrollbottom":
        scroll_bottom(int(sys.argv[2]), int(sys.argv[3]))
        time.sleep(0.5)
        h = find_workbuddy_window()
        shot(sys.argv[4], h)
