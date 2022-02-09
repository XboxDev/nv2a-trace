"""Manages the HTML log file."""

# pylint: disable=consider-using-f-string
# pylint: disable=invalid-name
# pylint: disable=line-too-long

import atexit


class HTMLLog:
    """Manages the HTML log file."""

    def __init__(self, path):
        self.path = path

        with open(path, "w", encoding="utf8") as logfile:
            logfile.write(
                "<html><head>"
                "<style>"
                "body { font-family: sans-serif; background:#333; color: #ccc } "
                "img { border: 1px solid #FFF; } "
                "td, tr, table { background: #444; padding: 10px; border:1px solid #888; border-collapse: collapse; }"
                "</style></head><body><table>\n"
            )

        self.log(["<b>#</b>", "<b>Opcode / Method</b>", "..."])
        atexit.register(self._close_tags)

    def _close_tags(self):
        with open(self.path, "a", encoding="utf8") as logfile:
            logfile.write("</table></body></html>")

    def log(self, values):
        """Append the given values to the HTML log."""
        with open(self.path, "a", encoding="utf8") as logfile:
            logfile.write("<tr>")
            for val in values:
                logfile.write("<td>%s</td>" % val)
            logfile.write("</tr>\n")

    def print_log(self, message):
        """Print the given string and append it to the HTML log."""
        print(message)
        self.log([message])
