"""Manages the exchange_u32.asm patch."""

# pylint: disable=consider-using-f-string
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

import struct
from Xbox import Xbox
import XboxHelper


class _ExchangeU32:
    """Manages the exchange_u32.asm patch."""

    def __init__(self, verbose=True):
        self.exchange_u32_addr = 0
        self.verbose = verbose

    def _install_kicker(self, xbox: Xbox):
        with open("exchange_u32", "rb") as patch_file:
            data = patch_file.read()

        self.exchange_u32_addr = XboxHelper.load_binary(xbox, data)
        if self.verbose:
            print("exchange_u32 installed at 0x%08X" % self.exchange_u32_addr)

    def call(self, xbox: Xbox, address: int, value: int) -> int:
        """Calls the kicker with the given argument."""
        if not self.exchange_u32_addr:
            self._install_kicker(xbox)

        return xbox.call(self.exchange_u32_addr, struct.pack("<LL", value, address))[
            "eax"
        ]


_instance = _ExchangeU32()


def exchange_u32(xbox: Xbox, address: int, value: int) -> int:
    """Exchanges `value` with the value at `address`, returning the original value."""
    return _instance.call(xbox, address, value)
