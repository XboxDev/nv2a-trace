#FIXME: Move to xboxpy.NV2A.PGRAPH.Texture

from xboxpy import nv2a

import struct
from PIL import Image

def decodeTexture(data, size, pitch, swizzled, bits_per_pixel, channel_sizes, channel_offsets):

  # Check argument sanity
  assert(len(size) == 2) #FIXME: Support 1D and 3D?
  assert(len(channel_offsets) == len(channel_sizes))

  # Helper function to extract integer at bit offset with bit size
  def get_bits(bits, offset, length):
    mask = (1 << length) - 1
    return(bits >> offset) & mask

  width = size[0]
  height = size[1]

  if (len(channel_sizes) == 3):
    mode = 'RGB'
  elif (len(channel_sizes) == 4):
    mode = 'RGBA'

  img = Image.new(mode, (width, height))

  #FIXME: Unswizzle data on the fly instead
  if swizzled:
    data = nv2a.Unswizzle(data, bits_per_pixel, (width, height), pitch)

  pixels = img.load() # create the pixel map

  assert(bits_per_pixel % 8 == 0)

  for y in range(height):
    for x in range(width):

      pixel_offset = y * pitch + x * bits_per_pixel // 8
      pixel_bytes = data[pixel_offset:pixel_offset + bits_per_pixel // 8]
      pixel_bits = int.from_bytes(pixel_bytes, byteorder='little')

      pixel_channels = ()
      for channel_offset, channel_size in zip(channel_offsets, channel_sizes):
        channel_value = get_bits(pixel_bits, channel_offset, channel_size)

        # Normalize channel
        if channel_size > 0:
          channel_value /= (1 << channel_size) - 1
          channel_value = int(channel_value * 0xFF)
        else:
          channel_value = 0x00

        pixel_channels += (channel_value,)
      pixels[x, y] = pixel_channels

  return img

      
def surface_color_format_to_texture_format(fmt, swizzled):
  if fmt == 0x3: # ARGB1555
    return 0x3 if swizzled else 0x1C
  elif fmt == 0x5: # RGB565
    return 0x5 if swizzled else 0x11
  elif fmt == 0x7 or fmt == 0x8: # XRGB8888
    return 0x7 if swizzled else 0x1E
  elif fmt == 0xC: # ARGB8888
    return 0x6 if swizzled else 0x12
  else:
    raise Exception("Unknown color fmt %d (0x%X) %s" % (fmt, fmt, "swizzled" if swizzled else "unswizzled"))
    return None


def surface_zeta_format_to_texture_format(fmt, swizzled, is_float):
  if fmt == 0x1: # Z16
    if is_float:
      return 0x2D if swizzled else 0x31
    else:
      return 0x2C if swizzled else 0x30
  elif fmt == 0x2: # Z24S8
    if is_float:
      return 0x2B if swizzled else 0x2F
    else:
      return 0x2A if swizzled else 0x2E
  else:
    raise Exception("Unknown zeta fmt %d (0x%X) %s %s" % (fmt, fmt, "float" if is_float else "fixed", "swizzled" if swizzled else "unswizzled"))
    return None


def dumpTexture(xbox, offset, pitch, fmt_color, width, height):
  img = None

  # bits per pixel, channel sizes, channel offsets.
  # Right hand side is always in RGB or RGBA channel order.
  Y8 = (8, (8, 8, 8), (0, 0, 0))
  AY8 = (8, (8, 8, 8, 8), (0, 0, 0, 0))
  A8 = (8, (0, 0, 0, 8), (0, 0, 0, 0))
  A8Y8 = (16, (8, 8, 8, 8), (0, 0, 0, 8))
  R5G6B5 = (16, (5,6,5), (11, 5, 0))
  A4R4G4B4 = (16, (4,4,4,4), (8, 4, 0, 12))
  A1R5G5B5 = (16, (5,5,5,1), (10, 5, 0, 15))
  X1R5G5B5 = (16, (5,5,5), (10, 5, 0))
  A8R8G8B8 = (32, (8,8,8,8), (16, 8, 0, 24))
  X8R8G8B8 = (32, (8,8,8), (16, 8, 0))

  if fmt_color == 0x0: tex_info = (True, Y8)
  elif fmt_color == 0x1: tex_info = (True, AY8)
  elif fmt_color == 0x2: tex_info = (True, A1R5G5B5)
  elif fmt_color == 0x3: tex_info = (True, X1R5G5B5)
  elif fmt_color == 0x4: tex_info = (True, A4R4G4B4)
  elif fmt_color == 0x5: tex_info = (True, R5G6B5)
  elif fmt_color == 0x6: tex_info = (True, A8R8G8B8)
  elif fmt_color == 0x7: tex_info = (True, X8R8G8B8)
  elif fmt_color == 0xB: img = Image.new('RGB', (width, height), (255, 0, 255, 255)) #FIXME! Palette mode!
  elif fmt_color == 0xC: # DXT1
    data = xbox.read(0x80000000 | offset, width * height // 2)
    img = Image.frombytes('RGBA', (width, height), data, 'bcn', 1) # DXT1
  elif fmt_color == 0xE: # DXT3
    data = xbox.read(0x80000000 | offset, width * height * 1)
    img = Image.frombytes('RGBA', (width, height), data, 'bcn', 2) # DXT3
  elif fmt_color == 0xF: # DXT5
    data = xbox.read(0x80000000 | offset, width * height * 1)
    img = Image.frombytes('RGBA', (width, height), data, 'bcn', 3) # DXT5
  elif fmt_color == 0x10: tex_info = (False, A1R5G5B5A5)
  elif fmt_color == 0x11: tex_info = (False, R5G6B5)
  elif fmt_color == 0x12: tex_info = (False, A8R8G8B8)
  elif fmt_color == 0x19: tex_info = (True, A8)
  elif fmt_color == 0x1A: tex_info = (True, A8Y8)
  elif fmt_color == 0x1C: tex_info = (False, X1R5G5B5)
  elif fmt_color == 0x1D: tex_info = (False, A4R4G4B4)
  elif fmt_color == 0x1E: tex_info = (False, X8R8G8B8)
  elif fmt_color == 0x2E: img = Image.new('RGB', (width, height), (255, 0, 255, 255)) #FIXME! Depth format
  elif fmt_color == 0x30: img = Image.new('RGB', (width, height), (255, 0, 255, 255)) #FIXME! Depth format
  elif fmt_color == 0x31: img = Image.new('RGB', (width, height), (255, 0, 255, 255)) #FIXME! Depth format
  else:
    raise Exception("Unknown texture format: 0x%X" % fmt_color)

  # Some formats might have been parsed already    
  if img == None:

    swizzled = tex_info[0]
    format_info = tex_info[1]

    # Parse format info
    bits_per_pixel, channel_sizes, channel_offsets = format_info

    #FIXME: Avoid this nasty ~~convience feature~~ hack
    if pitch == 0:
      pitch = width * bits_per_pixel // 8

    #FIXME: Might want to skip the empty area if pitch and width diverge?
    data = xbox.read(0x80000000 | offset, pitch * height)
    img = decodeTexture(data, (width, height), pitch, swizzled, bits_per_pixel, channel_sizes, channel_offsets)

  return img
    

