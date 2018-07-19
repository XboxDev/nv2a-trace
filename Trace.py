import os
import struct

import Texture

StateDumping = True

commandCount = 0
flipStallCount = 0


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

color_offset = 0
surface_clip_x = 0
surface_clip_y = 0
surface_pitch = 0

pgraph_dump = None

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


def recordPGRAPHMethod(xbox, method, data):
  global pgraph_dump
  global color_offset
  global surface_clip_x
  global surface_clip_y
  global commandCount
  global flipStallCount

  extraHTML = []

  if method == 0x0100:
    print("No operation, data: 0x%08X!" % data)

  if method == 0x0130:
    print("Flip stall!")
    flipStallCount += 1

  if method == 0x1d8c:
    print("Zeta clear value!")

  if method == 0x1d90:
    pgraph_dump = dumpPGRAPH(xbox)
    print("Color clear value!")

  #FIXME: This shouldn't be necessary, but I can't find this address in PGRAPH
  if method == 0x0200:
    #pgraph_dump = dumpPGRAPH(xbox)
    print("Changing surface clip x")
    surface_clip_x = data
  if method == 0x0204:
    #pgraph_dump = dumpPGRAPH(xbox)
    print("Changing surface clip y")
    surface_clip_y = data
  if method == 0x0208:
    print("Changing surface format")
    # Anti-aliasing in 0x00400710
  if method == 0x020c:
    #pgraph_dump = dumpPGRAPH(xbox)
    print("Changing surface pitch")
    # 0x00400858 and 0x0040085C in pgraph
  if method == 0x0210:
    #pgraph_dump = dumpPGRAPH(xbox)
    print("Changing color surface address")
    #FIXME: Mabye in PGRAPH: 0x00400828 ? [modified by command]
    color_offset = data

  if method == 0x17fc:
    if StateDumping:
      print("Set begin end")
      if data != 0:
        # Dump textures
        for i in range(4):
          path = "command%d--tex_%d.png" % (commandCount, i)
          img = Texture.dumpTextureUnit(xbox, i)
          if img != None:
            img.save(os.path.join("out", path))
          extraHTML += ['<img height="128px" src="%s" alt="%s"/>' % (path, path)]
      else:
        # Dump finished surface
        if True:
          
          offset = color_offset
          pitch = xbox.read_u32(0xFD400858) # FIXME: Read from PGRAPH
          #FIXME: Poor var names

          surface_color_offset = xbox.read_u32(0xFD400828)
          surface_clip_x = xbox.read_u32(0xFD4019B4)
          surface_clip_y = xbox.read_u32(0xFD4019B8)

          offset = surface_color_offset

          draw_format = xbox.read_u32(0xFD400804)
          surface_type = xbox.read_u32(0xFD400710)
          swizzle_unk = xbox.read_u32(0xFD400818)

          #FIXME: This does not seem to be a good field for this
          #FIXME: Patched to give 50% of coolness
          swizzled = commandCount & 1 #((surface_type & 3) == 1)
          #FIXME: if surface_type is 0, we probably can't even draw..

          color_fmt = (draw_format >> 12) & 0xF
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

          width = (surface_clip_x >> 16) & 0xFFFF
          height = (surface_clip_y >> 16) & 0xFFFF

          #FIXME: Respect anti-aliasing

          path = "command%d--color.png" % (commandCount)
          extraHTML += ['<img height="128px" src="%s" alt="%s"/>' % (path, path)]
          extraHTML += ['%d x %d [pitch = %d (0x%X)], at 0x%08X [PGRAPH: 0x%08X?], format 0x%X, type: 0x%X, swizzle: 0x%X [used %d]' % (width, height, pitch, pitch, offset, surface_color_offset, color_fmt, surface_type, swizzle_unk, swizzled)]
          print(extraHTML[-1])

          img = Texture.dumpTexture(xbox, offset, pitch, fmt_color, width, height)
          if img != None:

            # Hack to remove alpha channel
            if True:
              img = img.convert('RGB')

            img.save(os.path.join("out", path))

  # Check for texture address changes
  for i in range(4):
    if method == 0x1b00 + 64 * i:
      print("Texture %d [0x%08X]" % (i, data))

  addHTML(["", "0x%04X" % method, "0x%08X" % data] + extraHTML)

def recordPushBufferCommand(xbox, v_dma_get_addr):
  global commandCount
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

  # Retrieve command type from Xbox
  word = xbox.read_u32(0x80000000 | v_dma_get_addr)

  # Put info in debug HTML
  addHTML(["%d" % commandCount, "0x%08X" % word])

  # Check which method it is.
  if ((word & 0xe0030003) == 0) or ((word & 0xe0030003) == 0x40000000):
    # methods
    method = word & 0x1fff;
    subchannel = (word >> 13) & 7;
    method_count = (word >> 18) & 0x7ff;
    method_nonincreasing = word & 0x40000000;

    # Download this command from Xbox
    command = xbox.read(0x80000000 | (v_dma_get_addr + 4), method_count * 4)
    
    for method_index in range(method_count):

      data = struct.unpack_from("<L", command, method_index * 4)[0]
      recordPGRAPHMethod(xbox, method, data)
      
      if not method_nonincreasing:
        method += 4

  if pgraph_dump != None:
    addHTML(["", "", "", "", "Dumped PGRAPH for later"])

  commandCount += 1

def recordedFlipStallCount():
  global flipStallCount
  return flipStallCount

def recordedPushBufferCommandCount():
  global commandCount
  return commandCount
