#!/usr/bin/env python3

"""Tool to capture nv2a activity from an xbox."""

# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-f-string
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals

import argparse
import os
import signal
import sys
import time
import traceback

import xboxpy
import XboxHelper
import Trace

# pylint: disable=invalid-name
abort_now = False
_enable_experimental_disable_z_compression_and_tiling = True
# pylint: enable=invalid-name


def signal_handler(_signal, _frame):
    global abort_now
    if not abort_now:
        print("Got first SIGINT! Aborting..")
        abort_now = True
    else:
        print("Got second SIGINT! Forcing exit")
        sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class Xbox:
    """Trivial wrapper around xboxpy"""

    def __init__(self):
        self.read_u32 = xboxpy.read_u32
        self.write_u32 = xboxpy.write_u32
        self.read = xboxpy.read
        self.write = xboxpy.write
        self.call = xboxpy.api.call
        self.ke = xboxpy.ke


def _wait_for_stable_push_buffer_state(xbox, xbox_helper):
    """Blocks until the push buffer reaches a stable state."""

    v_dma_get_addr = 0
    v_dma_put_addr_real = 0

    while not abort_now:
        # Stop consuming CACHE entries.
        xbox_helper.disable_pgraph_fifo()
        xbox_helper.wait_until_pgraph_idle()

        # Kick the pusher, so that it fills the CACHE.
        xbox_helper.allow_populate_fifo_cache()

        # Now drain the CACHE.
        xbox_helper.enable_pgraph_fifo()

        # Check out where the PB currently is and where it was supposed to go.
        v_dma_put_addr_real = xbox.read_u32(XboxHelper.DMA_PUSH_ADDR)
        v_dma_get_addr = xbox.read_u32(XboxHelper.DMA_PULL_ADDR)

        # Check if we have any methods left to run and skip those.
        v_dma_state = xbox.read_u32(XboxHelper.DMA_STATE)
        v_dma_method_count = (v_dma_state >> 18) & 0x7FF
        v_dma_get_addr += v_dma_method_count * 4

        # Hide all commands from the PB by setting PUT = GET.
        v_dma_put_addr_target = v_dma_get_addr
        xbox.write_u32(XboxHelper.DMA_PUSH_ADDR, v_dma_put_addr_target)

        # Resume pusher - The PB can't run yet, as it has no commands to process.
        xbox_helper.resume_fifo_pusher()

        # We might get issues where the pusher missed our PUT (miscalculated).
        # This can happen as `v_dma_method_count` is not the most accurate.
        # Probably because the DMA is halfway through a transfer.
        # So we pause the pusher again to validate our state
        xbox_helper.pause_fifo_pusher()

        time.sleep(1.0)

        v_dma_put_addr_target_check = xbox.read_u32(XboxHelper.DMA_PUSH_ADDR)
        v_dma_get_addr_check = xbox.read_u32(XboxHelper.DMA_PULL_ADDR)

        # We want the PB to be paused
        if v_dma_get_addr_check != v_dma_put_addr_target_check:
            print(
                "Oops GET (0x%08X) did not reach PUT (0x%08X)!"
                % (v_dma_get_addr_check, v_dma_put_addr_target_check)
            )
            continue

        # Ensure that we are at the correct offset
        if v_dma_put_addr_target_check != v_dma_put_addr_target:
            print(
                "Oops PUT was modified; got 0x%08X but expected 0x%08X!"
                % (v_dma_put_addr_target_check, v_dma_put_addr_target)
            )
            continue

        break

    return v_dma_get_addr, v_dma_put_addr_real


def _run(xbox, xbox_helper, v_dma_get_addr, trace):
    """Traces the push buffer until aborted."""
    global abort_now
    bytes_queued = 0

    while not abort_now:
        try:
            v_dma_get_addr, unprocessed_bytes = trace.process_push_buffer_command(
                v_dma_get_addr
            )
            bytes_queued += unprocessed_bytes

            # time.sleep(0.5)

            # Avoid queuing up too many bytes: while the buffer is being processed,
            # D3D might fixup the buffer if GET is still too far away.
            if v_dma_get_addr == trace.real_dma_put_addr or bytes_queued >= 200:
                print(
                    "Flushing buffer until (0x%08X): real_put 0x%X; bytes_queued: %d"
                    % (v_dma_get_addr, trace.real_dma_put_addr, bytes_queued)
                )
                trace.run_fifo(v_dma_get_addr)
                bytes_queued = 0

            if v_dma_get_addr == trace.real_dma_put_addr:
                print("Reached end of buffer with %d bytes queued?!" % bytes_queued)
                # break

            # Verify we are where we think we are
            if bytes_queued == 0:
                v_dma_get_addr_real = xbox.read_u32(XboxHelper.DMA_PULL_ADDR)
                print(
                    "Verifying hw (0x%08X) is at parser (0x%08X)"
                    % (v_dma_get_addr_real, v_dma_get_addr)
                )
                try:
                    assert v_dma_get_addr_real == v_dma_get_addr
                except:
                    xbox_helper.print_pb_state()
                    raise

        except Trace.MaxFlipExceeded:
            print("Max flip count reached")
            abort_now = True
        except:  # pylint: disable=bare-except
            traceback.print_exc()
            abort_now = True


def experimental_disable_z_compression_and_tiling(xbox):
    # Disable Z-buffer compression and Tiling
    # FIXME: This is a dirty dirty hack which breaks PFB and PGRAPH state!
    NV10_PGRAPH_RDI_INDEX = 0xFD400750
    NV10_PGRAPH_RDI_DATA = 0xFD400754
    for i in range(8):

        # This is from a discussion on nouveau IRC:
        #  mwk: the RDI copy is for texturing
        #  mwk: the mmio PGRAPH copy is for drawing to the framebuffer

        # Disabling Z-Compression seems to work fine
        def disable_z_compression(index):
            zcomp = xbox.read_u32(0xFD100300 + 4 * index)
            zcomp &= 0x7FFFFFFF
            xbox.write_u32(0xFD100300 + 4 * index, zcomp)  # PFB
            xbox.write_u32(0xFD400980 + 4 * index, zcomp)  # PGRAPH
            # PGRAPH RDI
            # FIXME: This scope should be atomic
            xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0090 + 4 * index)
            xbox.write_u32(NV10_PGRAPH_RDI_DATA, zcomp)

        disable_z_compression(i)

        # Disabling tiling entirely
        def disable_tiling(index):
            tile_addr = xbox.read_u32(0xFD100240 + 16 * index)
            tile_addr &= 0xFFFFFFFE
            xbox.write_u32(0xFD100240 + 16 * index, tile_addr)  # PFB
            xbox.write_u32(0xFD400900 + 16 * index, tile_addr)  # PGRAPH
            # PGRAPH RDI
            # FIXME: This scope should be atomic
            xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0010 + 4 * index)
            xbox.write_u32(NV10_PGRAPH_RDI_DATA, tile_addr)
            # xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0030 + 4 * i)
            # xbox.write_u32(NV10_PGRAPH_RDI_DATA, tile_limit)
            # xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0050 + 4 * i)
            # xbox.write_u32(NV10_PGRAPH_RDI_DATA, tile_pitch)

        disable_tiling(i)


def main(args):

    os.makedirs(args.out, exist_ok=True)

    if args.no_surface:
        Trace.SurfaceDumping = False

    if args.no_texture:
        Trace.TextureDumping = False

    if args.no_pixel:
        Trace.PixelDumping = False

    Trace.MaxFrames = args.max_flip

    global abort_now  # pylint: disable=C0103
    xbox = Xbox()
    xbox_helper = XboxHelper.XboxHelper(xbox)

    print("\n\nAwaiting stable PB state\n\n")
    v_dma_get_addr, v_dma_put_addr_real = _wait_for_stable_push_buffer_state(
        xbox, xbox_helper
    )

    if not v_dma_get_addr or not v_dma_put_addr_real:
        if not abort_now:
            print("\n\nFailed to reach stable state.\n\n")
        return

    print("\n\nStepping through PB\n\n")

    # Start measuring time
    begin_time = time.monotonic()

    if _enable_experimental_disable_z_compression_and_tiling:
        # TODO: Enable after removing FIXME above.
        experimental_disable_z_compression_and_tiling(xbox)

    # Create a new trace object
    trace = Trace.Tracer(v_dma_get_addr, v_dma_put_addr_real, xbox, xbox_helper)

    # Dump the initial state
    trace.command_count = -1
    trace.dump_surfaces(xbox, None)
    trace.command_count = 0

    _run(xbox, xbox_helper, v_dma_get_addr, trace)

    # Recover the real address
    xbox.write_u32(XboxHelper.DMA_PUSH_ADDR, trace.real_dma_put_addr)

    print("\n\nFinished PB\n\n")

    # We can continue the cache updates now.
    xbox_helper.resume_fifo_pusher()

    # Finish measuring time
    end_time = time.monotonic()
    duration = end_time - begin_time

    command_count = trace.recorded_command_count
    print(
        "Recorded %d flip stalls and %d PB commands (%.2f commands / second)"
        % (trace.recorded_flip_stall_count, command_count, command_count / duration)
    )


if __name__ == "__main__":

    def _parse_args():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-o",
            "--out",
            metavar="path",
            default="out",
            help="Set the output directory.",
        )

        parser.add_argument(
            "--no-surface", help="Disable dumping of surfaces.", action="store_true"
        )

        parser.add_argument(
            "--no-texture", help="Disable dumping of textures.", action="store_true"
        )

        parser.add_argument(
            "--no-pixel",
            help="Disable dumping of all graphical resources (surfaces, textures).",
            action="store_true",
        )

        parser.add_argument(
            "--max-flip",
            metavar="frames",
            default=0,
            type=int,
            help="Exit tracing after the given number of frame swaps.",
        )

        return parser.parse_args()

    sys.exit(main(_parse_args()))
