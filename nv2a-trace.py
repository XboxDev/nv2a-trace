#!/usr/bin/env python3

from xboxpy import *

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
    self.read = read
    self.write_u32 = write_u32
xbox = Xbox()

xbox_helper = XboxHelper(xbox)

def main():

  global abortNow

  DebugPrint = False

  print("\n\nSearching stable PB state\n\n")
  
  while True:

    # Stop consuming CACHE entries.
    xbox_helper.disable_pgraph_fifo()

    # Kick the pusher, so that it fills the cache CACHE.
    xbox_helper.resume_fifo_pusher()
    xbox_helper.pause_fifo_pusher()

    # Now drain the CACHE
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

  # Step through the PB until we finish.
  while(v_dma_get_addr != v_dma_put_addr_real):

    print("@0x%08X; wants to be at 0x%08X" % (v_dma_get_addr, v_dma_put_addr_target))

    # Get size of current command.
    v_dma_put_addr_target = xbox_helper.parseCommand(v_dma_get_addr, DebugPrint)

    # If we don't know where this command ends, we have to abort.
    if v_dma_put_addr_target == 0:
      print("Aborting due to unknown PB command")

      # Recover the real address as Xbox would get stuck otherwise.
      xbox.write_u32(dma_put_addr, v_dma_put_addr_real)

      break

    # Do whatever we want to do with the queued command / methods
    try:

      # Emulate the current instruction stream.
      #FIXME: This will create dumps, but nothing has actually run yet.
      #       If one of the methods sets a register, and then another one draws
      #       Then we won't have a state for that draw call.
      #       We need better integration of this.
      Trace.recordPushBufferCommand(xbox, v_dma_get_addr)

    # Catches any errors so we don't leave the GPU in a bad state.
    # We'll force quit now though
    except Exception as err:
      traceback.print_exc()
      abortNow = True

    # Queue this command
    xbox.write_u32(dma_put_addr, v_dma_put_addr_target)

    def JumpCheck(v_dma_put_addr_real):
      # See if the PB target was modified.
      # If necessary, we recover the current target to keep the GPU stuck on our
      # current command.
      v_dma_put_addr_new_real = xbox.read_u32(dma_put_addr)
      if (v_dma_put_addr_new_real != v_dma_put_addr_target):
        print("PB was modified! Got 0x%08X, but expected: 0x%08X; Restoring." % (v_dma_put_addr_new_real, v_dma_put_addr_target))
        #FIXME: Ensure that the pusher is still disabled, or we might be
        #       screwed already. Because the pusher probably pushed new data
        #       to the CACHE which we attempt to avoid.

        s1 = xbox.read_u32(put_state)
        if s1 & 1:
          print("PB was modified and pusher was already active!")
          time.sleep(60.0)

        xbox.write_u32(dma_put_addr, v_dma_put_addr_target)
        v_dma_put_addr_real = v_dma_put_addr_new_real
      return v_dma_put_addr_real

    # Loop while this command is being ran.
    # This is necessary because a whole command might not fit into CACHE.
    # So we have to process it chunk by chunk.
    command_base = v_dma_get_addr
    while v_dma_get_addr >= command_base and v_dma_get_addr < v_dma_put_addr_target:
      if DebugPrint: print("At 0x%08X, target is 0x%08X (Real: 0x%08X)" % (v_dma_get_addr, v_dma_put_addr_target, v_dma_put_addr_real))
      if DebugPrint: xbox_helper.printDMAstate()

      # Disable PGRAPH, so it can't run anything from CACHE.
      xbox_helper.disable_pgraph_fifo()
      xbox_helper.wait_until_pgraph_idle()

      # This scope should be atomic.
      if True:

        # Avoid running bad code, if the PUT was modified sometime during
        # this command.
        v_dma_put_addr_real = JumpCheck(v_dma_put_addr_real)

        # Kick our planned commands into CACHE now.
        xbox_helper.resume_fifo_pusher()
        xbox_helper.pause_fifo_pusher()

      # Run the commands we have moved to CACHE, by enabling PGRAPH.
      xbox_helper.enable_pgraph_fifo()

      # Get the updated PB address.
      v_dma_get_addr = xbox.read_u32(dma_get_addr)

    # It's possible that the CPU updated the PUT after execution
    v_dma_put_addr_real = JumpCheck(v_dma_put_addr_real)

    # Also show that we processed the commands.
    if DebugPrint: xbox_helper.dumpPBState()

    # Check if the user wants to exit
    if abortNow:
      xbox.write_u32(dma_put_addr, v_dma_put_addr_real)
      break

  print("\n\nFinished PB\n\n")

  # We can continue the cache updates now.
  xbox_helper.resume_fifo_pusher()

  # Finish measuring time
  end_time = time.monotonic()
  duration = end_time - begin_time

  flipStallCount = Trace.recordedFlipStallCount()
  commandCount = Trace.recordedPushBufferCommandCount()
  
  print("Recorded %d flip stalls and %d PB commands (%.2f commands / second)" % (flipStallCount, commandCount, commandCount / duration))

if __name__ == '__main__':
  main()
