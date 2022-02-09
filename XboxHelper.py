"""Various helper methods"""

# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-f-string
# pylint: disable=chained-comparison

import atexit
import time

# For general information on PFIFO, see
# https://envytools.readthedocs.io/en/latest/hw/fifo/intro.html

# mmio blocks
NV2A_MMIO_BASE = 0xFD000000
BLOCK_PMC = 0x000000
BLOCK_PBUS = 0x001000
BLOCK_PFIFO = 0x002000
BLOCK_PRMA = 0x007000
BLOCK_PVIDEO = 0x008000
BLOCK_PTIMER = 0x009000
BLOCK_PCOUNTER = 0x00A000
BLOCK_PVPE = 0x00B000
BLOCK_PTV = 0x00D000
BLOCK_PRMFB = 0x0A0000
BLOCK_PRMVIO = 0x0C0000
BLOCK_PFB = 0x100000
BLOCK_PSTRAPS = 0x101000
BLOCK_PGRAPH = 0x400000
BLOCK_PCRTC = 0x600000
BLOCK_PRMCIO = 0x601000
BLOCK_PRAMDAC = 0x680000
BLOCK_PRMDIO = 0x681000
BLOCK_PRAMIN = 0x700000
BLOCK_USER = 0x800000


def _PFIFO(addr):
    return NV2A_MMIO_BASE + BLOCK_PFIFO + addr


def _PGRAPH(addr):
    return NV2A_MMIO_BASE + BLOCK_PGRAPH + addr


# Pushbuffer state
NV_PFIFO_CACHE1_DMA_STATE = 0x00001228
DMA_STATE = _PFIFO(NV_PFIFO_CACHE1_DMA_STATE)

# Pushbuffer write address
NV_PFIFO_CACHE1_DMA_PUT = 0x00001240
DMA_PUSH_ADDR = _PFIFO(NV_PFIFO_CACHE1_DMA_PUT)

# Pushbuffer read address
NV_PFIFO_CACHE1_DMA_GET = 0x00001244
DMA_PULL_ADDR = _PFIFO(NV_PFIFO_CACHE1_DMA_GET)

NV_PFIFO_CACHE1_DMA_SUBROUTINE = 0x0000124C
DMA_SUBROUTINE = _PFIFO(NV_PFIFO_CACHE1_DMA_SUBROUTINE)

NV_PFIFO_CACHE1_PUSH0 = 0x00001200
CACHE_PUSH_MASTER_STATE = _PFIFO(NV_PFIFO_CACHE1_PUSH0)

# CACHE write state
NV_PFIFO_CACHE1_DMA_PUSH = 0x00001220
CACHE_PUSH_STATE = _PFIFO(NV_PFIFO_CACHE1_DMA_PUSH)

# CACHE read state
NV_PFIFO_CACHE1_PULL0 = 0x00001250
CACHE_PULL_STATE = _PFIFO(NV_PFIFO_CACHE1_PULL0)

# CACHE write address
NV_PFIFO_CACHE1_PUT = 0x00001210
CACHE_PUSH_ADDR = _PFIFO(NV_PFIFO_CACHE1_PUT)

# CACHE read address
NV_PFIFO_CACHE1_GET = 0x00001270
CACHE_PULL_ADDR = _PFIFO(NV_PFIFO_CACHE1_GET)

NV_PFIFO_RAMHT = 0x00000210
RAM_HASHTABLE = _PFIFO(NV_PFIFO_RAMHT)

NV_PGRAPH_CTX_SWITCH1 = 0x0000014C
CTX_SWITCH1 = _PGRAPH(NV_PGRAPH_CTX_SWITCH1)

NV_PGRAPH_FIFO = 0x00000720
PGRAPH_STATE = _PGRAPH(NV_PGRAPH_FIFO)

NV_PGRAPH_STATUS = 0x00000700
PGRAPH_STATUS = _PGRAPH(NV_PGRAPH_STATUS)


def _free_allocation(xbox, address):
    print("_free_allocation: Free'ing 0x%08X" % address)
    xbox.ke.MmFreeContiguousMemory(address)
    # Sleep to ensure the call is fully processed.
    time.sleep(0.1)
    print("_free_allocation: Freed")


def load_binary(xbox, data):
    """Loads arbitrary data into a new contiguous memory block on the xbox."""
    data_len = len(data)
    code_addr = xbox.ke.MmAllocateContiguousMemory(data_len)
    print("load_binary: Allocated %d bytes at 0x%08X" % (data_len, code_addr))

    atexit.register(_free_allocation, xbox, code_addr)
    xbox.write(code_addr, data)
    return code_addr


def parse_command(addr, word, display=False):

    prefix = "0x%08X: Opcode: 0x%08X" % (addr, word)

    if (word & 0xE0000003) == 0x20000000:
        # state->get_jmp_shadow = control->dma_get;
        # NV2A_DPRINTF("pb OLD_JMP 0x%" HWADDR_PRIx "\n", control->dma_get);
        addr = word & 0x1FFFFFFC
        print(prefix + "; old jump 0x%08X" % addr)
        return addr

    if (word & 3) == 1:
        addr = word & 0xFFFFFFFC
        print(prefix + "; jump 0x%08X" % addr)
        # state->get_jmp_shadow = control->dma_get;
        return addr

    if (word & 3) == 2:
        print(prefix + "; unhandled opcode type: call")
        # if (state->subroutine_active) {
        #  state->error = NV_PFIFO_CACHE1_DMA_STATE_ERROR_CALL;
        #  break;
        # }
        # state->subroutine_return = control->dma_get;
        # state->subroutine_active = true;
        # control->dma_get = word & 0xfffffffc;
        return 0

    if word == 0x00020000:
        # return
        print(prefix + "; unhandled opcode type: return")
        return 0

    if not (word & 0xE0030003) or (word & 0xE0030003) == 0x40000000:
        # methods
        method = word & 0x1FFF
        # subchannel = (word >> 13) & 7
        method_count = (word >> 18) & 0x7FF
        # method_nonincreasing = word & 0x40000000
        # state->dcount = 0;
        if display:
            print(prefix + "; Method: 0x%04X (%d times)" % (method, method_count))
        addr += 4 + method_count * 4
        return addr

    print(prefix + "; unknown opcode type")
    return addr


class XboxHelper:
    """Provides various functions for interaction with XBOX"""

    def __init__(self, xbox):
        self.xbox = xbox
        self.ramht_offset = 0
        self.ramht_size = 0

    def delay(self):
        # FIXME: if this returns `True`, the functions below should have their own
        #       loops which check for command completion
        # time.sleep(0.01)
        return False

    def disable_pgraph_fifo(self):
        state_s1 = self.xbox.read_u32(PGRAPH_STATE)
        self.xbox.write_u32(PGRAPH_STATE, state_s1 & 0xFFFFFFFE)

    def wait_until_pgraph_idle(self):
        while self.xbox.read_u32(PGRAPH_STATUS) & 0x00000001:
            time.sleep(0.001)

    def enable_pgraph_fifo(self):
        state_s1 = self.xbox.read_u32(PGRAPH_STATE)
        self.xbox.write_u32(PGRAPH_STATE, state_s1 | 0x00000001)
        if self.delay():
            pass

    def pause_fifo_puller(self):
        """Disable the PFIFO puller"""
        state_s1 = self.xbox.read_u32(CACHE_PULL_STATE)
        self.xbox.write_u32(CACHE_PULL_STATE, state_s1 & 0xFFFFFFFE)
        if self.delay():
            pass
        # print("Puller State was 0x" + format(state_s1, '08X'))

    def resume_fifo_puller(self):
        """Enable the PFIFO puller"""
        state_s2 = self.xbox.read_u32(CACHE_PULL_STATE)
        self.xbox.write_u32(
            CACHE_PULL_STATE, (state_s2 & 0xFFFFFFFE) | 1
        )  # Recover puller state
        if self.delay():
            pass

    def wait_until_pusher_idle(self):
        """Busy wait until the PFIFO pusher stops being busy"""
        while self.xbox.read_u32(CACHE_PUSH_STATE) & (1 << 4):
            pass

    def pause_fifo_pusher(self):
        """Disable the PFIFO pusher"""
        state_s1 = self.xbox.read_u32(CACHE_PUSH_MASTER_STATE)
        self.xbox.write_u32(CACHE_PUSH_MASTER_STATE, state_s1 & 0xFFFFFFFE)
        if self.delay():
            pass

    def resume_fifo_pusher(self):
        """Enable the PFIFO pusher"""
        state_s2 = self.xbox.read_u32(CACHE_PUSH_MASTER_STATE)
        self.xbox.write_u32(
            CACHE_PUSH_MASTER_STATE, (state_s2 & 0xFFFFFFFE) | 1
        )  # Recover pusher state
        if self.delay():
            pass

    def allow_populate_fifo_cache(self):
        """Temporarily enable the PFIFO pusher to populate the CACHE

        It is assumed that the pusher was previously paused, and it will be paused on
        exit.
        """
        self.resume_fifo_pusher()
        time.sleep(0.05)
        self.pause_fifo_pusher()

    def _dump_pb(self, start, end):
        offset = start
        while offset != end:
            word = self.xbox.read_u32(0x80000000 | offset)
            offset = parse_command(offset, word, True)
            if offset == 0:
                break

    # FIXME: This works poorly if the method count is not 0
    def print_pb_state(self):
        v_dma_get_addr = self.xbox.read_u32(DMA_PULL_ADDR)
        v_dma_put_addr = self.xbox.read_u32(DMA_PUSH_ADDR)
        v_dma_subroutine = self.xbox.read_u32(DMA_SUBROUTINE)

        print(
            "PB-State: 0x%08X / 0x%08X / 0x%08X"
            % (v_dma_get_addr, v_dma_put_addr, v_dma_subroutine)
        )
        self._dump_pb(v_dma_get_addr, v_dma_put_addr)
        print()

    def print_cache_state(self):
        v_get_addr = self.xbox.read_u32(CACHE_PULL_ADDR)
        v_put_addr = self.xbox.read_u32(CACHE_PUSH_ADDR)

        v_get_state = self.xbox.read_u32(CACHE_PULL_STATE)
        v_put_state = self.xbox.read_u32(CACHE_PUSH_STATE)

        print("CACHE-State: 0x%X / 0x%X" % (v_get_addr, v_put_addr))

        print("Put / Pusher enabled: %s" % ("Yes" if (v_put_state & 1) else "No"))
        print("Get / Puller enabled: %s" % ("Yes" if (v_get_state & 1) else "No"))

        print("Cache:")
        for i in range(128):

            cache1_method = self.xbox.read_u32(0xFD003800 + i * 8)
            cache1_data = self.xbox.read_u32(0xFD003804 + i * 8)

            output = "  [0x%02X] 0x%04X (0x%08X)" % (i, cache1_method, cache1_data)
            v_get_offset = i * 8 - v_get_addr
            if v_get_offset >= 0 and v_get_offset < 8:
                output += " < get[%d]" % v_get_offset
            v_put_offset = i * 8 - v_put_addr
            if v_put_offset >= 0 and v_put_offset < 8:
                output += " < put[%d]" % v_put_offset

            print(output)
        print()

    def print_dma_state(self):
        v_dma_state = self.xbox.read_u32(DMA_STATE)
        v_dma_method = v_dma_state & 0x1FFC
        # v_dma_subchannel = (v_dma_state >> 13) & 7
        v_dma_method_count = (v_dma_state >> 18) & 0x7FF
        # v_dma_method_nonincreasing = v_dma_state & 1
        # higher bits are for error signalling?

        print("v_dma_method: 0x%04X (count: %d)" % (v_dma_method, v_dma_method_count))

    def fetch_ramht(self):
        ht = self.xbox.read_u32(RAM_HASHTABLE)
        NV_PFIFO_RAMHT_BASE_ADDRESS = 0x000001F0
        NV_PFIFO_RAMHT_SIZE = 0x00030000

        offset = (ht & NV_PFIFO_RAMHT_BASE_ADDRESS) << 12
        size = 1 << (((ht & NV_PFIFO_RAMHT_SIZE) >> 16) + 12)

        self.ramht_offset = offset
        self.ramht_size = size
        print("RAMHT: 0x%X - Base addr 0x%X size: %d" % (ht, offset, size))

    def fetch_graphics_class(self):
        """Returns the target graphics class."""
        ctx_switch_1 = self.xbox.read_u32(CTX_SWITCH1)
        return ctx_switch_1 & 0xFF


def apply_anti_aliasing_factor(surface_anti_aliasing, x, y):
    if surface_anti_aliasing == 0:
        return x, y

    if surface_anti_aliasing == 1:
        return x * 2, y

    if surface_anti_aliasing == 2:
        return x * 2, y * 2

    assert False
