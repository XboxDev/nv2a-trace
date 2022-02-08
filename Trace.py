"""Provides methods to trace nv2a commands."""

# FIXME: DONOTSUBMIT REMOVE BELOW
# pylint: disable=fixme

# pylint: disable=consider-using-f-string
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements

import atexit
import os
import struct
import time
import traceback

import KickFIFO
import Texture
import XboxHelper


class MaxFlipExceeded(Exception):
    """Exception to indicate the maximum number of buffer flips has been reached."""


# pylint: disable=invalid-name
OutputDir = "out"
PixelDumping = True
TextureDumping = True
SurfaceDumping = True
DebugPrint = False
MaxFrames = 0
# pylint: enable=invalid-name


# pylint: disable=invalid-name
exchange_u32_addr = None
# pylint: enable=invalid-name


def _exchange_u32(xbox, address, value):
    global exchange_u32_addr
    if exchange_u32_addr is None:
        with open("exchange_u32", "rb") as infile:
            data = infile.read()

        exchange_u32_addr = XboxHelper.load_binary(xbox, data)
        print("exchange_u32 installed at 0x%08X" % exchange_u32_addr)
    return xbox.call(exchange_u32_addr, struct.pack("<LL", value, address))["eax"]


def _dump_pgraph(xbox):
    """Returns the entire PGRAPH region."""
    buffer = bytearray([])
    buffer.extend(xbox.read(0xFD400000, 0x200))

    # 0xFD400200 hangs Xbox, I just skipped to 0x400.
    # Needs further testing which regions work.
    buffer.extend(bytes([0] * 0x200))

    buffer.extend(xbox.read(0xFD400400, 0x2000 - 0x400))

    # Return the PGRAPH dump
    assert len(buffer) == 0x2000
    return bytes(buffer)


def _dump_pfb(xbox):
    """Returns the entire PFB region."""
    buffer = bytearray([])
    buffer.extend(xbox.read(0xFD100000, 0x1000))

    # Return the PFB dump
    assert len(buffer) == 0x1000
    return bytes(buffer)


def _read_pgraph_rdi(xbox, offset, count):
    # FIXME: Assert pusher access is disabled
    # FIXME: Assert PGRAPH idle

    NV10_PGRAPH_RDI_INDEX = 0xFD400750
    NV10_PGRAPH_RDI_DATA = 0xFD400754

    xbox.write_u32(NV10_PGRAPH_RDI_INDEX, offset)
    data = bytearray()
    for _ in range(count):
        word = xbox.read_u32(NV10_PGRAPH_RDI_DATA)
        data += struct.pack("<L", word)

    # FIXME: Restore original RDI?
    # FIXME: Assert the conditions from entry have not changed
    return data


class HTMLLog:
    """Manages the HTML log file."""

    def __init__(self, path):
        self.path = path

        with open(path, "w", encoding="utf8") as logfile:
            # pylint: disable=line-too-long
            logfile.write(
                "<html><head>"
                "<style>"
                "body { font-family: sans-serif; background:#333; color: #ccc } "
                "img { border: 1px solid #FFF; } "
                "td, tr, table { background: #444; padding: 10px; border:1px solid #888; border-collapse: collapse; }"
                "</style></head><body><table>\n"
            )
            # pylint: enable=line-too-long

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
            logfile.write(
                "nv2a: pgraph method (%d): 0x97 -> 0x%x (0x%x)\n"
                % (method_info["subchannel"], method_info["method"], data)
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


class Tracer:
    """Performs tracing of the xbox nv2a state."""

    def __init__(self, dma_get_addr, dma_put_addr):
        self.html_log = HTMLLog(os.path.join(OutputDir, "debug.html"))
        self.nv2a_log = NV2ALog(os.path.join(OutputDir, "nv2a_log.txt"))
        self.flip_stall_count = 0
        self.command_count = 0

        self.real_dma_get_addr = dma_get_addr
        self.real_dma_put_addr = dma_put_addr
        self.target_dma_put_addr = dma_get_addr

        self.pgraph_dump = None

        self.method_callbacks = {}
        self._hook_methods()

    def hook_method(self, _obj, method, pre_hooks, post_hooks):
        """Registers pre- and post-run hooks for the given method."""
        # TODO: Respect object parameter.
        print("Registering method hook for 0x%04X" % method)
        self.method_callbacks[method] = pre_hooks, post_hooks

    @property
    def recorded_flip_stall_count(self):
        return self.flip_stall_count

    @property
    def recorded_command_count(self):
        return self.command_count

    def run_fifo(self, xbox, xbox_helper, put_target):
        # Queue the commands
        self._write_put(xbox, put_target)

        # FIXME: we can avoid this read in some cases, as we should know where we are
        self.real_dma_get_addr = xbox.read_u32(XboxHelper.DMA_GET_ADDR)

        self.html_log.log(
            [
                "WARNING",
                "Running FIFO (GET: 0x%08X -- PUT: 0x%08X / 0x%08X)"
                % (self.real_dma_get_addr, put_target, self.real_dma_put_addr),
            ]
        )

        # Loop while this command is being ran.
        # This is necessary because a whole command might not fit into CACHE.
        # So we have to process it chunk by chunk.
        # FIXME: This used to be a check which made sure that `v_dma_get_addr` did
        #       never leave the known PB.
        while self.real_dma_get_addr != put_target:
            if DebugPrint:
                print(
                    "At 0x%08X, target is 0x%08X (Real: 0x%08X)"
                    % (self.real_dma_get_addr, put_target, self.real_dma_put_addr)
                )

            # Disable PGRAPH, so it can't run anything from CACHE.
            xbox_helper.disable_pgraph_fifo()
            xbox_helper.wait_until_pgraph_idle()

            # This scope should be atomic.
            # Avoid running bad code, if the PUT was modified sometime during
            # this command.
            self._write_put(xbox, self.target_dma_put_addr)

            # Kick commands into CACHE.
            KickFIFO.kick(xbox, self.target_dma_put_addr)

            # print("PUT STATE 0x%08X" % xbox.read_u32(0xFD003220))

            # Run the commands we have moved to CACHE, by enabling PGRAPH.
            xbox_helper.enable_pgraph_fifo()

            # Get the updated PB address.
            self.real_dma_get_addr = xbox.read_u32(XboxHelper.DMA_GET_ADDR)

        # This is just to confirm that nothing was modified in the final chunk
        self._write_put(xbox, self.target_dma_put_addr)

    def dump_textures(self, xbox, data, *args):
        if not PixelDumping or not TextureDumping:
            return []

        extra_html = []

        for i in range(4):
            path = "command%d--tex_%d.png" % (self.command_count, i)

            offset = xbox.read_u32(0xFD401A24 + i * 4)  # NV_PGRAPH_TEXOFFSET0
            pitch = (
                0  # xbox.read_u32(0xFD4019DC + i * 4) # NV_PGRAPH_TEXCTL1_0_IMAGE_PITCH
            )
            fmt = xbox.read_u32(0xFD401A04 + i * 4)  # NV_PGRAPH_TEXFMT0
            fmt_color = (fmt >> 8) & 0x7F
            width_shift = (fmt >> 20) & 0xF
            height_shift = (fmt >> 24) & 0xF
            width = 1 << width_shift
            height = 1 << height_shift

            # FIXME: self.out("tex-%d.bin" % (i), xbox.read(0x80000000 | offset, pitch * height))

            print(
                "Texture %d [0x%08X, %d x %d (pitch: 0x%X), format 0x%X]"
                % (i, offset, width, height, pitch, fmt_color)
            )
            img = Texture.dump_texture(xbox, offset, pitch, fmt_color, width, height)

            if img:
                img.save(os.path.join(OutputDir, path))
            extra_html += ['<img height="128px" src="%s" alt="%s"/>' % (path, path)]

        return extra_html

    def dump_surfaces(self, xbox, data, *args):
        if not PixelDumping or not SurfaceDumping:
            return []

        color_pitch = xbox.read_u32(0xFD400858)
        depth_pitch = xbox.read_u32(0xFD40085C)

        color_offset = xbox.read_u32(0xFD400828)
        depth_offset = xbox.read_u32(0xFD40082C)

        color_base = xbox.read_u32(0xFD400840)
        depth_base = xbox.read_u32(0xFD400844)

        # FIXME: Is this correct? pbkit uses _base, but D3D seems to use _offset?
        color_offset += color_base
        depth_offset += depth_base

        surface_clip_x = xbox.read_u32(0xFD4019B4)
        surface_clip_y = xbox.read_u32(0xFD4019B8)

        draw_format = xbox.read_u32(0xFD400804)
        surface_type = xbox.read_u32(0xFD400710)
        swizzle_unk = xbox.read_u32(0xFD400818)

        swizzle_unk2 = xbox.read_u32(0xFD40086C)

        clip_x = (surface_clip_x >> 0) & 0xFFFF
        clip_y = (surface_clip_y >> 0) & 0xFFFF

        clip_w = (surface_clip_x >> 16) & 0xFFFF
        clip_h = (surface_clip_y >> 16) & 0xFFFF

        surface_anti_aliasing = (surface_type >> 4) & 3

        clip_x, clip_y = XboxHelper.apply_anti_aliasing_factor(
            surface_anti_aliasing, clip_x, clip_y
        )
        clip_w, clip_h = XboxHelper.apply_anti_aliasing_factor(
            surface_anti_aliasing, clip_w, clip_h
        )

        width = clip_x + clip_w
        height = clip_y + clip_h

        # FIXME: 128 x 128 [pitch = 256 (0x100)], at 0x01AA8000 [PGRAPH: 0x01AA8000?], format 0x5, type: 0x21000002, swizzle: 0x7070000 [used 0]

        # FIXME: This does not seem to be a good field for this
        # FIXME: Patched to give 50% of coolness
        swizzled = (surface_type & 3) == 2
        # FIXME: if surface_type is 0, we probably can't even draw..

        format_color = (draw_format >> 12) & 0xF
        # FIXME: Support 3D surfaces.
        format_depth = (draw_format >> 18) & 0x3

        fmt_color = Texture.surface_color_format_to_texture_format(
            format_color, swizzled
        )
        # fmt_depth = Texture.surface_zeta_format_to_texture_format(format_depth)

        # Dump stuff we might care about
        self._write("pgraph.bin", _dump_pgraph(xbox))
        self._write("pfb.bin", _dump_pfb(xbox))
        if color_offset != 0x00000000:
            self._write(
                "mem-2.bin",
                xbox.read(0x80000000 | color_offset, color_pitch * height),
            )
        if depth_offset != 0x00000000:
            self._write(
                "mem-3.bin",
                xbox.read(0x80000000 | depth_offset, depth_pitch * height),
            )
        self._write(
            "pgraph-rdi-vp-instructions.bin",
            _read_pgraph_rdi(xbox, 0x100000, 136 * 4),
        )
        self._write(
            "pgraph-rdi-vp-constants0.bin",
            _read_pgraph_rdi(xbox, 0x170000, 192 * 4),
        )
        self._write(
            "pgraph-rdi-vp-constants1.bin",
            _read_pgraph_rdi(xbox, 0xCC0000, 192 * 4),
        )

        # FIXME: Respect anti-aliasing

        path = "command%d--color.png" % (self.command_count)
        extra_html = []
        extra_html += ['<img height="128px" src="%s" alt="%s"/>' % (path, path)]
        extra_html += [
            "%d x %d [pitch = %d (0x%X)], at 0x%08X, format 0x%X, type: 0x%X, swizzle: 0x%08X, 0x%08X [used %d]"
            % (
                width,
                height,
                color_pitch,
                color_pitch,
                color_offset,
                format_color,
                surface_type,
                swizzle_unk,
                swizzle_unk2,
                swizzled,
            )
        ]
        print(extra_html[-1])

        try:
            if color_offset == 0x00000000:
                print("Color offset is null")
                raise Exception()

            print("Attempting to dump surface; swizzle: %s" % (str(swizzled)))
            img = Texture.dump_texture(
                xbox, color_offset, color_pitch, fmt_color, width, height
            )
        except:  # pylint: disable=bare-except
            img = None
            print("Failed to dump color surface")
            traceback.print_exc()

        if img:
            # FIXME: Make this configurable or save an alpha preserving variant.
            # Hack to remove alpha channel
            img = img.convert("RGB")

            img.save(os.path.join(OutputDir, path))

        return extra_html

    def _hook_methods(self):
        """Installs hooks for methods interpreted by this class."""
        NV097_CLEAR_SURFACE = 0x1D94
        self.hook_method(0x97, NV097_CLEAR_SURFACE, [], [self.dump_surfaces])

        NV097_SET_BEGIN_END = 0x17FC
        self.hook_method(
            0x97, NV097_SET_BEGIN_END, [self._handle_begin], [self._handle_end]
        )

        # Check for texture address changes
        # for i in range(4):
        #  methodHooks(0x1B00 + 64 * i, [],    [HandleSetTexture], i)

        # Add the list of commands which might trigger CPU actions
        NV097_FLIP_STALL = 0x0130
        self.hook_method(0x97, NV097_FLIP_STALL, [], [self._handle_flip_stall])

        NV097_BACK_END_WRITE_SEMAPHORE_RELEASE = 0x1D70
        self.hook_method(
            0x97, NV097_BACK_END_WRITE_SEMAPHORE_RELEASE, [], [self.dump_surfaces]
        )

    def _handle_begin(self, xbox, data, *args):

        # Avoid handling End
        if data == 0:
            return []

        print("BEGIN %d" % self.command_count)

        extra_html = []
        # extra_html += self.DumpSurfaces(xbox, data, *args)
        # extra_html += self.DumpTextures(xbox, data, *args)
        return extra_html

    def _handle_end(self, xbox, data, *args):

        # Avoid handling Begin
        if data != 0:
            return []

        extra_html = []
        extra_html += self.dump_surfaces(xbox, data, *args)
        return extra_html

    def _begin_pgraph_recording(self, xbox, data, *args):
        self.pgraph_dump = _dump_pgraph(xbox)
        self.html_log.log(["", "", "", "", "Dumped PGRAPH for later"])
        return []

    def _end_pgraph_recording(self, xbox, data, *args):
        # Debug feature to understand PGRAPH
        if self.pgraph_dump is not None:
            new_pgraph_dump = _dump_pgraph(xbox)

            # This blacklist was created from a CLEAR_COLOR, CLEAR
            blacklist = [
                0x0040000C,  # 0xF3DF0479 → 0xF3DE04F9
                0x0040002C,  # 0xF3DF37FF → 0xF3DE37FF
                0x0040010C,  # 0x03DF0000 → 0x020000F1
                0x0040012C,  # 0x13DF379F → 0x131A37FF
                0x00400704,  # 0x00001D9C → 0x00001D94
                0x00400708,  # 0x01DF0000 → 0x000000F1
                0x0040070C,  # 0x01DF0000 → 0x000000F1
                0x0040072C,  # 0x01DF2700 → 0x000027F1
                0x00400740,  # 0x01DF37DD → 0x01DF37FF
                0x00400744,  # 0x18111D9C → 0x18111D94
                0x00400748,  # 0x01DF0011 → 0x000000F1
                0x0040074C,  # 0x01DF0097 → 0x000000F7
                0x00400750,  # 0x00DF005C → 0x00DF0064
                0x00400760,  # 0x000000CC → 0x000000FF
                0x00400764,  # 0x08001D9C → 0x08001D94
                0x00400768,  # 0x01DF0000 → 0x000000F1
                0x0040076C,  # 0x01DF0000 → 0x000000F1
                0x00400788,  # 0x01DF110A → 0x000011FB
                0x004007A0,  # 0x00200100 → 0x00201D70
                0x004007A4,  # 0x00200100 → 0x00201D70
                0x004007A8,  # 0x00200100 → 0x00201D70
                0x004007AC,  # 0x00200100 → 0x00201D70
                0x004007B0,  # 0x00200100 → 0x00201D70
                0x004007B4,  # 0x00200100 → 0x00201D70
                0x004007B8,  # 0x00200100 → 0x00201D70
                0x004007BC,  # 0x00200100 → 0x00201D70
                0x004007C0,  # 0x00000000 → 0x000006C9
                0x004007C4,  # 0x00000000 → 0x000006C9
                0x004007C8,  # 0x00000000 → 0x000006C9
                0x004007CC,  # 0x00000000 → 0x000006C9
                0x004007D0,  # 0x00000000 → 0x000006C9
                0x004007D4,  # 0x00000000 → 0x000006C9
                0x004007D8,  # 0x00000000 → 0x000006C9
                0x004007DC,  # 0x00000000 → 0x000006C9
                0x004007E0,  # 0x00000000 → 0x000006C9
                0x004007E4,  # 0x00000000 → 0x000006C9
                0x004007E8,  # 0x00000000 → 0x000006C9
                0x004007EC,  # 0x00000000 → 0x000006C9
                0x004007F0,  # 0x00000000 → 0x000006C9
                0x004007F4,  # 0x00000000 → 0x000006C9
                0x004007F8,  # 0x00000000 → 0x000006C9
                0x004007FC,  # 0x00000000 → 0x000006C9
                0x00400D6C,  # 0x00000000 → 0xFF000000
                0x0040110C,  # 0x03DF0000 → 0x020000F1
                0x0040112C,  # 0x13DF379F → 0x131A37FF
                0x00401704,  # 0x00001D9C → 0x00001D94
                0x00401708,  # 0x01DF0000 → 0x000000F1
                0x0040170C,  # 0x01DF0000 → 0x000000F1
                0x0040172C,  # 0x01DF2700 → 0x000027F1
                0x00401740,  # 0x01DF37FD → 0x01DF37FF
                0x00401744,  # 0x18111D9C → 0x18111D94
                0x00401748,  # 0x01DF0011 → 0x000000F1
                0x0040174C,  # 0x01DF0097 → 0x000000F7
                0x00401750,  # 0x00DF0064 → 0x00DF006C
                0x00401760,  # 0x000000CC → 0x000000FF
                0x00401764,  # 0x08001D9C → 0x08001D94
                0x00401768,  # 0x01DF0000 → 0x000000F1
                0x0040176C,  # 0x01DF0000 → 0x000000F1
                0x00401788,  # 0x01DF110A → 0x000011FB
                0x004017A0,  # 0x00200100 → 0x00201D70
                0x004017A4,  # 0x00200100 → 0x00201D70
                0x004017A8,  # 0x00200100 → 0x00201D70
                0x004017AC,  # 0x00200100 → 0x00201D70
                0x004017B0,  # 0x00200100 → 0x00201D70
                0x004017B4,  # 0x00200100 → 0x00201D70
                0x004017B8,  # 0x00200100 → 0x00201D70
                0x004017BC,  # 0x00200100 → 0x00201D70
                0x004017C0,  # 0x00000000 → 0x000006C9
                0x004017C4,  # 0x00000000 → 0x000006C9
                0x004017C8,  # 0x00000000 → 0x000006C9
                0x004017CC,  # 0x00000000 → 0x000006C9
                0x004017D0,  # 0x00000000 → 0x000006C9
                0x004017D4,  # 0x00000000 → 0x000006C9
                0x004017D8,  # 0x00000000 → 0x000006C9
                0x004017DC,  # 0x00000000 → 0x000006C9
                0x004017E0,  # 0x00000000 → 0x000006C9
                0x004017E4,  # 0x00000000 → 0x000006C9
                0x004017E8,  # 0x00000000 → 0x000006C9
                0x004017EC,  # 0x00000000 → 0x000006C9
                0x004017F0,  # 0x00000000 → 0x000006C9
                0x004017F4,  # 0x00000000 → 0x000006C9
                0x004017F8,  # 0x00000000 → 0x000006C9
                0x004017FC,  # 0x00000000 → 0x000006C9
                # 0x0040186C, # 0x00000000 → 0xFF000000 # CLEAR COLOR
                0x0040196C,  # 0x00000000 → 0xFF000000
                0x00401C6C,  # 0x00000000 → 0xFF000000
                0x00401D6C,  # 0x00000000 → 0xFF000000
            ]

            for i in range(len(self.pgraph_dump) // 4):
                off = 0x00400000 + i * 4
                if off in blacklist:
                    continue
                word = struct.unpack_from("<L", self.pgraph_dump, i * 4)[0]
                new_word = struct.unpack_from("<L", new_pgraph_dump, i * 4)[0]
                if new_word != word:
                    self.html_log.log(
                        [
                            "",
                            "",
                            "",
                            "",
                            "Modified 0x%08X in PGRAPH: 0x%08X &rarr; 0x%08X"
                            % (off, word, new_word),
                        ]
                    )

            pgraph_dump = None
            self.html_log.log(["", "", "", "", "Finished PGRAPH comparison"])

        return []

    def _handle_flip_stall(self, xbox, data, *args):
        print("Flip (Stall)")
        self.flip_stall_count += 1

        self.nv2a_log.log("Flip (stall) %d\n\n" % self.flip_stall_count)

        if MaxFrames and self.flip_stall_count >= MaxFrames:
            raise MaxFlipExceeded()
        return []

    def _filter_pgraph_method(self, xbox, method):
        # Do callback for pre-method
        if method in self.method_callbacks:
            return self.method_callbacks[method]
        return [], []

    def _record_pgraph_method(self, xbox, method_info, data, pre_info, post_info):
        if data is not None:
            dataf = struct.unpack("<f", struct.pack("<L", data))[0]
            self.nv2a_log.log_method(method_info, data, pre_info, post_info)
            self.html_log.log(
                [
                    "",
                    "0x%08X" % method_info["address"],
                    "0x%04X" % method_info["method"],
                    "0x%08X / %f" % (data, dataf),
                ]
                + pre_info
                + post_info
            )
        else:
            self.nv2a_log.log_method(method_info, None, pre_info, post_info)
            self.html_log.log(
                [
                    "",
                    "0x%08X" % method_info["address"],
                    "0x%04X" % method_info["method"],
                    "<No data>",
                ]
                + pre_info
                + post_info
            )

    def _write_put(self, xbox, target):

        prev_target = self.target_dma_put_addr
        prev_real = self.real_dma_put_addr

        real = _exchange_u32(xbox, XboxHelper.DMA_PUT_ADDR, target)
        self.target_dma_put_addr = target

        # It must point where we pointed previously, otherwise something is broken
        if real != prev_target:
            self.html_log.print_log(
                "New real PUT (0x%08X -> 0x%08X) while changing hook 0x%08X -> 0x%08X"
                % (prev_real, real, prev_target, target)
            )
            s1 = xbox.read_u32(XboxHelper.PUT_STATE)
            if s1 & 1:
                print("PUT was modified and pusher was already active!")
                time.sleep(60.0)
            self.real_dma_put_addr = real
            # traceback.print_stack()

    def _parse_push_buffer_command(self, xbox, get_addr):
        global DebugPrint

        # Retrieve command type from Xbox
        word = xbox.read_u32(0x80000000 | get_addr)
        self.html_log.log(["", "", "", "@0x%08X: DATA: 0x%08X" % (get_addr, word)])

        # FIXME: Get where this command ends
        next_parser_addr = XboxHelper.parse_command(get_addr, word, DebugPrint)

        # If we don't know where this command ends, we have to abort.
        if next_parser_addr == 0:
            return None, 0

        # Check which method it is.
        if ((word & 0xE0030003) == 0) or ((word & 0xE0030003) == 0x40000000):
            # methods
            method = word & 0x1FFF
            subchannel = (word >> 13) & 7
            method_count = (word >> 18) & 0x7FF
            method_nonincreasing = word & 0x40000000

            method_info = {}
            method_info["address"] = get_addr
            method_info["method"] = method
            method_info["nonincreasing"] = method_nonincreasing
            method_info["subchannel"] = subchannel

            # Download this command from Xbox
            if method_count == 0:
                # Halo: CE has cases where method_count is 0?!
                self.html_log.print_log(
                    "Warning: Command 0x%X with method_count == 0\n" % method
                )
                data = []
            else:
                command = xbox.read(0x80000000 | (get_addr + 4), method_count * 4)

                # FIXME: Unpack all of them?
                data = struct.unpack("<%dL" % method_count, command)
                assert len(data) == method_count
            method_info["data"] = data
        else:
            method_info = None

        return method_info, next_parser_addr

    def _get_method_hooks(self, xbox, method_info):

        pre_callbacks = []
        post_callbacks = []

        method = method_info["method"]
        for data in method_info["data"]:
            pre_callbacks_this, post_callbacks_this = self._filter_pgraph_method(
                xbox, method
            )

            # Queue the callbacks
            pre_callbacks += pre_callbacks_this
            post_callbacks += post_callbacks_this

            if not method_info["nonincreasing"]:
                method += 4

        return pre_callbacks, post_callbacks

    def _record_push_buffer_command(
        self, xbox, address, method_info, pre_info, post_info
    ):
        orig_method = method_info["method"]

        self.html_log.log(["%d" % self.command_count, "%s" % method_info])
        # Handle special case from Halo: CE where there are commands with no data.
        if not method_info["data"]:
            self._record_pgraph_method(xbox, method_info, None, pre_info, post_info)
        else:
            for data in method_info["data"]:
                self._record_pgraph_method(xbox, method_info, data, pre_info, post_info)
                if not method_info["nonincreasing"]:
                    method_info["method"] += 4

        method_info["method"] = orig_method
        self.command_count += 1

    def process_push_buffer_command(self, xbox, xbox_helper, parser_addr):
        self.html_log.log(
            [
                "WARNING",
                "Starting FIFO parsing from 0x%08X -- 0x%08X"
                % (parser_addr, self.real_dma_put_addr),
            ]
        )

        if parser_addr == self.real_dma_put_addr:
            unprocessed_bytes = 0
        else:

            # Filter commands and check where it wants to go to
            method_info, post_addr = self._parse_push_buffer_command(xbox, parser_addr)

            # We have a problem if we can't tell where to go next
            assert post_addr != 0

            # If we have a method, work with it
            if method_info is None:

                self.html_log.log(["WARNING", "No method. Going to 0x%08X" % post_addr])
                unprocessed_bytes = 4

            else:

                # Check what method this is
                pre_callbacks, post_callbacks = self._get_method_hooks(
                    xbox, method_info
                )

                # Count number of bytes in instruction
                unprocessed_bytes = 4 * (1 + len(method_info["data"]))

                # Go where we can do pre-callback
                pre_info = []
                if len(pre_callbacks) > 0:

                    # Go where we want to go
                    self.run_fifo(xbox, xbox_helper, parser_addr)

                    # Do the pre callbacks before running the command
                    # FIXME: assert we are where we wanted to be
                    for callback in pre_callbacks:
                        pre_info += callback(xbox, method_info["data"][0])

                # Go where we can do post-callback
                post_info = []
                if len(post_callbacks) > 0:

                    # If we reached target, we can't step again without leaving valid buffer
                    assert parser_addr != self.real_dma_put_addr

                    # Go where we want to go (equivalent to step)
                    self.run_fifo(xbox, xbox_helper, post_addr)

                    # We have processed all bytes now
                    unprocessed_bytes = 0

                    # Do all post callbacks
                    for callback in post_callbacks:
                        post_info += callback(xbox, method_info["data"][0])

                # Add the pushbuffer command to log
                self._record_push_buffer_command(
                    xbox, parser_addr, method_info, pre_info, post_info
                )

            # Move parser to the next instruction
            parser_addr = post_addr

        self.html_log.log(
            [
                "WARNING",
                "Sucessfully finished FIFO parsing 0x%08X -- 0x%08X (%d bytes unprocessed)"
                % (parser_addr, self.real_dma_put_addr, unprocessed_bytes),
            ]
        )

        return parser_addr, unprocessed_bytes

    def _write(self, suffix, contents):
        out_path = os.path.join(OutputDir, "command%d_" % self.command_count) + suffix
        with open(out_path, "wb") as dumpfile:
            dumpfile.write(contents)
