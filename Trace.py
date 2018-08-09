import os
import struct
import time
import traceback

import Texture

from helper import *

PixelDumping = True
DebugPrint = False

debugLog = os.path.join("out", "debug.html")
def addHTML(xx):
  f = open(debugLog,"a")
  f.write("<tr>")
  for x in xx:
    f.write("<td>%s</td>" % x)
  f.write("</tr>\n")
  f.close()
f = open(debugLog,"w")
f.write("<html><head><style>body { font-family: sans-serif; background:#333; color: #ccc } img { border: 1px solid #FFF; } td, tr, table { background: #444; padding: 10px; border:1px solid #888; border-collapse: collapse; }</style></head><body><table>\n")
#FIXME: atexit close tags.. but yolo!
f.close()
addHTML(["<b>#</b>", "<b>Opcode / Method</b>", "..."])



pgraph_dump = None



def html_print(s):
  print(s)
  addHTML([s])


import atexit

def load_binary(xbox, code):
  code_addr = xbox.ke.MmAllocateContiguousMemory(len(code))
  print("Allocated 0x%08X" % code_addr)
  def free_code():
    print("Free'ing 0x%08X" % code_addr)
    xbox.ke.MmFreeContiguousMemory(code_addr)
  atexit.register(free_code)
  xbox.write(code_addr, code)
  return code_addr


exchange_u32_addr = None
def exchange_u32_call(xbox, address, value):
  global exchange_u32_addr
  if exchange_u32_addr is None:
    exchange_u32_addr = load_binary(xbox, bytes([ 0xFA, 0x8B, 0x44, 0x24, 0x04, 0x8B, 0x54, 0x24, 0x08, 0x87, 0x02, 0xFB, 0xC2, 0x08, 0x00 ]))
    print("exchange_u32 installed at 0x%08X" % exchange_u32_addr)
  return xbox.call(exchange_u32_addr, struct.pack("<LL", value, address))['eax']

def exchange_u32_simple(xbox, address, value):
  old_value = xbox.read_u32(address)
  xbox.write_u32(address, value)
  return old_value

def exchange_u32(xbox, address, value):
  return exchange_u32_call(xbox, address, value)

def dumpPGRAPH(xbox):
  buffer = bytearray([])
  buffer.extend(xbox.read(0xFD400000, 0x200))

  # 0xFD400200 hangs Xbox, I just skipped to 0x400.
  # Needs further testing which regions work.
  buffer.extend(bytes([0] * 0x200))

  buffer.extend(xbox.read(0xFD400400, 0x2000 - 0x400))

  # Return the PGRAPH dump
  assert(len(buffer) == 0x2000)
  return bytes(buffer)




kick_fifo_addr = None
def kick_fifo_call(xbox, expected_put):
  global kick_fifo_addr
  if kick_fifo_addr is None:
    kick_fifo_addr = load_binary(xbox, open("kick_fifo", "rb").read())
    print("kick_fifo installed at 0x%08X" % kick_fifo_addr)
  eax = xbox.call(kick_fifo_addr, struct.pack("<L", expected_put))['eax']
  assert(eax != 0xBADBAD)

# This version is open to race conditions, where PUT is modified.
# This might lead to accidental command injection.
def kick_fifo_simple(xbox, expected_put):
  resume_fifo_pusher(xbox)
  pause_fifo_pusher(xbox)

def kick_fifo(xbox, expected_put):
  kick_fifo_call(xbox, expected_put)


class Tracer():












  #FIXME: Maybe take a list of vertices?
  def DumpVertexAttributes(self, xbox, data, *args):
    pass
    return []

  def DumpBlitSource(self, xbox, data, *args):
    pass
    return []

  def DumpBlitDest(self, xbox, data, *args):
    pass
    return []


  def DumpTextures(self, xbox, data, *args):
    global PixelDumping
    if not PixelDumping:
      return []
      
    return [] #FIXME: Remove, dirty hack to speedup debugging

    extraHTML = []

    for i in range(4):
      path = "command%d--tex_%d.png" % (self.commandCount, i)
      img = Texture.dumpTextureUnit(xbox, i)
      if img != None:
        img.save(os.path.join("out", path))
      extraHTML += ['<img height="128px" src="%s" alt="%s"/>' % (path, path)]

    return extraHTML

  def DumpSurfaces(self, xbox, data, *args):
    global PixelDumping
    if not PixelDumping:
      return []
    
  #  offset = color_offset
    pitch = xbox.read_u32(0xFD400858) # FIXME: Read from PGRAPH
    #FIXME: Poor var names

    surface_color_offset = xbox.read_u32(0xFD400828)
    surface_clip_x = xbox.read_u32(0xFD4019B4)
    surface_clip_y = xbox.read_u32(0xFD4019B8)

    offset = surface_color_offset

    draw_format = xbox.read_u32(0xFD400804)
    surface_type = xbox.read_u32(0xFD400710)
    swizzle_unk = xbox.read_u32(0xFD400818)

    swizzle_unk2 = xbox.read_u32(0xFD40086c)

    width = (surface_clip_x >> 16) & 0xFFFF
    height = (surface_clip_y >> 16) & 0xFFFF


    #FIXME: 128 x 128 [pitch = 256 (0x100)], at 0x01AA8000 [PGRAPH: 0x01AA8000?], format 0x5, type: 0x21000002, swizzle: 0x7070000 [used 0]

    #FIXME: This does not seem to be a good field for this
    #FIXME: Patched to give 50% of coolness
    swizzled = True #commandCount & 1 #((surface_type & 3) == 1)
    #FIXME: if surface_type is 0, we probably can't even draw..


    color_fmt = (draw_format >> 12) & 0xF

     #FIXME: Remove, dirty hack to speedup debugging
    if color_fmt != 5:
      #return []
      pass
    else:
      #swizzled = False
      pass


    if color_fmt == 0x3: # ARGB1555
      fmt_color = 0x3 if swizzled else 0x1C
    elif color_fmt == 0x5: # RGB565
      fmt_color = 0x5 if swizzled else 0x11
    elif color_fmt == 0x7 or color_fmt == 0x8: # XRGB8888
      fmt_color = 0x7 if swizzled else 0x1E
    elif color_fmt == 0xC: # ARGB8888
      fmt_color = 0x6 if swizzled else 0x12
    else:
      raise Exception("Oops! Unknown color fmt %d (0x%X)" % (color_fmt, color_fmt))



    #FIXME: Respect anti-aliasing

    path = "command%d--color.png" % (self.commandCount)
    extraHTML = []
    extraHTML += ['<img height="128px" src="%s" alt="%s"/>' % (path, path)]
    extraHTML += ['%d x %d [pitch = %d (0x%X)], at 0x%08X [PGRAPH: 0x%08X?], format 0x%X, type: 0x%X, swizzle: 0x%08X, 0x%08X [used %d]' % (width, height, pitch, pitch, offset, surface_color_offset, color_fmt, surface_type, swizzle_unk, swizzle_unk2, swizzled)]
    print(extraHTML[-1])

    try:
      if offset == 0x00000000:
        raise Exception()
      else:
        img = Texture.dumpTexture(xbox, offset, pitch, fmt_color, width, height)
    except:
      img = None

    if img != None:

      # Hack to remove alpha channel
      if True:
        img = img.convert('RGB')

      img.save(os.path.join("out", path))

    return extraHTML

  def HandleBegin(self, xbox, data, *args):

    # Avoid handling End
    if data == 0:
      return []

    extraHTML = []
    #extraHTML += self.DumpSurfaces(xbox, data, *args)
    #extraHTML += self.DumpTextures(xbox, data, *args)
    return extraHTML

  def HandleEnd(self, xbox, data, *args):

    # Avoid handling Begin
    if data != 0:
      return []

    extraHTML = []
    extraHTML += self.DumpSurfaces(xbox, data, *args)
    return extraHTML

  def beginPGRAPHRecord(self, xbox, data, *args):
    global pgraph_dump
    pgraph_dump = dumpPGRAPH(xbox)
    addHTML(["", "", "", "", "Dumped PGRAPH for later"])
    return []

  def endPGRAPHRecord(xbox, data, *args):
    global pgraph_dump

    # Debug feature to understand PGRAPH
    if pgraph_dump != None:
      new_pgraph_dump = dumpPGRAPH(xbox)

      # This blacklist was created from a CLEAR_COLOR, CLEAR
      blacklist = []
      blacklist += [0x0040000C] # 0xF3DF0479 → 0xF3DE04F9
      blacklist += [0x0040002C] # 0xF3DF37FF → 0xF3DE37FF
      blacklist += [0x0040010C] # 0x03DF0000 → 0x020000F1
      blacklist += [0x0040012C] # 0x13DF379F → 0x131A37FF
      blacklist += [0x00400704] # 0x00001D9C → 0x00001D94
      blacklist += [0x00400708] # 0x01DF0000 → 0x000000F1
      blacklist += [0x0040070C] # 0x01DF0000 → 0x000000F1
      blacklist += [0x0040072C] # 0x01DF2700 → 0x000027F1
      blacklist += [0x00400740] # 0x01DF37DD → 0x01DF37FF
      blacklist += [0x00400744] # 0x18111D9C → 0x18111D94
      blacklist += [0x00400748] # 0x01DF0011 → 0x000000F1
      blacklist += [0x0040074C] # 0x01DF0097 → 0x000000F7
      blacklist += [0x00400750] # 0x00DF005C → 0x00DF0064
      blacklist += [0x00400760] # 0x000000CC → 0x000000FF
      blacklist += [0x00400764] # 0x08001D9C → 0x08001D94
      blacklist += [0x00400768] # 0x01DF0000 → 0x000000F1
      blacklist += [0x0040076C] # 0x01DF0000 → 0x000000F1
      blacklist += [0x00400788] # 0x01DF110A → 0x000011FB
      blacklist += [0x004007A0] # 0x00200100 → 0x00201D70
      blacklist += [0x004007A4] # 0x00200100 → 0x00201D70
      blacklist += [0x004007A8] # 0x00200100 → 0x00201D70
      blacklist += [0x004007AC] # 0x00200100 → 0x00201D70
      blacklist += [0x004007B0] # 0x00200100 → 0x00201D70
      blacklist += [0x004007B4] # 0x00200100 → 0x00201D70
      blacklist += [0x004007B8] # 0x00200100 → 0x00201D70
      blacklist += [0x004007BC] # 0x00200100 → 0x00201D70
      blacklist += [0x004007C0] # 0x00000000 → 0x000006C9
      blacklist += [0x004007C4] # 0x00000000 → 0x000006C9
      blacklist += [0x004007C8] # 0x00000000 → 0x000006C9
      blacklist += [0x004007CC] # 0x00000000 → 0x000006C9
      blacklist += [0x004007D0] # 0x00000000 → 0x000006C9
      blacklist += [0x004007D4] # 0x00000000 → 0x000006C9
      blacklist += [0x004007D8] # 0x00000000 → 0x000006C9
      blacklist += [0x004007DC] # 0x00000000 → 0x000006C9
      blacklist += [0x004007E0] # 0x00000000 → 0x000006C9
      blacklist += [0x004007E4] # 0x00000000 → 0x000006C9
      blacklist += [0x004007E8] # 0x00000000 → 0x000006C9
      blacklist += [0x004007EC] # 0x00000000 → 0x000006C9
      blacklist += [0x004007F0] # 0x00000000 → 0x000006C9
      blacklist += [0x004007F4] # 0x00000000 → 0x000006C9
      blacklist += [0x004007F8] # 0x00000000 → 0x000006C9
      blacklist += [0x004007FC] # 0x00000000 → 0x000006C9
      blacklist += [0x00400D6C] # 0x00000000 → 0xFF000000
      blacklist += [0x0040110C] # 0x03DF0000 → 0x020000F1
      blacklist += [0x0040112C] # 0x13DF379F → 0x131A37FF
      blacklist += [0x00401704] # 0x00001D9C → 0x00001D94
      blacklist += [0x00401708] # 0x01DF0000 → 0x000000F1
      blacklist += [0x0040170C] # 0x01DF0000 → 0x000000F1
      blacklist += [0x0040172C] # 0x01DF2700 → 0x000027F1
      blacklist += [0x00401740] # 0x01DF37FD → 0x01DF37FF
      blacklist += [0x00401744] # 0x18111D9C → 0x18111D94
      blacklist += [0x00401748] # 0x01DF0011 → 0x000000F1
      blacklist += [0x0040174C] # 0x01DF0097 → 0x000000F7
      blacklist += [0x00401750] # 0x00DF0064 → 0x00DF006C
      blacklist += [0x00401760] # 0x000000CC → 0x000000FF
      blacklist += [0x00401764] # 0x08001D9C → 0x08001D94
      blacklist += [0x00401768] # 0x01DF0000 → 0x000000F1
      blacklist += [0x0040176C] # 0x01DF0000 → 0x000000F1
      blacklist += [0x00401788] # 0x01DF110A → 0x000011FB
      blacklist += [0x004017A0] # 0x00200100 → 0x00201D70
      blacklist += [0x004017A4] # 0x00200100 → 0x00201D70
      blacklist += [0x004017A8] # 0x00200100 → 0x00201D70
      blacklist += [0x004017AC] # 0x00200100 → 0x00201D70
      blacklist += [0x004017B0] # 0x00200100 → 0x00201D70
      blacklist += [0x004017B4] # 0x00200100 → 0x00201D70
      blacklist += [0x004017B8] # 0x00200100 → 0x00201D70
      blacklist += [0x004017BC] # 0x00200100 → 0x00201D70
      blacklist += [0x004017C0] # 0x00000000 → 0x000006C9
      blacklist += [0x004017C4] # 0x00000000 → 0x000006C9
      blacklist += [0x004017C8] # 0x00000000 → 0x000006C9
      blacklist += [0x004017CC] # 0x00000000 → 0x000006C9
      blacklist += [0x004017D0] # 0x00000000 → 0x000006C9
      blacklist += [0x004017D4] # 0x00000000 → 0x000006C9
      blacklist += [0x004017D8] # 0x00000000 → 0x000006C9
      blacklist += [0x004017DC] # 0x00000000 → 0x000006C9
      blacklist += [0x004017E0] # 0x00000000 → 0x000006C9
      blacklist += [0x004017E4] # 0x00000000 → 0x000006C9
      blacklist += [0x004017E8] # 0x00000000 → 0x000006C9
      blacklist += [0x004017EC] # 0x00000000 → 0x000006C9
      blacklist += [0x004017F0] # 0x00000000 → 0x000006C9
      blacklist += [0x004017F4] # 0x00000000 → 0x000006C9
      blacklist += [0x004017F8] # 0x00000000 → 0x000006C9
      blacklist += [0x004017FC] # 0x00000000 → 0x000006C9
      #blacklist += [0x0040186C] # 0x00000000 → 0xFF000000 # CLEAR COLOR
      blacklist += [0x0040196C] # 0x00000000 → 0xFF000000
      blacklist += [0x00401C6C] # 0x00000000 → 0xFF000000
      blacklist += [0x00401D6C] # 0x00000000 → 0xFF000000

      for i in range(len(pgraph_dump) // 4):
        off = 0x00400000 + i * 4
        if off in blacklist:
          continue
        word = struct.unpack_from("<L", pgraph_dump, i * 4)[0]
        new_word = struct.unpack_from("<L", new_pgraph_dump, i * 4)[0]
        if new_word != word:
          addHTML(["", "", "", "", "Modified 0x%08X in PGRAPH: 0x%08X &rarr; 0x%08X" % (off, word, new_word)])
      pgraph_dump = None
      addHTML(["", "", "", "", "Finished PGRAPH comparison"])

    return []





  def updateSurfaceClipX(self, data):
    global surface_clip_x
    surface_clip_x = data

  def updateSurfaceClipY(self, data):
    global surface_clip_y
    surface_clip_y = data

  def updateSurfaceFormat(self, data):
    print("Changing surface format")
    # Anti-aliasing in 0x00400710

  def updateSurfacePitch(self, data):
    print("Changing surface pitch")
    # 0x00400858 and 0x0040085C in pgraph

  def updateSurfaceAddress(self, data):
    global color_offset
    print("Changing color surface address")
    #FIXME: Mabye in PGRAPH: 0x00400828 ? [modified by command]
    color_offset = data

  def HandleFlipStall(self, xbox, data, *args):
    print("Flip (Stall)")
    self.flipStallCount += 1
    return []

  def HandleSetTexture(self, xbox, data, *args):
    pass
    #FIXME: Dump texture here?
















  def filterPGRAPHMethod(self, xbox, method):
    # Do callback for pre-method
    if method in self.method_callbacks:
      return self.method_callbacks[method]
    return [], []
    

  def recordPGRAPHMethod(self, xbox, method_info, data, pre_info, post_info):
    dataf = struct.unpack("<f", struct.pack("<L", data))[0]

    addHTML(["", "0x%08X" % method_info['address'], "0x%04X" % method_info['method'], "0x%08X / %f" % (data, dataf)] + pre_info + post_info)











  def __init__(self, dma_get_addr, dma_put_addr):
    self.flipStallCount = 0
    self.commandCount = 0

    self.real_dma_get_addr = dma_get_addr
    self.real_dma_put_addr = dma_put_addr
    self.target_dma_put_addr = dma_get_addr


    self.method_callbacks = {}

    self.methodHooks(0x97, 0x1D94, [],                 [self.DumpSurfaces])    # CLEAR
    self.methodHooks(0x97, 0x17FC, [self.HandleBegin], [self.HandleEnd])       # BEGIN_END

    # Check for texture address changes
    #for i in range(4):
    #  methodHooks(0x1B00 + 64 * i, [],    [HandleSetTexture], i)

    # Add the list of commands which might trigger CPU actions
    self.methodHooks(0x97, 0x0130, [],                 [self.HandleFlipStall]) # FLIP_STALL
    self.methodHooks(0x97, 0x1D70, [],                 [self.DumpSurfaces])    # BACK_END_WRITE_SEMAPHORE_RELEASE

  

  def WritePUT(self, xbox, target):

    prev_target = self.target_dma_put_addr
    prev_real = self.real_dma_put_addr

    real = exchange_u32(xbox, dma_put_addr, target)
    self.target_dma_put_addr = target

    # It must point where we pointed previously, otherwise something is broken
    if (real != prev_target):
      html_print("New real PUT (0x%08X -> 0x%08X) while changing hook 0x%08X -> 0x%08X" % (prev_real, real, prev_target, target))
      s1 = xbox.read_u32(put_state)
      if s1 & 1:
        print("PUT was modified and pusher was already active!")
        time.sleep(60.0)
      self.real_dma_put_addr = real
      #traceback.print_stack()



  def run_fifo(self, xbox, xbox_helper, put_target):
    global DebugPrint

    # Queue the commands
    self.WritePUT(xbox, put_target)

    #FIXME: we can avoid this read in some cases, as we should know where we are
    self.real_dma_get_addr = xbox.read_u32(dma_get_addr)


    addHTML(["WARNING", "Running FIFO (GET: 0x%08X -- PUT: 0x%08X / 0x%08X)" % (self.real_dma_get_addr, put_target, self.real_dma_put_addr)])

    # Loop while this command is being ran.
    # This is necessary because a whole command might not fit into CACHE.
    # So we have to process it chunk by chunk.
    command_base = self.real_dma_get_addr
    #FIXME: This used to be a check which made sure that `v_dma_get_addr` did
    #       never leave the known PB.
    while self.real_dma_get_addr != put_target:
      if DebugPrint: print("At 0x%08X, target is 0x%08X (Real: 0x%08X)" % (self.real_dma_get_addr, put_target, self.real_dma_put_addr))

      # Disable PGRAPH, so it can't run anything from CACHE.
      xbox_helper.disable_pgraph_fifo()
      xbox_helper.wait_until_pgraph_idle()

      # This scope should be atomic.
      if True:

        # Avoid running bad code, if the PUT was modified sometime during
        # this command.
        self.WritePUT(xbox, self.target_dma_put_addr)

        # Kick commands into CACHE.
        kick_fifo(xbox, self.target_dma_put_addr)

        #print("PUT STATE 0x%08X" % xbox.read_u32(0xFD003220))


      # Run the commands we have moved to CACHE, by enabling PGRAPH.
      xbox_helper.enable_pgraph_fifo()

      # Get the updated PB address.
      self.real_dma_get_addr = xbox.read_u32(dma_get_addr)

    # This is just to confirm that nothing was modified in the final chunk
    self.WritePUT(xbox, self.target_dma_put_addr)

    return







  def parsePushBufferCommand(self, xbox, get_addr):
    global DebugPrint

    # Retrieve command type from Xbox
    word = xbox.read_u32(0x80000000 | get_addr)
    addHTML(["", "", "", "@0x%08X: DATA: 0x%08X" % (get_addr, word)])

    #FIXME: Get where this command ends
    next_parser_addr = parseCommand(get_addr, word, DebugPrint)

    # If we don't know where this command ends, we have to abort.
    if next_parser_addr == 0:
      return None, 0


    # Check which method it is.
    if ((word & 0xe0030003) == 0) or ((word & 0xe0030003) == 0x40000000):
      # methods
      method = word & 0x1fff;
      subchannel = (word >> 13) & 7;
      method_count = (word >> 18) & 0x7ff;
      method_nonincreasing = word & 0x40000000;

      # Download this command from Xbox
      #FIXME: Halo: CE has cases where method_count is 0?!
      command = xbox.read(0x80000000 | (get_addr + 4), method_count * 4)
      
      #FIXME: Unpack all of them?
      data = struct.unpack("<%dL" % method_count, command)
      assert(len(data) == method_count)

      method_info = {}
      method_info['address'] = get_addr
      method_info['method'] = method
      method_info['nonincreasing'] = method_nonincreasing
      method_info['subchannel'] = subchannel
      method_info['data'] = data
    else:
      method_info = None

    return method_info, next_parser_addr

  def filterPushBufferCommand(self, xbox, method_info):

    pre_callbacks = []
    post_callbacks = []

    method = method_info['method']
    for data in method_info['data']:
      pre_callbacks_this, post_callbacks_this = self.filterPGRAPHMethod(xbox, method)

      # Queue the callbacks
      pre_callbacks += pre_callbacks_this
      post_callbacks += post_callbacks_this

      if not method_info['nonincreasing']:
        method += 4

    return pre_callbacks, post_callbacks


  def recordPushBufferCommand(self, xbox, address, method_info, pre_info, post_info):
    orig_method = method_info['method']

    # Put info in debug HTML
    addHTML(["%d" % self.commandCount, "%s" % method_info])
    for data in method_info['data']:

      self.recordPGRAPHMethod(xbox, method_info, data, pre_info, post_info)

      if not method_info['nonincreasing']:
        method_info['method'] += 4

    #FIXME: Is this necessary? are dicts passed by value in python?
    method_info['method'] = orig_method

    self.commandCount += 1

    return


  def processPushBufferCommand(self, xbox, xbox_helper, parser_addr):
    parser_addr

    addHTML(["WARNING", "Starting FIFO parsing from 0x%08X -- 0x%08X" % (parser_addr, self.real_dma_put_addr)])


    if parser_addr == self.real_dma_put_addr:
      unprocessed_bytes = 0
    else:

      # Filter commands and check where it wants to go to
      method_info, post_addr = self.parsePushBufferCommand(xbox, parser_addr)

      # We have a problem if we can't tell where to go next
      assert(post_addr != 0)

      # If we have a method, work with it
      if method_info is None:

        addHTML(["WARNING", "No method. Going to 0x%08X" % post_addr])
        unprocessed_bytes = 4

      else:

        # Check what method this is
        pre_callbacks, post_callbacks = self.filterPushBufferCommand(xbox, method_info)

        # Count number of bytes in instruction
        unprocessed_bytes = 4 * (1 + len(method_info['data']))

        # Go where we can do pre-callback
        pre_info = []
        if len(pre_callbacks) > 0:
        
          # Go where we want to go
          self.run_fifo(xbox, xbox_helper, parser_addr)

          # Do the pre callbacks before running the command
          #FIXME: assert we are where we wanted to be
          for callback in pre_callbacks:
            pre_info += callback(xbox, method_info['data'][0])


        # Go where we can do post-callback
        post_info = []
        if len(post_callbacks) > 0:

          # If we reached target, we can't step again without leaving valid buffer
          assert(parser_addr != self.real_dma_put_addr)

          # Go where we want to go (equivalent to step)
          self.run_fifo(xbox, xbox_helper, post_addr)

          # We have processed all bytes now
          unprocessed_bytes = 0

          # Do all post callbacks
          for callback in post_callbacks:
            post_info += callback(xbox, method_info['data'][0])


        # Add the pushbuffer command to log
        self.recordPushBufferCommand(xbox, parser_addr, method_info, pre_info, post_info)


      # Move parser to the next instruction
      parser_addr = post_addr

    addHTML(["WARNING", "Sucessfully finished FIFO parsing 0x%08X -- 0x%08X (%d bytes unprocessed)" % (parser_addr, self.real_dma_put_addr, unprocessed_bytes)])

    return parser_addr, unprocessed_bytes

  def recordedFlipStallCount(self):
    return self.flipStallCount

  def recordedPushBufferCommandCount(self):
    return self.commandCount














  def methodHooks(self, obj, method, pre_hooks, post_hooks, user = None):
    print("Registering method hook for 0x%04X" % method)
    self.method_callbacks[method] = (pre_hooks, post_hooks)
    return





