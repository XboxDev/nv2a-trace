"""Python interface to the ntrc Dynamic DXT module."""

from typing import Tuple

from xboxpy.interface import if_xbdm


class NTRC:
    """Python interface to the ntrc Dynamic DXT module."""

    # Keep in sync with value in dxtmain.c
    _COMMAND_PREFIX = "ntrc!"

    def __init__(self):
        self._connected = False

    def connect(self) -> bool:
        """Verifies that the ntrc handler is available."""
        if self._connected:
            return True

        status, message = self._send("hello")
        if status == 200:
            self._connected = True
            return True

        print(f"Failed to communicate with ntrc module: {status} {message}")
        return False

    def _send(self, command_string) -> Tuple[int, str]:
        return if_xbdm.xbdm_command(self._COMMAND_PREFIX + command_string)
