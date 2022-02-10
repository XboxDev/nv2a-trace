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

from AbortFlag import AbortFlag
from Xbox import Xbox
import XboxHelper
import Trace

# pylint: disable=invalid-name
# TODO: Remove tiling suppression once AGP read in Texture.py is fully proven.
_enable_experimental_disable_z_compression_and_tiling = False
# pylint: enable=invalid-name


def _wait_for_stable_push_buffer_state(
    xbox_helper: XboxHelper.XboxHelper, abort_flag: AbortFlag, verbose: bool = False
):
    """Blocks until the push buffer reaches a stable state."""

    dma_pull_addr = 0
    dma_push_addr_real = 0

    while not abort_flag.should_abort:

        # Stop consuming CACHE entries.
        xbox_helper.disable_pgraph_fifo()
        xbox_helper.wait_until_pgraph_idle()

        # Kick the pusher so that it fills the CACHE.
        xbox_helper.allow_populate_fifo_cache()

        # Now drain the CACHE.
        xbox_helper.enable_pgraph_fifo()

        # Check out where the PB currently is and where it was supposed to go.
        dma_push_addr_real = xbox_helper.get_dma_push_address()
        dma_pull_addr = xbox_helper.get_dma_pull_address()

        # Check if we have any methods left to run and skip those.
        state = xbox_helper.parse_dma_state()
        dma_method_count = state.method_count
        dma_pull_addr += dma_method_count * 4

        # Hide all commands from the PB by setting PUT = GET.
        dma_push_addr_target = dma_pull_addr
        xbox_helper.set_dma_push_address(dma_push_addr_target)

        if verbose:
            print("=== PRE RESUME ======")
            print("Real push addr: 0x%X" % dma_push_addr_real)
            xbox_helper.print_dma_addresses()
            xbox_helper.print_cache_state()

        # Resume pusher - The PB can't run yet, as it has no commands to process.
        xbox_helper.resume_fifo_pusher()

        # We might get issues where the pusher missed our PUT (miscalculated).
        # This can happen as `dma_method_count` is not the most accurate.
        # Probably because the DMA is halfway through a transfer.
        # So we pause the pusher again to validate our state
        xbox_helper.pause_fifo_pusher()

        time.sleep(0.1)

        if verbose:
            print("   POST RESUME")
            xbox_helper.print_dma_addresses()
            xbox_helper.print_cache_state()

        dma_push_addr_check = xbox_helper.get_dma_push_address()
        dma_pull_addr_check = xbox_helper.get_dma_pull_address()

        # We want the PB to be empty
        if dma_pull_addr_check != dma_push_addr_check:
            print(
                "  Pushbuffer not empty - PULL (0x%08X) != PUSH (0x%08X)"
                % (dma_pull_addr_check, dma_push_addr_check)
            )
            continue

        # Ensure that we are at the correct offset
        if dma_push_addr_check != dma_push_addr_target:
            print(
                "Oops PUT was modified; got 0x%08X but expected 0x%08X!"
                % (dma_push_addr_check, dma_push_addr_target)
            )
            continue

        break

    if abort_flag.should_abort:
        print("Restoring pfifo state...")
        xbox_helper.set_dma_push_address(dma_push_addr_real)
        xbox_helper.enable_pgraph_fifo()
        xbox_helper.resume_fifo_pusher()
        xbox_helper.print_enable_states()

    return dma_pull_addr, dma_push_addr_real


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

    xbox = Xbox()
    xbox_helper = XboxHelper.XboxHelper(xbox)

    abort_flag = AbortFlag()

    def signal_handler(_signal, _frame):
        if not abort_flag.should_abort:
            print("Got first SIGINT! Aborting..")
            abort_flag.abort()
        else:
            print("Got second SIGINT! Forcing exit")
            sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("\n\nAwaiting stable PB state\n\n")
    dma_pull_addr, dma_push_addr = _wait_for_stable_push_buffer_state(
        xbox_helper, abort_flag, args.verbose
    )

    if not dma_pull_addr or not dma_push_addr or abort_flag.should_abort:
        if not abort_flag.should_abort:
            print("\n\nFailed to reach stable state.\n\n")
        return

    print("\n\nStepping through PB\n\n")

    # Start measuring time
    begin_time = time.monotonic()

    if _enable_experimental_disable_z_compression_and_tiling:
        # TODO: Enable after removing FIXME above.
        experimental_disable_z_compression_and_tiling(xbox)

    # Create a new trace object
    pixel_dumping = not args.no_pixel
    enable_texture_dumping = pixel_dumping and not args.no_texture
    enable_surface_dumping = pixel_dumping and not args.no_surface
    enable_raw_pixel_dumping = pixel_dumping and not args.no_raw_pixel

    if args.alpha_mode == "both":
        alpha_mode = Trace.Tracer.ALPHA_MODE_BOTH
    elif args.alpha_mode == "keep":
        alpha_mode = Trace.Tracer.ALPHA_MODE_KEEP
    else:
        alpha_mode = Trace.Tracer.ALPHA_MODE_DROP

    trace = Trace.Tracer(
        dma_pull_addr,
        dma_push_addr,
        xbox,
        xbox_helper,
        abort_flag,
        output_dir=args.out,
        alpha_mode=alpha_mode,
        enable_texture_dumping=enable_texture_dumping,
        enable_surface_dumping=enable_surface_dumping,
        enable_raw_pixel_dumping=enable_raw_pixel_dumping,
        verbose=args.verbose,
        max_frames=args.max_flip,
    )

    # Dump the initial state
    trace.command_count = -1
    trace.dump_surfaces(xbox, None)
    trace.command_count = 0

    trace.run()

    # Recover the real address
    xbox.write_u32(XboxHelper.DMA_PUSH_ADDR, trace.real_dma_push_addr)

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
            "--no-raw-pixel",
            help="Disable raw memory dumping of all graphical resources (surfaces, textures).",
            action="store_true",
        )

        parser.add_argument(
            "--alpha-mode",
            default="drop",
            choices=["drop", "keep", "both"],
            help=(
                "Define how the alpha channel is handled in color graphical resources.\n"
                "  drop: Discard the alpha channel\n"
                "  keep: Save the alpha channel\n"
                "  drop: Save two dumps, one with the alpha channel and one without\n"
            ),
        )

        parser.add_argument(
            "-v",
            "--verbose",
            help="Enable verbose debug output.",
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
