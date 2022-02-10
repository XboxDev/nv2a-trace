"""Provides functions for manipulating xbox textures."""

# pylint: disable=consider-using-f-string
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements

# FIXME: Move to xboxpy.NV2A.PGRAPH.Texture

from collections import namedtuple
from PIL import Image

from Xbox import Xbox
import XboxHelper
from xboxpy import nv2a

# Value that may be added to contiguous memory addresses to access as ADDR_AGPMEM, which
# is guaranteed to be linear (and thus may be slower than tiled ADDR_FBMEM but can be
# manipulated directly).
AGP_MEMORY_BASE = 0xF0000000

TextureParameters = namedtuple(
    "TextureParameters",
    [
        "width",
        "height",
        "color_pitch",
        "color_offset",
        "format_color",
        "depth_pitch",
        "depth_offset",
        "format_depth",
        "surface_type",
        "swizzle_unk",
        "swizzle_unk2",
        "swizzled",
    ],
)

# Right hand side is always in RGB or RGBA channel order.
TextureDescription = namedtuple(
    "TextureDescription", ["bpp", "channel_bpps", "channel_offsets"]
)
Y8 = TextureDescription(8, (8, 8, 8), (0, 0, 0))
AY8 = TextureDescription(8, (8, 8, 8, 8), (0, 0, 0, 0))
A8 = TextureDescription(8, (0, 0, 0, 8), (0, 0, 0, 0))
A8Y8 = TextureDescription(16, (8, 8, 8, 8), (0, 0, 0, 8))
R5G6B5 = TextureDescription(16, (5, 6, 5), (11, 5, 0))
A4R4G4B4 = TextureDescription(16, (4, 4, 4, 4), (8, 4, 0, 12))
A1R5G5B5 = TextureDescription(16, (5, 5, 5, 1), (10, 5, 0, 15))
X1R5G5B5 = TextureDescription(16, (5, 5, 5), (10, 5, 0))
A8R8G8B8 = TextureDescription(32, (8, 8, 8, 8), (16, 8, 0, 24))
X8R8G8B8 = TextureDescription(32, (8, 8, 8), (16, 8, 0))


def _decode_texture(
    data, size, pitch, swizzled, bits_per_pixel, channel_sizes, channel_offsets
):
    """Convert the given texture data into a PIL.Image."""

    # Check argument sanity
    assert len(size) == 2  # FIXME: Support 1D and 3D?
    assert len(channel_offsets) == len(channel_sizes)

    # Helper function to extract integer at bit offset with bit size
    def get_bits(bits, offset, length):
        mask = (1 << length) - 1
        return (bits >> offset) & mask

    width = size[0]
    height = size[1]

    if len(channel_sizes) == 3:
        mode = "RGB"
    elif len(channel_sizes) == 4:
        mode = "RGBA"
    else:
        raise Exception("Unsupported channel_sizes %d" % len(channel_sizes))

    img = Image.new(mode, (width, height))

    # TODO: Is unswizzling actually necessary if textures are read via AGP?
    # Need to set up a swizzled test case and verify behavior.

    # FIXME: Unswizzle data on the fly instead
    if swizzled:
        data = nv2a.Unswizzle(data, bits_per_pixel, (width, height), pitch)

    pixels = img.load()  # create the pixel map

    assert bits_per_pixel % 8 == 0

    for y in range(height):
        for x in range(width):

            pixel_offset = y * pitch + x * bits_per_pixel // 8
            pixel_bytes = data[pixel_offset : pixel_offset + bits_per_pixel // 8]
            pixel_bits = int.from_bytes(pixel_bytes, byteorder="little")

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
    """Convert nv2a draw format to the equivalent Texture format."""
    if fmt == 0x3:  # ARGB1555
        return 0x3 if swizzled else 0x1C

    if fmt == 0x5:  # RGB565
        return 0x5 if swizzled else 0x11

    if fmt in [0x7, 0x08]:  # XRGB8888
        return 0x7 if swizzled else 0x1E

    if fmt == 0xC:  # ARGB8888
        return 0x6 if swizzled else 0x12

    raise Exception(
        "Unknown color fmt %d (0x%X) %s"
        % (fmt, fmt, "swizzled" if swizzled else "unswizzled")
    )


def surface_zeta_format_to_texture_format(fmt, swizzled, is_float):
    """Convert nv2a zeta format to the equivalent Texture format."""
    if fmt == 0x1:  # Z16
        if is_float:
            return 0x2D if swizzled else 0x31
        return 0x2C if swizzled else 0x30

    if fmt == 0x2:  # Z24S8
        if is_float:
            return 0x2B if swizzled else 0x2F
        return 0x2A if swizzled else 0x2E

    raise Exception(
        "Unknown zeta fmt %d (0x%X) %s %s"
        % (
            fmt,
            fmt,
            "float" if is_float else "fixed",
            "swizzled" if swizzled else "unswizzled",
        )
    )


def read_texture_parameters(xbox: Xbox) -> TextureParameters:
    """Reads the current texture state"""
    color_pitch = xbox.read_u32(0xFD400858)
    depth_pitch = xbox.read_u32(0xFD40085C)

    color_offset = xbox.read_u32(0xFD400828)
    depth_offset = xbox.read_u32(0xFD40082C)

    color_base = xbox.read_u32(0xFD400840)
    depth_base = xbox.read_u32(0xFD400844)

    # FIXME: Is this correct? pbkit uses _base, but D3D seems to use _offset?
    color_offset += color_base
    depth_offset += depth_base

    surface_clip_x = xbox.read_u32(0xFD4019B4)
    surface_clip_y = xbox.read_u32(0xFD4019B8)

    draw_format = xbox.read_u32(0xFD400804)
    surface_type = xbox.read_u32(0xFD400710)
    swizzle_unk = xbox.read_u32(0xFD400818)

    swizzle_unk2 = xbox.read_u32(0xFD40086C)

    clip_x = (surface_clip_x >> 0) & 0xFFFF
    clip_y = (surface_clip_y >> 0) & 0xFFFF

    clip_w = (surface_clip_x >> 16) & 0xFFFF
    clip_h = (surface_clip_y >> 16) & 0xFFFF

    surface_anti_aliasing = (surface_type >> 4) & 3

    clip_x, clip_y = XboxHelper.apply_anti_aliasing_factor(
        surface_anti_aliasing, clip_x, clip_y
    )
    clip_w, clip_h = XboxHelper.apply_anti_aliasing_factor(
        surface_anti_aliasing, clip_w, clip_h
    )

    width = clip_x + clip_w
    height = clip_y + clip_h

    # FIXME: 128 x 128 [pitch = 256 (0x100)], at 0x01AA8000 [PGRAPH: 0x01AA8000?], format 0x5, type: 0x21000002, swizzle: 0x7070000 [used 0]

    # FIXME: This does not seem to be a good field for this
    # FIXME: Patched to give 50% of coolness
    swizzled = (surface_type & 3) == 2
    # FIXME: if surface_type is 0, we probably can't even draw..

    format_color = (draw_format >> 12) & 0xF
    # FIXME: Support 3D surfaces.
    _format_depth_buffer = (draw_format >> 18) & 0x3

    if not format_color:
        fmt_color = None
    else:
        fmt_color = surface_color_format_to_texture_format(format_color, swizzled)
    # TODO: Extract swizzle and float state.
    # fmt_depth = surface_zeta_format_to_texture_format(format_depth_buffer)

    return TextureParameters(
        width=width,
        height=height,
        color_pitch=color_pitch,
        color_offset=color_offset,
        format_color=fmt_color,
        depth_pitch=depth_pitch,
        depth_offset=depth_offset,
        format_depth=None,
        surface_type=surface_type,
        swizzle_unk=swizzle_unk,
        swizzle_unk2=swizzle_unk2,
        swizzled=swizzled,
    )


def dump_texture(xbox, offset, pitch, fmt_color, width, height):
    """Convert the texture at the given offset into a PIL.Image."""
    img = None

    if fmt_color == 0x0:
        tex_info = (True, Y8)
    elif fmt_color == 0x1:
        tex_info = (True, AY8)
    elif fmt_color == 0x2:
        tex_info = (True, A1R5G5B5)
    elif fmt_color == 0x3:
        tex_info = (True, X1R5G5B5)
    elif fmt_color == 0x4:
        tex_info = (True, A4R4G4B4)
    elif fmt_color == 0x5:
        tex_info = (True, R5G6B5)
    elif fmt_color == 0x6:
        tex_info = (True, A8R8G8B8)
    elif fmt_color == 0x7:
        tex_info = (True, X8R8G8B8)
    elif fmt_color == 0xB:
        img = Image.new(
            "RGB", (width, height), (255, 0, 255, 255)
        )  # FIXME! Palette mode!
    elif fmt_color == 0xC:  # DXT1
        data = xbox.read(AGP_MEMORY_BASE | offset, width * height // 2)
        img = Image.frombytes("RGBA", (width, height), data, "bcn", 1)  # DXT1
    elif fmt_color == 0xE:  # DXT3
        data = xbox.read(AGP_MEMORY_BASE | offset, width * height * 1)
        img = Image.frombytes("RGBA", (width, height), data, "bcn", 2)  # DXT3
    elif fmt_color == 0xF:  # DXT5
        data = xbox.read(AGP_MEMORY_BASE | offset, width * height * 1)
        img = Image.frombytes("RGBA", (width, height), data, "bcn", 3)  # DXT5
    elif fmt_color == 0x10:
        tex_info = (False, A1R5G5B5)
    elif fmt_color == 0x11:
        tex_info = (False, R5G6B5)
    elif fmt_color == 0x12:
        tex_info = (False, A8R8G8B8)
    elif fmt_color == 0x19:
        tex_info = (True, A8)
    elif fmt_color == 0x1A:
        tex_info = (True, A8Y8)
    elif fmt_color == 0x1C:
        tex_info = (False, X1R5G5B5)
    elif fmt_color == 0x1D:
        tex_info = (False, A4R4G4B4)
    elif fmt_color == 0x1E:
        tex_info = (False, X8R8G8B8)
    elif fmt_color == 0x2E:
        img = Image.new(
            "RGB", (width, height), (255, 0, 255, 255)
        )  # FIXME! Depth format
    elif fmt_color == 0x30:
        img = Image.new(
            "RGB", (width, height), (255, 0, 255, 255)
        )  # FIXME! Depth format
    elif fmt_color == 0x31:
        img = Image.new(
            "RGB", (width, height), (255, 0, 255, 255)
        )  # FIXME! Depth format
    else:
        raise Exception("Unknown texture format: 0x%X" % fmt_color)

    # Some formats might have been parsed already
    if img is None:

        swizzled = tex_info[0]
        format_info = tex_info[1]

        # Parse format info
        bits_per_pixel, channel_sizes, channel_offsets = format_info

        # FIXME: Avoid this nasty ~~convience feature~~ hack
        if pitch == 0:
            pitch = width * bits_per_pixel // 8

        # FIXME: Might want to skip the empty area if pitch and width diverge?
        data = xbox.read(AGP_MEMORY_BASE | offset, pitch * height)
        img = _decode_texture(
            data,
            (width, height),
            pitch,
            swizzled,
            bits_per_pixel,
            channel_sizes,
            channel_offsets,
        )

    return img
