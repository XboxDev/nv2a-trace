"""Provides a trivial wrapper around xboxpy functionality."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import xboxpy


class Xbox:
    """Trivial wrapper around xboxpy"""

    def __init__(self):
        self.read_u32 = xboxpy.read_u32
        self.write_u32 = xboxpy.write_u32
        self.read = xboxpy.read
        self.write = xboxpy.write
        self.call = xboxpy.api.call
        self.ke = xboxpy.ke
