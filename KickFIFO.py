"""Manages the kick_fifo.asm patch."""

# pylint: disable=consider-using-f-string
# pylint: disable=too-few-public-methods

import struct
from Xbox import Xbox
import XboxHelper


class _KickFIFO:
    """Manages the kick_fifo.asm patch."""

    # The kick worked and the pushbuffer is empty.
    STATE_OK = 0x1337C0DE

    # The kick worked, but the command timed out waiting for the pushbuffer to become
    # empty
    STATE_BUSY = 0x32555359

    # xbox.DMA_PUSH_ADDR != `expected_push`
    STATE_INVALID_READ_PUSH_ADDR = 0xBAD0000

    # xbox.DMA_PUSH_ADDR changed during the course of the kick
    STATE_INVALID_PUSH_MODIFIED_IN_CALL = 0xBADBAD

    def __init__(self, verbose=True):
        self.method_addr = None
        self.verbose = verbose

    def _install_kicker(self, xbox):
        if self.method_addr is not None:
            return

        with open("kick_fifo", "rb") as patch_file:
            data = patch_file.read()

        self.method_addr = XboxHelper.load_binary(xbox, data)
        if self.verbose:
            print("kick_fifo installed at 0x%08X" % self.method_addr)

    def call(self, xbox: Xbox, expected_push: int):
        """Calls the kicker with the given argument."""
        self._install_kicker(xbox)

        # Allow a handful of retries if the push buffer does not become empty during a
        # kick
        for _ in range(100):
            eax = xbox.call(self.method_addr, struct.pack("<L", expected_push))["eax"]
            if eax == self.STATE_INVALID_READ_PUSH_ADDR:
                real_push_addr = xbox.read_u32(XboxHelper.DMA_PUSH_ADDR)
                print(
                    "WARNING: real DMA_PUSH_ADDR 0x%X != expected address 0x%X. Aborting"
                    % (real_push_addr, expected_push)
                )
                return False
            if eax == self.STATE_INVALID_PUSH_MODIFIED_IN_CALL:
                raise Exception("DMA_PUSH_ADDR modified during kick_fifo call")
            if eax == self.STATE_OK:
                return True

        print("WARNING: timed out waiting for pushbuffer to become empty.")
        return False


_kicker = _KickFIFO()


def kick(xbox: Xbox, expected_put: int):
    """Calls the kicker with the given argument. Returns true if successful."""
    return _kicker.call(xbox, expected_put)
