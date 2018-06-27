#FIXME: Move to xboxpy.NV2A.PGRAPH.Texture

from xboxpy.xboxpy import nv2a

import struct
from PIL import Image

def dumpTexture(xbox, offset, pitch, fmt_color, width, height):
  img = None

  #FIXME: Why not use the one from the CLI?!
  bits_per_pixel = 0
  auto_pitch = 0


  if fmt_color == 4:
    pass #FIXME!


  elif fmt_color == 5:
    auto_pitch = width * 2
    bits_per_pixel = 16
    img = Image.new( 'RGB', (width, height))
    swizzled = True
  elif fmt_color == 6:
    auto_pitch = width * 4
    bits_per_pixel = 32
    img = Image.new( 'RGBA', (width, height))
    swizzled = True
  elif fmt_color == 7:
    auto_pitch = width * 4
    bits_per_pixel = 32
    img = Image.new( 'RGB', (width, height))
    swizzled = True


  elif fmt_color == 0xB:
    pass #FIXME!


  elif fmt_color == 0xC: # DXT1
    img = Image.new( 'RGB', (width, height))
    auto_pitch = width // 2
    bits_per_pixel = 4
    swizzled = False
  elif fmt_color == 0xF: # DXT5
    img = Image.new( 'RGBA', (width, height))
    auto_pitch = width * 1
    bits_per_pixel = 8
    swizzled = False
  elif fmt_color == 0x11:
    img = Image.new( 'RGB', (width, height))
    auto_pitch = width * 2
    bits_per_pixel = 16
    swizzled = False
  elif fmt_color == 0x12:
    auto_pitch = width * 4
    bits_per_pixel = 32
    img = Image.new( 'RGBA', (width, height))
    swizzled = False
  elif fmt_color == 0x1E:
    auto_pitch = width * 4
    bits_per_pixel = 32
    img = Image.new( 'RGB', (width, height))
    swizzled = False


  elif fmt_color == 0x2E:
    pass #FIXME!


  elif fmt_color == 0x30:
    pass #FIXME!


  elif fmt_color == 0x31:
    pass #FIXME!


  else:
    print("\n\nUnknown texture format: 0x%X\n\n" % fmt_color)
    raise Exception("lolz")
    return

  if pitch == 0:
    pitch = auto_pitch

  if img != None:

    #FIXME: Might want to skip the empty area if pitch and width diverge?
    data = xbox.read(0x80000000 | offset, pitch * height)

    if img == None:

      pass #FIXME: Save raw data to disk

    else:

      if swizzled:
        if width == 640 and height <= 480 and pitch == 2560:
          data = nv2a.Unswizzle(data, bits_per_pixel, (width, height), pitch)
        else:
          data = nv2a._Unswizzle(data, bits_per_pixel, (width, height), pitch)
      
      pixels = img.load() # create the pixel map

      if fmt_color == 0x6 or fmt_color == 0x7 or fmt_color == 0x12 or fmt_color == 0x1E:
        for x in range(img.size[0]):    # for every col:
          for y in range(img.size[1]):    # For every row
            blue = data[(y * pitch + x * 4) + 0]
            green = data[(y * pitch + x * 4) + 1]
            red = data[(y * pitch + x * 4) + 2]
            if fmt_color == 0x7 or fmt_color == 0x1E:
              pixels[x, y] = (red, green, blue)
            else:
              alpha = data[(y * pitch + x * 4) + 3]
              pixels[x, y] = (red, green, blue, alpha) # set the colour accordingly

      elif fmt_color == 0xC:
        img = Image.frombytes("RGBA", img.size, data, 'bcn', 1) # DXT1

      #FIXME:   'dxt3': ('bcn', 2),

      elif fmt_color == 0xF:
        img = Image.frombytes("RGBA", img.size, data, 'bcn', 3) # DXT5

      elif fmt_color == 0x5 or fmt_color == 0x11:
        for x in range(img.size[0]):    # for every col:
          for y in range(img.size[1]):    # For every row
            pixel = struct.unpack_from("<H", data, y * pitch + 2 * x)[0]
            blue = (pixel >> 11) & 0x1F
            green = (pixel >> 5) & 0x3F
            red = pixel & 0x1F
            #FIXME: Fill lower bits with lowest bit
            pixels[x, y] = (red << 3, green << 2, blue << 3, 255) # set the colour accordingly
    
  return img

def dumpTextureUnit(xbox, i):
  offset = xbox.read_u32(0xFD401A24 + i * 4) # NV_PGRAPH_TEXOFFSET0
  pitch = 0 # xbox.read_u32(0xFD4019DC + i * 4) # NV_PGRAPH_TEXCTL1_0_IMAGE_PITCH
  fmt = xbox.read_u32(0xFD401A04 + i * 4) # NV_PGRAPH_TEXFMT0
  fmt_color = (fmt >> 8) & 0x7F
  width_shift = (fmt >> 20) & 0xF
  height_shift = (fmt >> 24) & 0xF
  width = 1 << width_shift
  height = 1 << height_shift
  print("Texture %d [0x%08X, %d x %d (pitch: 0x%X), format %d]" % (i, offset, width, height, pitch, fmt_color))
  img = dumpTexture(xbox, offset, pitch, fmt_color, width, height)
  return img
    

