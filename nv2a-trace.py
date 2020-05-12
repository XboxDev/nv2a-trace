#!/usr/bin/env python3

from xboxpy import *

from helper import *

# Create output folder
import os
try:
  os.mkdir("out")
except:
  pass

import time
import signal
import sys
import struct
import traceback

from helper import *

import Trace


abortNow = False


def signal_handler(signal, frame):
  global abortNow
  if abortNow == False:
    print('Got first SIGINT! Aborting..')
    abortNow = True
  else:
    print('Got second SIGINT! Forcing exit')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# Hack to pretend we have a better API in xboxpy
class Xbox:
  def __init__(self):
    self.read_u32 = read_u32
    self.write_u32 = write_u32
    self.read = read
    self.write = write
    self.call = api.call
    self.ke = ke
xbox = Xbox()

xbox_helper = XboxHelper(xbox)

def main():

  global abortNow

  print("\n\nSearching stable PB state\n\n")
  
  while True:

    # Stop consuming CACHE entries.
    xbox_helper.disable_pgraph_fifo()
    xbox_helper.wait_until_pgraph_idle()

    # Kick the pusher, so that it fills the cache CACHE.
    xbox_helper.resume_fifo_pusher()
    xbox_helper.pause_fifo_pusher()

    # Now drain the CACHE.
    xbox_helper.enable_pgraph_fifo()

    # Check out where the PB currently is and where it was supposed to go.
    v_dma_put_addr_real = xbox.read_u32(dma_put_addr)
    v_dma_get_addr = xbox.read_u32(dma_get_addr)

    # Check if we have any methods left to run and skip those.
    v_dma_state = xbox.read_u32(dma_state)
    v_dma_method_count = (v_dma_state >> 18) & 0x7ff
    v_dma_get_addr += v_dma_method_count * 4

    # Hide all commands from the PB by setting PUT = GET.
    v_dma_put_addr_target = v_dma_get_addr
    xbox.write_u32(dma_put_addr, v_dma_put_addr_target)

    # Resume pusher - The PB can't run yet, as it has no commands to process.
    xbox_helper.resume_fifo_pusher()

  
    # We might get issues where the pusher missed our PUT (miscalculated).
    # This can happen as `v_dma_method_count` is not the most accurate.
    # Probably because the DMA is halfway through a transfer.
    # So we pause the pusher again to validate our state
    xbox_helper.pause_fifo_pusher()

    time.sleep(1.0)

    v_dma_put_addr_target_check = xbox.read_u32(dma_put_addr)
    v_dma_get_addr_check = xbox.read_u32(dma_get_addr)

    # We want the PB to be paused
    if v_dma_get_addr_check != v_dma_put_addr_target_check:
      print("Oops GET did not reach PUT!")
      continue

    # Ensure that we are at the correct offset
    if v_dma_put_addr_target_check != v_dma_put_addr_target:
      print("Oops PUT was modified!")
      continue

    break
   
  print("\n\nStepping through PB\n\n")

  # Start measuring time
  begin_time = time.monotonic()

  bytes_queued = 0

  # Disable Z-buffer compression and Tiling
  # FIXME: This is a dirty dirty hack which breaks PFB and PGRAPH state!
  NV10_PGRAPH_RDI_INDEX = 0xFD400750
  NV10_PGRAPH_RDI_DATA = 0xFD400754
  for i in range(8):

    # This is from a discussion on nouveau IRC:
    #  mwk: the RDI copy is for texturing
    #  mwk: the mmio PGRAPH copy is for drawing to the framebuffer

    # Disabling Z-Compression seems to work fine
    if True:
      zcomp = xbox.read_u32(0xFD100300 + 4 * i)
      zcomp &= 0x7FFFFFFF
      xbox.write_u32(0xFD100300 + 4 * i, zcomp) # PFB
      xbox.write_u32(0xFD400980 + 4 * i, zcomp) # PGRAPH
      if True: # PGRAPH RDI
        #FIXME: This scope should be atomic
        xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0090 + 4 * i)
        xbox.write_u32(NV10_PGRAPH_RDI_DATA, zcomp)

    # Disabling tiling entirely
    if True:
      tile_addr = xbox.read_u32(0xFD100240 + 16 * i)
      tile_addr &= 0xFFFFFFFE
      xbox.write_u32(0xFD100240 + 16 * i, tile_addr) # PFB
      xbox.write_u32(0xFD400900 + 16 * i, tile_addr) # PGRAPH
      if True: # PGRAPH RDI
        #FIXME: This scope should be atomic
        xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0010 + 4 * i)
        xbox.write_u32(NV10_PGRAPH_RDI_DATA, tile_addr)
        #xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0030 + 4 * i)
        #xbox.write_u32(NV10_PGRAPH_RDI_DATA, tile_limit)
        #xbox.write_u32(NV10_PGRAPH_RDI_INDEX, 0x00EA0050 + 4 * i)
        #xbox.write_u32(NV10_PGRAPH_RDI_DATA, tile_pitch)

  # Create a new trace object
  trace = Trace.Tracer(v_dma_get_addr, v_dma_put_addr_real)


  # Record initial state
  trace.commandCount = -1
  trace.DumpSurfaces(xbox, None)
  trace.commandCount = 0

  # Step through the PB until we abort
  while not abortNow:

    try:

      v_dma_get_addr, unprocessed_bytes = trace.processPushBufferCommand(xbox, xbox_helper, v_dma_get_addr)
      bytes_queued += unprocessed_bytes

      #time.sleep(0.5)

      # Avoid queuing up too many bytes: while the buffer is being processed,
      # D3D might fixup the buffer if GET is still too far away.
      if v_dma_get_addr == trace.real_dma_put_addr or bytes_queued >= 200:
        print("Flushing buffer until (0x%08X)" % v_dma_get_addr)
        trace.run_fifo(xbox, xbox_helper, v_dma_get_addr)
        bytes_queued = 0
        if False:
          xbox_helper.dumpPBState()
          X = 4
          print(["PRE "] + ["%08X" % x for x in struct.unpack("<" + "L" * X, xbox.read(0x80000000 | (v_dma_get_addr - X * 4), X * 4))])
          print(["POST"] + ["%08X" % x for x in struct.unpack("<" + "L" * X, xbox.read(0x80000000 | (v_dma_get_addr        ), X * 4))])

      if v_dma_get_addr == trace.real_dma_put_addr:
        print("Reached end of buffer?!")
        #break

      # Verify we are where we think we are
      if bytes_queued == 0:
        v_dma_get_addr_real = xbox.read_u32(dma_get_addr)
        print("Verifying hw (0x%08X) is at parser (0x%08X)" % (v_dma_get_addr_real, v_dma_get_addr))
        try:
          assert(v_dma_get_addr_real == v_dma_get_addr)
        except:
          xbox_helper.dumpPBState()
          raise

    except:
      traceback.print_exc()
      abortNow = True

  # Recover the real address
  xbox.write_u32(dma_put_addr, trace.real_dma_put_addr)

  print("\n\nFinished PB\n\n")

  # We can continue the cache updates now.
  xbox_helper.resume_fifo_pusher()

  # Finish measuring time
  end_time = time.monotonic()
  duration = end_time - begin_time

  flipStallCount = trace.recordedFlipStallCount()
  commandCount = trace.recordedPushBufferCommandCount()
  
  print("Recorded %d flip stalls and %d PB commands (%.2f commands / second)" % (flipStallCount, commandCount, commandCount / duration))

if __name__ == '__main__':
  main()
