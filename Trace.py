"""Provides methods to trace nv2a commands."""

# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=too-many-function-args

from collections import defaultdict
import os
import struct
import time
import traceback

from AbortFlag import AbortFlag
import ExchangeU32
from HTMLLog import HTMLLog
import KickFIFO
from NV2ALog import NV2ALog
import Texture
from Xbox import Xbox
import XboxHelper


class MaxFlipExceeded(Exception):
    """Exception to indicate the maximum number of buffer flips has been reached."""


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


def _read_pgraph_rdi(xbox: Xbox, offset: int, count: int):
    # FIXME: Assert pusher access is disabled
    # FIXME: Assert PGRAPH idle

    NV10_PGRAPH_RDI_INDEX = 0xFD400750
    NV10_PGRAPH_RDI_DATA = 0xFD400754

    # TODO: Confirm behavior:
    # It may be that reading the DATA register 4 times returns X,Y,Z,W (not
    # necessarily in that order), but during that time the INDEX register will
    # stay constant, only being incremented on the final read.
    # It is not safe and likely incorrect to do a bulk read so this must be done
    # individualy despite the interface communication overhead.
    xbox.write_u32(NV10_PGRAPH_RDI_INDEX, offset)
    data = bytearray()
    for _ in range(count):
        word = xbox.read_u32(NV10_PGRAPH_RDI_DATA)
        data += struct.pack("<L", word)

    # FIXME: Restore original RDI?
    # Note: It may not be possible to restore the original index.
    # If you touch the INDEX register, you may or may not be resetting the
    # internal state machine.

    # FIXME: Assert the conditions from entry have not changed
    return data


class Tracer:
    """Performs tracing of the xbox nv2a state."""

    ALPHA_MODE_BOTH = 0
    ALPHA_MODE_KEEP = 1
    ALPHA_MODE_DROP = 2

    def __init__(
        self,
        dma_pull_addr: int,
        dma_push_addr: int,
        xbox: Xbox,
        xbox_helper: XboxHelper.XboxHelper,
        abort_flag: AbortFlag,
        output_dir="out",
        alpha_mode=ALPHA_MODE_DROP,
        enable_texture_dumping=True,
        enable_surface_dumping=True,
        enable_raw_pixel_dumping=True,
        enable_rdi=True,
        verbose=False,
        max_frames=0,
    ):
        self.xbox = xbox
        self.xbox_helper = xbox_helper
        self.abort_flag = abort_flag
        self.alpha_mode = alpha_mode
        self.output_dir = output_dir
        self.html_log = HTMLLog(os.path.join(output_dir, "debug.html"))
        self.nv2a_log = NV2ALog(os.path.join(output_dir, "nv2a_log.txt"))
        self.flip_stall_count = 0
        self.command_count = 0

        self.real_dma_pull_addr = dma_pull_addr
        self.real_dma_push_addr = dma_push_addr
        self.target_dma_push_addr = dma_pull_addr
        self.enable_texture_dumping = enable_texture_dumping
        self.enable_surface_dumping = enable_surface_dumping
        self.enable_raw_pixel_dumping = enable_raw_pixel_dumping
        self.enable_rdi = enable_rdi
        self.verbose = verbose
        self.max_frames = max_frames

        self.pgraph_dump = None

        # Maps {object : {method: ([pre_call_hooks], [post_call_hooks])} }
        self.method_callbacks = defaultdict(dict)
        self._hook_methods()

    def run(self):
        """Traces the push buffer until aborted."""
        bytes_queued = 0

        dma_pull_addr = self.real_dma_pull_addr

        while not self.abort_flag.should_abort:
            try:
                dma_pull_addr, unprocessed_bytes = self.process_push_buffer_command(
                    dma_pull_addr
                )
                bytes_queued += unprocessed_bytes

                # time.sleep(0.5)

                # Avoid queuing up too many bytes: while the buffer is being processed,
                # D3D might fixup the buffer if GET is still too far away.
                is_empty = dma_pull_addr == self.real_dma_push_addr
                if is_empty or bytes_queued >= 200:
                    print(
                        "Flushing buffer until (0x%08X): real_put 0x%X; bytes_queued: %d"
                        % (dma_pull_addr, self.real_dma_push_addr, bytes_queued)
                    )
                    self.run_fifo(dma_pull_addr)
                    bytes_queued = 0

                if is_empty:
                    print("Reached end of buffer with %d bytes queued?!" % bytes_queued)
                    self.xbox_helper.print_enable_states()
                    self.xbox_helper.print_pb_state()
                    self.xbox_helper.print_dma_state()
                    self.xbox_helper.print_cache_state()
                    print("========")
                    # break

                # Verify we are where we think we are
                if bytes_queued == 0:
                    dma_pull_addr_real = self.xbox_helper.get_dma_pull_address()
                    print(
                        "Verifying hw (0x%08X) is at parser (0x%08X)"
                        % (dma_pull_addr_real, dma_pull_addr)
                    )
                    try:
                        assert dma_pull_addr_real == dma_pull_addr
                    except:
                        self.xbox_helper.print_pb_state()
                        raise

            except MaxFlipExceeded:
                print("Max flip count reached")
                self.abort_flag.abort()
            except:  # pylint: disable=bare-except
                traceback.print_exc()
                self.abort_flag.abort()

    def hook_method(self, obj, method, pre_hooks, post_hooks):
        """Registers pre- and post-run hooks for the given method."""
        print("Registering method hook for 0x%X::0x%04X" % (obj, method))
        self.method_callbacks[obj][method] = pre_hooks, post_hooks

    @property
    def recorded_flip_stall_count(self):
        return self.flip_stall_count

    @property
    def recorded_command_count(self):
        return self.command_count

    def _exchange_dma_push_address(self, target):
        """Sets the DMA_PUSH_ADDR to the given target, storing the old value.

        self.real_dma_push_addr = Xbox.DMA_PUSH_ADDR
        self.target_dma_push_addr = target
        Xbox.DMA_PUSH_ADDR = target
        """
        prev_target = self.target_dma_push_addr
        prev_real = self.real_dma_push_addr

        real = ExchangeU32.exchange_u32(self.xbox, XboxHelper.DMA_PUSH_ADDR, target)
        self.target_dma_push_addr = target

        # It must point where we pointed previously, otherwise something is broken
        if real != prev_target:
            self.html_log.print_log(
                "New real PUT (0x%08X -> 0x%08X) while changing hook 0x%08X -> 0x%08X"
                % (prev_real, real, prev_target, target)
            )
            put_s1 = self.xbox.read_u32(XboxHelper.CACHE_PUSH_STATE)
            if put_s1 & 1:
                print("PUT was modified and pusher was already active!")
                time.sleep(60.0)
            self.real_dma_push_addr = real
            # traceback.print_stack()

    def _dbg_print(self, message):
        if not self.verbose:
            return
        print(message)

    def run_fifo(self, pull_addr_target):
        """Runs the PFIFO until the DMA_PULL_ADDR equals the given address."""

        # Mark the pushbuffer as empty by setting the push address to the target pull
        # address.
        self._exchange_dma_push_address(pull_addr_target)
        assert self.target_dma_push_addr == pull_addr_target

        # FIXME: we can avoid this read in some cases, as we should know where we are
        self.real_dma_pull_addr = self.xbox_helper.get_dma_pull_address()

        self.html_log.log(
            [
                "WARNING",
                "Running FIFO (GET: 0x%08X -- PUT: 0x%08X / 0x%08X)"
                % (self.real_dma_pull_addr, pull_addr_target, self.real_dma_push_addr),
            ]
        )

        # Loop while this command is being ran.
        # This is necessary because a whole command might not fit into CACHE.
        # So we have to process it chunk by chunk.
        # FIXME: This used to be a check which made sure that `dma_pull_addr` did
        #       never leave the known PB.
        iterations_with_no_change = 0
        while self.real_dma_pull_addr != pull_addr_target:
            if iterations_with_no_change and not iterations_with_no_change % 1000:
                print(
                    "Warning: %d iterations with no change to DMA_PULL_ADDR 0x%X "
                    " target 0x%X"
                    % (
                        iterations_with_no_change,
                        self.real_dma_pull_addr,
                        pull_addr_target,
                    )
                )

            self._dbg_print(
                "At 0x%08X, target is 0x%08X (Real: 0x%08X)"
                % (
                    self.real_dma_pull_addr,
                    pull_addr_target,
                    self.real_dma_push_addr,
                )
            )

            self._dbg_print(
                "> PULL ADDR: 0x%X  PUSH: 0x%X"
                % (
                    self.xbox_helper.get_dma_pull_address(),
                    self.xbox_helper.get_dma_push_address(),
                )
            )

            # Disable PGRAPH, so it can't run anything from CACHE.
            self.xbox_helper.disable_pgraph_fifo()
            self.xbox_helper.wait_until_pgraph_idle()

            # This scope should be atomic.
            # FIXME: Avoid running bad code, if the PUT was modified sometime during
            # this command.
            self._exchange_dma_push_address(pull_addr_target)

            # FIXME: xemu does not seem to implement the CACHE behavior
            # This leads to an infinite loop as the kick fails to populate the cache.
            # Kick commands into CACHE.
            kicked = KickFIFO.kick(self.xbox, pull_addr_target)
            if not kicked:
                print("Warning: FIFO kick failed")

            if self.verbose:
                self.xbox_helper.print_cache_state()

            # Run the commands we have moved to CACHE, by enabling PGRAPH.
            self.xbox_helper.enable_pgraph_fifo()
            time.sleep(0.01)

            # Get the updated PB address.
            new_get_addr = self.xbox_helper.get_dma_pull_address()
            if new_get_addr == self.real_dma_pull_addr:
                iterations_with_no_change += 1
            else:
                self.real_dma_pull_addr = new_get_addr
                iterations_with_no_change = 0

        # This is just to confirm that nothing was modified in the final chunk
        self._exchange_dma_push_address(pull_addr_target)

    def _dump_texture(self, index):
        reg_offset = index * 4
        # Verify that the texture stage is enabled
        control = self.xbox.read_u32(XboxHelper.PGRAPH_TEXCTL0_0 + reg_offset)
        if not control & (1 << 30):
            return ""

        offset = self.xbox.read_u32(XboxHelper.PGRAPH_TEXOFFSET0 + reg_offset)
        # FIXME: Use pitch from registers for linear formats.
        # FIXME: clean up associated fallback code in Texture.py
        reg_pitch = self.xbox.read_u32(XboxHelper.PGRAPH_TEXCTL1_0 + reg_offset) >> 16
        pitch = 0
        fmt = self.xbox.read_u32(XboxHelper.PGRAPH_TEXFMT0 + reg_offset)

        fmt_color = (fmt >> 8) & 0x7F
        width_shift = (fmt >> 20) & 0xF
        height_shift = (fmt >> 24) & 0xF
        depth_shift = (fmt >> 28) & 0xF
        width = 1 << width_shift
        height = 1 << height_shift
        depth = 1 << depth_shift

        self._dbg_print(
            "Texture %d [0x%08X, %d x %d x %d (pitch register: 0x%X), format 0x%X]"
            % (index, offset, width, height, depth, reg_pitch, fmt_color)
        )

        def dump(img_tags, adjusted_offset, layer):
            if layer >= 0:
                layer_name = "_L%d" % layer
            else:
                layer_name = ""

            if self.alpha_mode != self.ALPHA_MODE_KEEP:
                no_alpha_path = "command%d--tex_%d%scolor.png" % (
                    self.command_count,
                    index,
                    layer_name,
                )
                img_tags += '<img height="128px" src="%s" alt="%s"/>' % (
                    no_alpha_path,
                    no_alpha_path,
                )
            else:
                no_alpha_path = None

            if self.alpha_mode != self.ALPHA_MODE_DROP:
                alpha_path = "command%d--tex_%d%scolor-a.png" % (
                    self.command_count,
                    index,
                    layer_name,
                )
                img_tags += '<img height="128px" src="%s" alt="%s"/>' % (
                    alpha_path,
                    alpha_path,
                )
            else:
                alpha_path = None

            img = Texture.dump_texture(
                self.xbox, adjusted_offset, pitch, fmt_color, width, height
            )

            self._save_image(img, no_alpha_path, alpha_path)

            return img_tags

        img_tags = ""
        if depth == 1:
            img_tags = dump(img_tags, offset, -1)
        else:
            adjusted_offset = offset
            for layer in range(depth):
                img_tags += dump(img_tags, adjusted_offset, layer)
                adjusted_offset += pitch * height

        return img_tags

    def dump_textures(self, _data, *_args):
        if not self.enable_texture_dumping:
            return []

        extra_html = []

        for i in range(4):
            tags = self._dump_texture(i)
            if tags:
                extra_html += [tags]

        return extra_html

    def dump_surfaces(self, _data, *_args):
        if not self.enable_surface_dumping:
            return []

        params = Texture.read_texture_parameters(self.xbox)

        if not params.format_color:
            print("Warning: Invalid color format, skipping surface dump.")
            return []

        if params.depth_offset:
            depth_buffer = self.xbox.read(
                Texture.AGP_MEMORY_BASE | params.depth_offset,
                params.depth_pitch * params.height,
            )

        # Dump stuff we might care about
        self._write("pgraph.bin", _dump_pgraph(self.xbox))
        self._write("pfb.bin", _dump_pfb(self.xbox))
        if params.color_offset and self.enable_raw_pixel_dumping:
            self._write(
                "mem-2.bin",
                self.xbox.read(
                    Texture.AGP_MEMORY_BASE | params.color_offset,
                    params.color_pitch * params.height,
                ),
            )
        if params.depth_offset and self.enable_raw_pixel_dumping:
            self._write(
                "mem-3.bin",
                depth_buffer,
            )
        if self.enable_rdi:
            self._write(
                "pgraph-rdi-vp-instructions.bin",
                _read_pgraph_rdi(self.xbox, 0x100000, 136 * 4),
            )
            self._write(
                "pgraph-rdi-vp-constants0.bin",
                _read_pgraph_rdi(self.xbox, 0x170000, 192 * 4),
            )
            self._write(
                "pgraph-rdi-vp-constants1.bin",
                _read_pgraph_rdi(self.xbox, 0xCC0000, 192 * 4),
            )

        # FIXME: Respect anti-aliasing
        img_tags = ""
        if self.alpha_mode != self.ALPHA_MODE_KEEP:
            no_alpha_path = "command%d--color.png" % (self.command_count)
            img_tags += '<img height="128px" src="%s" alt="%s"/>' % (
                no_alpha_path,
                no_alpha_path,
            )
        else:
            no_alpha_path = None

        if self.alpha_mode != self.ALPHA_MODE_DROP:
            alpha_path = "command%d--color-a.png" % (self.command_count)
            img_tags += '<img height="128px" src="%s" alt="%s"/>' % (
                alpha_path,
                alpha_path,
            )
        else:
            alpha_path = None

        extra_html = []

        extra_html += [img_tags]
        extra_html += [
            "%d x %d [pitch = %d (0x%X)], at 0x%08X, format 0x%X, type: 0x%X, swizzle: 0x%08X, 0x%08X [used %d]"
            % (
                params.width,
                params.height,
                params.color_pitch,
                params.color_pitch,
                params.color_offset,
                params.format_color,
                params.surface_type,
                params.swizzle_unk,
                params.swizzle_unk2,
                params.swizzled,
            )
        ]
        self._dbg_print(extra_html[-1])

        try:
            if not params.color_offset:
                raise Exception("Color offset is null")

            self._dbg_print(
                "Attempting to dump surface; swizzle: %s" % (str(params.swizzled))
            )
            img = Texture.dump_texture(
                self.xbox,
                params.color_offset,
                params.color_pitch,
                params.format_color,
                params.width,
                params.height,
            )
        except:  # pylint: disable=bare-except
            img = None
            print("Failed to dump color surface")
            traceback.print_exc()

        self._save_image(img, no_alpha_path, alpha_path)

        depth_path = "command%d--depth.png" % (self.command_count)
        stencil_path = "command%d--stencil.png" % (self.command_count)

        try:
            if not params.depth_offset:
                raise Exception("Depth offset is null")

            self._dbg_print("Attempting to dump zeta")
            depth, stencil = Texture.dump_zeta(
                depth_buffer,
                params.depth_offset,
                params.depth_pitch,
                params.format_depth,
                params.width,
                params.height,
            )
        except:
            depth = None
            stencil = None
            print("Failed to dump zeta surface")
            traceback.print_exc()

        self._save_image(depth, None, depth_path)
        self._save_image(stencil, None, stencil_path)

        zeta_img_tags = '<img height="128px" src="%s" alt="%s"/>' % (
            depth_path,
            depth_path,
        )

        if stencil is not None:
            zeta_img_tags += '<img height="128px" src="%s" alt="%s"/>' % (
                stencil_path,
                stencil_path,
            )

        extra_html += [zeta_img_tags]
        extra_html += [
            "zeta: [pitch = %d (0x%X)], at 0x%08X, format 0x%X]"
            % (
                params.depth_pitch,
                params.depth_pitch,
                params.depth_offset,
                params.format_depth,
            )
        ]

        return extra_html

    def _save_image(self, img, no_alpha_path, alpha_path):
        """Saves a PIL.Image to the given path(s)"""
        if not img:
            return

        if alpha_path:
            img.save(os.path.join(self.output_dir, alpha_path))
        if no_alpha_path:
            img = img.convert("RGB")
            img.save(os.path.join(self.output_dir, no_alpha_path))

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

    def _handle_begin(self, data, *args):

        # Avoid handling End
        if not data:
            return []

        print("BEGIN %d" % self.command_count)

        extra_html = []
        extra_html += self.dump_textures(data, *args)
        return extra_html

    def _handle_end(self, data, *args):

        # Avoid handling Begin
        if data != 0:
            return []

        extra_html = []
        extra_html += self.dump_surfaces(data, *args)
        return extra_html

    def _begin_pgraph_recording(self, _data, *_args):
        self.pgraph_dump = _dump_pgraph(self.xbox)
        self.html_log.log(["", "", "", "", "Dumped PGRAPH for later"])
        return []

    def _end_pgraph_recording(self, _data, *_args):
        # Debug feature to understand PGRAPH
        if self.pgraph_dump is not None:
            new_pgraph_dump = _dump_pgraph(self.xbox)

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

            self.pgraph_dump = None
            self.html_log.log(["", "", "", "", "Finished PGRAPH comparison"])

        return []

    def _handle_flip_stall(self, _data, *_args):
        print("Flip (Stall)")
        self.flip_stall_count += 1

        self.nv2a_log.log("Flip (stall) %d\n\n" % self.flip_stall_count)

        if self.max_frames and self.flip_stall_count >= self.max_frames:
            raise MaxFlipExceeded()
        return []

    def _filter_pgraph_method(self, nv_obj, method):
        # Do callback for pre-method
        return self.method_callbacks[nv_obj].get(method, ([], []))

    def _record_pgraph_method(self, method_info, data, pre_info, post_info):
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

    def _parse_push_buffer_command(self, pull_addr):
        # Retrieve command type from Xbox
        word = self.xbox.read_u32(0x80000000 | pull_addr)
        self.html_log.log(["", "", "", "@0x%08X: DATA: 0x%08X" % (pull_addr, word)])

        # FIXME: Get where this command ends
        next_parser_addr, info = XboxHelper.parse_command(pull_addr, word, self.verbose)

        # If we don't know where this command ends, we have to abort.
        if not next_parser_addr:
            raise Exception(
                "Failed to process command at 0x%X = 0x%X" % (pull_addr, word)
            )

        if info:
            method_info = {}
            method_info["address"] = pull_addr
            method_info["object"] = self.xbox_helper.fetch_graphics_class()
            method_info["method"] = info.method
            method_info["nonincreasing"] = info.non_increasing
            method_info["subchannel"] = info.subchannel
            method_info["method_count"] = info.method_count

            # Download this command from Xbox
            if not info.method_count:
                # Halo: CE has cases where method_count is 0?!
                self.html_log.print_log(
                    "Warning: Command 0x%X with method_count == 0\n" % info.method
                )
                data = []
            else:
                parameters = self.xbox.read(
                    0x80000000 | (pull_addr + 4), info.method_count * 4
                )
                data = struct.unpack("<%dL" % info.method_count, parameters)
                assert len(data) == info.method_count

            method_info["data"] = data
        else:
            method_info = None

        return method_info, next_parser_addr

    def _get_method_hooks(self, method_info):

        pre_callbacks = []
        post_callbacks = []

        nv_obj = method_info["object"]
        method = method_info["method"]
        for _data in method_info["data"]:
            pre_callbacks_this, post_callbacks_this = self._filter_pgraph_method(
                nv_obj, method
            )

            # Queue the callbacks
            pre_callbacks += pre_callbacks_this
            post_callbacks += post_callbacks_this

            if not method_info["nonincreasing"]:
                method += 4

        return pre_callbacks, post_callbacks

    def _record_push_buffer_command(self, method_info, pre_info, post_info):
        orig_method = method_info["method"]

        self.html_log.log(["%d" % self.command_count, "%s" % method_info])
        # Handle special case from Halo: CE where there are commands with no data.
        if not method_info["data"]:
            self._record_pgraph_method(method_info, None, pre_info, post_info)
        else:
            for data in method_info["data"]:
                self._record_pgraph_method(method_info, data, pre_info, post_info)
                if not method_info["nonincreasing"]:
                    method_info["method"] += 4

        method_info["method"] = orig_method
        self.command_count += 1

    def process_push_buffer_command(self, pull_addr):
        self.html_log.log(
            [
                "WARNING",
                "Starting FIFO parsing from 0x%08X -- 0x%08X"
                % (pull_addr, self.real_dma_push_addr),
            ]
        )

        if pull_addr == self.real_dma_push_addr:
            unprocessed_bytes = 0
        else:

            # Filter commands and check where it wants to go to
            method_info, post_addr = self._parse_push_buffer_command(pull_addr)

            # We have a problem if we can't tell where to go next
            assert post_addr

            # If we have a method, work with it
            if method_info is None:

                self.html_log.log(["WARNING", "No method. Going to 0x%08X" % post_addr])
                unprocessed_bytes = 4

            else:

                # Check what method this is
                pre_callbacks, post_callbacks = self._get_method_hooks(method_info)

                # Count number of bytes in instruction
                unprocessed_bytes = 4 * (1 + len(method_info["data"]))

                # Go where we can do pre-callback
                pre_info = []
                if len(pre_callbacks) > 0:

                    # Go where we want to go
                    self.run_fifo(pull_addr)

                    # Do the pre callbacks before running the command
                    # FIXME: assert we are where we wanted to be
                    for callback in pre_callbacks:
                        pre_info += callback(method_info["data"][0])

                # Go where we can do post-callback
                post_info = []
                if len(post_callbacks) > 0:

                    # If we reached target, we can't step again without leaving valid buffer
                    assert pull_addr != self.real_dma_push_addr

                    # Go where we want to go (equivalent to step)
                    self.run_fifo(post_addr)

                    # We have processed all bytes now
                    unprocessed_bytes = 0

                    # Do all post callbacks
                    for callback in post_callbacks:
                        post_info += callback(method_info["data"][0])

                # Add the pushbuffer command to log
                self._record_push_buffer_command(method_info, pre_info, post_info)

            # Move parser to the next instruction
            pull_addr = post_addr

        self.html_log.log(
            [
                "WARNING",
                "Sucessfully finished FIFO parsing 0x%08X -- 0x%08X (%d bytes unprocessed)"
                % (pull_addr, self.real_dma_push_addr, unprocessed_bytes),
            ]
        )

        return pull_addr, unprocessed_bytes

    def _write(self, suffix, contents):
        """Writes a raw byte dump."""
        out_path = (
            os.path.join(self.output_dir, "command%d_" % self.command_count) + suffix
        )
        with open(out_path, "wb") as dumpfile:
            dumpfile.write(contents)
