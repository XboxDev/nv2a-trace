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


def parseCommand(addr, word, display=False):

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
      # Get the address after the first instruction after a jump?
      # This is a hack, because it seems that the NV2A refuses to jump if there
      # is no room for a real method
      assert(False)

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



class XboxHelper():

  def __init__(self, xbox):
    self.xbox = xbox

  def delay(self):
    #FIXME: if this returns `True`, the functions below should have their own
    #       loops which check for command completion
    #time.sleep(0.01)
    return False

  def disable_pgraph_fifo(self):
    s1 = self.xbox.read_u32(pgraph_state)
    self.xbox.write_u32(pgraph_state, s1 & 0xFFFFFFFE)

  def wait_until_pgraph_idle(self):
    while(self.xbox.read_u32(pgraph_status) & 0x00000001):
      pass

  def enable_pgraph_fifo(self):
    s1 = self.xbox.read_u32(pgraph_state)
    self.xbox.write_u32(pgraph_state, s1 | 0x00000001)
    if self.delay(): pass

  def wait_until_pusher_idle(self):
    while(self.xbox.read_u32(get_state) & (1 << 4)):
      pass

  def pause_fifo_puller(self):
    # Idle the puller and pusher
    s1 = self.xbox.read_u32(get_state)
    self.xbox.write_u32(get_state, s1 & 0xFFFFFFFE)
    if self.delay(): pass
    #print("Puller State was 0x" + format(s1, '08X'))

  def pause_fifo_pusher(self):
    s1 = self.xbox.read_u32(put_state)
    self.xbox.write_u32(put_state, s1 & 0xFFFFFFFE)
    if self.delay(): pass
    if False:
      s1 = self.xbox.read_u32(0xFD003200)
      self.xbox.write_u32(0xFD003200, s1 & 0xFFFFFFFE)
      if self.delay(): pass
      #print("Pusher State was 0x" + format(s1, '08X'))

  def resume_fifo_puller(self):
    # Resume puller and pusher
    s2 = self.xbox.read_u32(get_state)
    self.xbox.write_u32(get_state, (s2 & 0xFFFFFFFE) | 1) # Recover puller state
    if self.delay(): pass

  def resume_fifo_pusher(self):
    if False:
      s2 = self.xbox.read_u32(0xFD003200)
      self.xbox.write_u32(0xFD003200, s2 & 0xFFFFFFFE | 1)
      if self.delay(): pass
    s2 = self.xbox.read_u32(put_state)
    self.xbox.write_u32(put_state, (s2 & 0xFFFFFFFE) | 1) # Recover pusher state
    if self.delay(): pass

  def dumpPB(self, start, end):
    offset = start
    while(offset != end):
      word = self.xbox.read_u32(0x80000000 | offset)
      offset = parseCommand(offset, word, True)
      if offset == 0:
        break

  #FIXME: This works poorly if the method count is not 0
  def dumpPBState(self):
    v_dma_get_addr = self.xbox.read_u32(dma_get_addr)
    v_dma_put_addr = self.xbox.read_u32(dma_put_addr)
    v_dma_subroutine = self.xbox.read_u32(dma_subroutine)

    print("PB-State: 0x%08X / 0x%08X / 0x%08X" % (v_dma_get_addr, v_dma_put_addr, v_dma_subroutine))
    self.dumpPB(v_dma_get_addr, v_dma_put_addr)
    print()

  def dumpCacheState(self):
    v_get_addr = self.xbox.read_u32(get_addr)
    v_put_addr = self.xbox.read_u32(put_addr)

    v_get_state = self.xbox.read_u32(get_state)
    v_put_state = self.xbox.read_u32(put_state)

    print("CACHE-State: 0x%X / 0x%X" % (v_get_addr, v_put_addr))

    print("Put / Pusher enabled: %s" % ("Yes" if (v_put_state & 1) else "No"))
    print("Get / Puller enabled: %s" % ("Yes" if (v_get_state & 1) else "No"))

    print("Cache:")
    for i in range(128):

      cache1_method = self.xbox.read_u32(0xFD003800 + i * 8)
      cache1_data = self.xbox.read_u32(0xFD003804 + i * 8)

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

  def printDMAstate(self):

    v_dma_state = self.xbox.read_u32(dma_state)
    v_dma_method = v_dma_state & 0x1FFC
    v_dma_subchannel = (v_dma_state >> 13) & 7
    v_dma_method_count = (v_dma_state >> 18) & 0x7ff
    v_dma_method_nonincreasing = v_dma_state & 1
    # higher bits are for error signalling?
    
    print("v_dma_method: 0x%04X (count: %d)" % (v_dma_method, v_dma_method_count))
