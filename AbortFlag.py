"""Provides a simple pass-by-reference wrapped flag."""

# pylint: disable=invalid-name


class AbortFlag:
    """Indicates whether the trace should be aborted"""

    def __init__(self):
        self.abort_now = False

    def abort(self):
        """Sets the abort flag."""
        self.abort_now = True

    @property
    def should_abort(self):
        """Queries the abort flag."""
        return self.abort_now
