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


import Trace

abortNow = False

def delay():
  #FIXME: if this returns `True`, the functions below should have their own
  #       loops which check for command completion
  #time.sleep(0.01)
  return False

def signal_handler(signal, frame):
  global abortNow
  if abortNow == False:
    print('Got first SIGINT! Aborting..')
    abortNow = True
  else:
    print('Got second SIGINT! Forcing exit')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

dma_state = 0xFD003228
dma_put_addr = 0xFD003240
dma_get_addr = 0xFD003244
dma_subroutine = 0xFD00324C

put_addr = 0xFD003210
put_state = 0xFD003220
get_addr = 0xFD003270
get_state = 0xFD003250

pgraph_state = 0xFD400720
pgraph_status = 0xFD400700

def disable_pgraph_fifo():
  s1 = read_u32(pgraph_state)
  write_u32(pgraph_state, s1 & 0xFFFFFFFE)

def wait_until_pgraph_idle():
  while(read_u32(pgraph_status) & 0x00000001):
    pass

def enable_pgraph_fifo():
  s1 = read_u32(pgraph_state)
  write_u32(pgraph_state, s1 | 0x00000001)
  if delay(): pass

def wait_until_pusher_idle():
  while(read_u32(get_state) & (1 << 4)):
    pass

def pause_fifo_puller():
  # Idle the puller and pusher
  s1 = read_u32(get_state)
  write_u32(get_state, s1 & 0xFFFFFFFE)
  if delay(): pass
  #print("Puller State was 0x" + format(s1, '08X'))

def pause_fifo_pusher():
  s1 = read_u32(put_state)
  write_u32(put_state, s1 & 0xFFFFFFFE)
  if delay(): pass
  if False:
    s1 = read_u32(0xFD003200)
    write_u32(0xFD003200, s1 & 0xFFFFFFFE)
    if delay(): pass
    #print("Pusher State was 0x" + format(s1, '08X'))

def resume_fifo_puller():
  # Resume puller and pusher
  s2 = read_u32(get_state)
  write_u32(get_state, (s2 & 0xFFFFFFFE) | 1) # Recover puller state
  if delay(): pass

def resume_fifo_pusher():
  if False:
    s2 = read_u32(0xFD003200)
    write_u32(0xFD003200, s2 & 0xFFFFFFFE | 1)
    if delay(): pass
  s2 = read_u32(put_state)
  write_u32(put_state, (s2 & 0xFFFFFFFE) | 1) # Recover pusher state
  if delay(): pass

def dumpPB(start, end):
  offset = start
  while(offset != end):
    offset = parseCommand(offset, True)
    if offset == 0:
      break

#FIXME: This works poorly if the method count is not 0
def dumpPBState():
  v_dma_get_addr = read_u32(dma_get_addr)
  v_dma_put_addr = read_u32(dma_put_addr)
  v_dma_subroutine = read_u32(dma_subroutine)

  print("PB-State: 0x%08X / 0x%08X / 0x%08X" % (v_dma_get_addr, v_dma_put_addr, v_dma_subroutine))
  dumpPB(v_dma_get_addr, v_dma_put_addr)
  print()

def dumpCacheState():
  v_get_addr = read_u32(get_addr)
  v_put_addr = read_u32(put_addr)

  v_get_state = read_u32(get_state)
  v_put_state = read_u32(put_state)

  print("CACHE-State: 0x%X / 0x%X" % (v_get_addr, v_put_addr))

  print("Put / Pusher enabled: %s" % ("Yes" if (v_put_state & 1) else "No"))
  print("Get / Puller enabled: %s" % ("Yes" if (v_get_state & 1) else "No"))

  print("Cache:")
  for i in range(128):

    cache1_method = read_u32(0xFD003800 + i * 8)
    cache1_data = read_u32(0xFD003804 + i * 8)

    s = "  [0x%02X] 0x%04X (0x%08X)" % (i, cache1_method, cache1_data)
    v_get_offset = i * 8 - v_get_addr
    if v_get_offset >= 0 and v_get_offset < 8:
      s += " < get[%d]" % v_get_offset
    v_put_offset = i * 8 - v_put_addr
    if v_put_offset >= 0 and v_put_offset < 8:
      s += " < put[%d]" % v_put_offset

    print(s)
  print()

  return

def printDMAstate():

  v_dma_state = read_u32(dma_state)
  v_dma_method = v_dma_state & 0x1FFC
  v_dma_subchannel = (v_dma_state >> 13) & 7
  v_dma_method_count = (v_dma_state >> 18) & 0x7ff
  v_dma_method_nonincreasing = v_dma_state & 1
  # higher bits are for error signalling?
  
  print("v_dma_method: 0x%04X (count: %d)" % (v_dma_method, v_dma_method_count))

def parseCommand(addr, display=False):

  word = read_u32(0x80000000 | addr)
  s = "0x%08X: Opcode: 0x%08X" % (addr, word)

  if ((word & 0xe0000003) == 0x20000000):
    print("old jump")
    #state->get_jmp_shadow = control->dma_get;
    #NV2A_DPRINTF("pb OLD_JMP 0x%" HWADDR_PRIx "\n", control->dma_get);
    addr = word & 0x1fffffff
  elif ((word & 3) == 1):
    addr = word & 0xfffffffc
    print("jump 0x%08X" % addr)
    #state->get_jmp_shadow = control->dma_get;

    if False:
      # Get the address after the first instruction after a jump
      # This is a hack, because it seems that the NV2A refuses to jump if there
      # is no room for a real method
      addr = parseCommand(addr, display)

  elif ((word & 3) == 2):
    print("unhandled opcode type: call")
    #if (state->subroutine_active) {
    #  state->error = NV_PFIFO_CACHE1_DMA_STATE_ERROR_CALL;
    #  break;
    #}
    #state->subroutine_return = control->dma_get;
    #state->subroutine_active = true;
    #control->dma_get = word & 0xfffffffc;
    addr = 0
  elif (word == 0x00020000):
    # return
    print("unhandled opcode type: return")
    addr = 0
  elif ((word & 0xe0030003) == 0) or ((word & 0xe0030003) == 0x40000000):
    # methods
    method = word & 0x1fff;
    subchannel = (word >> 13) & 7;
    method_count = (word >> 18) & 0x7ff;
    method_nonincreasing = word & 0x40000000;
    #state->dcount = 0;

    s += "; Method: 0x%04X (%d times)" % (method, method_count)
    addr += 4 + method_count * 4

  else:
    print("unknown opcode type")

  if display:
    print(s)

  return addr




# Hack to pretend we have a better API in xboxpy
class Xbox:
  def __init__(self):
    self.read_u32 = read_u32
    self.read = read
xbox = Xbox()

def main():

  global abortNow

  DebugPrint = False

  print("\n\nSearching stable PB state\n\n")
  
  while True:

    # Stop consuming CACHE entries.
    disable_pgraph_fifo()

    # Kick the pusher, so that it fills the cache CACHE.
    resume_fifo_pusher()
    pause_fifo_pusher()

    # Now drain the CACHE
    enable_pgraph_fifo()

    # Check out where the PB currently is and where it was supposed to go.
    v_dma_put_addr_real = read_u32(dma_put_addr)
    v_dma_get_addr = read_u32(dma_get_addr)

    # Check if we have any methods left to run and skip those.
    v_dma_state = read_u32(dma_state)
    v_dma_method_count = (v_dma_state >> 18) & 0x7ff
    v_dma_get_addr += v_dma_method_count * 4

    # Hide all commands from the PB by setting PUT = GET.
    v_dma_put_addr_target = v_dma_get_addr
    write_u32(dma_put_addr, v_dma_put_addr_target)

    # Resume pusher - The PB can't run yet, as it has no commands to process.
    resume_fifo_pusher()

  
    # We might get issues where the pusher missed our PUT (miscalculated).
    # This can happen as `v_dma_method_count` is not the most accurate.
    # Probably because the DMA is halfway through a transfer.
    # So we pause the pusher again to validate our state
    pause_fifo_pusher()

    v_dma_put_addr_target_check = read_u32(dma_put_addr)
    v_dma_get_addr_check = read_u32(dma_get_addr)

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
    v_dma_put_addr_target = parseCommand(v_dma_get_addr, DebugPrint)

    # If we don't know where this command ends, we have to abort.
    if v_dma_put_addr_target == 0:
      print("Aborting due to unknown PB command")

      # Recover the real address as Xbox would get stuck otherwise.
      write_u32(dma_put_addr, v_dma_put_addr_real)

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
    write_u32(dma_put_addr, v_dma_put_addr_target)

    def JumpCheck(v_dma_put_addr_real):
      # See if the PB target was modified.
      # If necessary, we recover the current target to keep the GPU stuck on our
      # current command.
      v_dma_put_addr_new_real = read_u32(dma_put_addr)
      if (v_dma_put_addr_new_real != v_dma_put_addr_target):
        print("PB was modified! Got 0x%08X, but expected: 0x%08X; Restoring." % (v_dma_put_addr_new_real, v_dma_put_addr_target))
        #FIXME: Ensure that the pusher is still disabled, or we might be
        #       screwed already. Because the pusher probably pushed new data
        #       to the CACHE which we attempt to avoid.

        s1 = read_u32(put_state)
        if s1 & 1:
          print("PB was modified and pusher was already active!")
          time.sleep(60.0)

        write_u32(dma_put_addr, v_dma_put_addr_target)
        v_dma_put_addr_real = v_dma_put_addr_new_real
      return v_dma_put_addr_real

    # Loop while this command is being ran.
    # This is necessary because a whole command might not fit into CACHE.
    # So we have to process it chunk by chunk.
    command_base = v_dma_get_addr
    while v_dma_get_addr >= command_base and v_dma_get_addr < v_dma_put_addr_target:
      if DebugPrint: print("At 0x%08X, target is 0x%08X (Real: 0x%08X)" % (v_dma_get_addr, v_dma_put_addr_target, v_dma_put_addr_real))
      if DebugPrint: printDMAstate()

      # Disable PGRAPH, so it can't run anything from CACHE.
      disable_pgraph_fifo()
      wait_until_pgraph_idle()

      # This scope should be atomic.
      if True:

        # Avoid running bad code, if the PUT was modified sometime during
        # this command.
        v_dma_put_addr_real = JumpCheck(v_dma_put_addr_real)

        # Kick our planned commands into CACHE now.
        resume_fifo_pusher()
        pause_fifo_pusher()

      # Run the commands we have moved to CACHE, by enabling PGRAPH.
      enable_pgraph_fifo()

      # Get the updated PB address.
      v_dma_get_addr = read_u32(dma_get_addr)

    # It's possible that the CPU updated the PUT after execution
    v_dma_put_addr_real = JumpCheck(v_dma_put_addr_real)

    # Also show that we processed the commands.
    if DebugPrint: dumpPBState()

    # Check if the user wants to exit
    if abortNow:
      write_u32(dma_put_addr, v_dma_put_addr_real)
      break

  print("\n\nFinished PB\n\n")

  # We can continue the cache updates now.
  resume_fifo_pusher()

  # Finish measuring time
  end_time = time.monotonic()
  duration = end_time - begin_time

  flipStallCount = Trace.recordedFlipStallCount()
  commandCount = Trace.recordedPushBufferCommandCount()
  
  print("Recorded %d flip stalls and %d PB commands (%.2f commands / second)" % (flipStallCount, commandCount, commandCount / duration))

if __name__ == '__main__':
  main()
