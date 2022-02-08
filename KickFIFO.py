"""Manages the kick_fifo.asm patch."""

# pylint: disable=consider-using-f-string
# pylint: disable=too-few-public-methods

import struct
import XboxHelper


class _KickFIFO:
    """Manages the kick_fifo.asm patch."""

    def __init__(self, verbose=True):
        self.kick_fifo_addr = None
        self.verbose = verbose

    def _install_kicker(self, xbox):
        if self.kick_fifo_addr is not None:
            return

        with open("kick_fifo", "rb") as patch_file:
            data = patch_file.read()

        self.kick_fifo_addr = XboxHelper.load_binary(xbox, data)
        if self.verbose:
            print("kick_fifo installed at 0x%08X" % self.kick_fifo_addr)

    def call(self, xbox, expected_put):
        """Calls the kicker with the given argument."""
        self._install_kicker(xbox)
        eax = xbox.call(self.kick_fifo_addr, struct.pack("<L", expected_put))["eax"]
        assert eax != 0xBADBAD


_kicker = _KickFIFO()


def kick(xbox, expected_put):
    """Calls the kicker with the given argument."""
    _kicker.call(xbox, expected_put)
