"""
Global keyboard listener — captures keypresses system-wide.

Uses pynput which on macOS requires Accessibility permission
(System Settings → Privacy & Security → Accessibility).
"""

from pynput import keyboard


_MODIFIERS = {
    keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
    keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
    keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
    keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
}

_IGNORED_KEYS = {
    keyboard.Key.caps_lock, keyboard.Key.tab,
    keyboard.Key.f1, keyboard.Key.f2, keyboard.Key.f3, keyboard.Key.f4,
    keyboard.Key.f5, keyboard.Key.f6, keyboard.Key.f7, keyboard.Key.f8,
    keyboard.Key.f9, keyboard.Key.f10, keyboard.Key.f11, keyboard.Key.f12,
}


class KeyboardListener:
    """
    Listens for global keypresses and classifies them.

    Parameters
    ----------
    on_keypress : callable
        Called on valid keypress: `on_keypress(key_type: str)`.
        key_type can be: "char", "space", "enter", "backspace", "modifier"
    on_quit : callable
        Called when Esc is pressed.
    """

    def __init__(self, on_keypress, on_quit):
        self._on_keypress = on_keypress
        self._on_quit = on_quit
        self._listener = keyboard.Listener(on_press=self._handle)

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()

    def join(self):
        self._listener.join()

    def _handle(self, key):
        if key == keyboard.Key.esc:
            self._on_quit()
            return

        if key in _IGNORED_KEYS:
            return

        key_type = "char"
        if key == keyboard.Key.space:
            key_type = "space"
        elif key == keyboard.Key.enter:
            key_type = "enter"
        elif key == keyboard.Key.backspace:
            key_type = "backspace"
        elif key in _MODIFIERS:
            key_type = "modifier"

        self._on_keypress(key_type)
