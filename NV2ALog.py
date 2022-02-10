"""Manages the nv2a log file."""

# pylint: disable=invalid-name
# pylint: disable=consider-using-f-string

Nv2aLogMethodDetails = False


class NV2ALog:
    """Manages the nv2a log file."""

    def __init__(self, path):
        self.path = path

        with open(self.path, "w", encoding="utf8") as logfile:
            logfile.write("xemu style NV2A log from nv2a-trace.py")

    def log(self, message):
        """Append the given string to the nv2a log."""
        with open(self.path, "a", encoding="utf8") as logfile:
            logfile.write(message)

    def log_method(self, method_info, data, pre_info, post_info):
        """Append a line describing the given pgraph call to the nv2a log."""
        with open(self.path, "a", encoding="utf8") as logfile:
            if data is not None:
                data_str = "0x%X" % data
            else:
                data_str = "<NO_DATA>"

            logfile.write(
                "nv2a: pgraph method (%d): 0x%x -> 0x%x (%s)\n"
                % (
                    method_info["subchannel"],
                    method_info["object"],
                    method_info["method"],
                    data_str,
                )
            )

            if Nv2aLogMethodDetails:
                logfile.write("Method info:\n")
                logfile.write("Address: 0x%X\n" % method_info["address"])
                logfile.write("Method: 0x%X\n" % method_info["method"])
                logfile.write("Nonincreasing: %d\n" % method_info["nonincreasing"])
                logfile.write("Subchannel: 0x%X\n" % method_info["subchannel"])
                logfile.write("data:\n")
                logfile.write(str(data))
                logfile.write("\n\n")
                logfile.write("pre_info: %s\n" % pre_info)
                logfile.write("post_info: %s\n" % post_info)
