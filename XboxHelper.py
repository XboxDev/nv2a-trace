"""Various helper methods"""

# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-f-string
# pylint: disable=chained-comparison

import atexit

DMA_STATE = 0xFD003228
DMA_PUT_ADDR = 0xFD003240
DMA_GET_ADDR = 0xFD003244
DMA_SUBROUTINE = 0xFD00324C

PUT_ADDR = 0xFD003210
PUT_STATE = 0xFD003220
GET_ADDR = 0xFD003270
GET_STATE = 0xFD003250

PGRAPH_STATE = 0xFD400720
PGRAPH_STATUS = 0xFD400700


def load_binary(xbox, data):
    """Loads arbitrary data into a new contiguous memory block on the xbox."""
    code_addr = xbox.ke.MmAllocateContiguousMemory(len(data))
    print("load_binary: Allocated 0x%08X" % code_addr)

    def free_allocation():
        print("load_binary: Free'ing 0x%08X" % code_addr)
        xbox.ke.MmFreeContiguousMemory(code_addr)

    atexit.register(free_allocation)
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
            pass

    def enable_pgraph_fifo(self):
        state_s1 = self.xbox.read_u32(PGRAPH_STATE)
        self.xbox.write_u32(PGRAPH_STATE, state_s1 | 0x00000001)
        if self.delay():
            pass

    def wait_until_pusher_idle(self):
        while self.xbox.read_u32(GET_STATE) & (1 << 4):
            pass

    def pause_fifo_puller(self):
        # Idle the puller and pusher
        state_s1 = self.xbox.read_u32(GET_STATE)
        self.xbox.write_u32(GET_STATE, state_s1 & 0xFFFFFFFE)
        if self.delay():
            pass
        # print("Puller State was 0x" + format(state_s1, '08X'))

    def pause_fifo_pusher(self):
        state_s1 = self.xbox.read_u32(PUT_STATE)
        self.xbox.write_u32(PUT_STATE, state_s1 & 0xFFFFFFFE)
        if self.delay():
            pass
        if False:
            state_s1 = self.xbox.read_u32(0xFD003200)
            self.xbox.write_u32(0xFD003200, state_s1 & 0xFFFFFFFE)
            if self.delay():
                pass
            # print("Pusher State was 0x" + format(state_s1, '08X'))

    def resume_fifo_puller(self):
        # Resume puller and pusher
        state_s2 = self.xbox.read_u32(GET_STATE)
        self.xbox.write_u32(
            GET_STATE, (state_s2 & 0xFFFFFFFE) | 1
        )  # Recover puller state
        if self.delay():
            pass

    def resume_fifo_pusher(self):
        if False:
            state_s2 = self.xbox.read_u32(0xFD003200)
            self.xbox.write_u32(0xFD003200, state_s2 & 0xFFFFFFFE | 1)
            if self.delay():
                pass
        state_s2 = self.xbox.read_u32(PUT_STATE)
        self.xbox.write_u32(
            PUT_STATE, (state_s2 & 0xFFFFFFFE) | 1
        )  # Recover pusher state
        if self.delay():
            pass

    def _dump_pb(self, start, end):
        offset = start
        while offset != end:
            word = self.xbox.read_u32(0x80000000 | offset)
            offset = parse_command(offset, word, True)
            if offset == 0:
                break

    # FIXME: This works poorly if the method count is not 0
    def print_pb_state(self):
        v_dma_get_addr = self.xbox.read_u32(DMA_GET_ADDR)
        v_dma_put_addr = self.xbox.read_u32(DMA_PUT_ADDR)
        v_dma_subroutine = self.xbox.read_u32(DMA_SUBROUTINE)

        print(
            "PB-State: 0x%08X / 0x%08X / 0x%08X"
            % (v_dma_get_addr, v_dma_put_addr, v_dma_subroutine)
        )
        self._dump_pb(v_dma_get_addr, v_dma_put_addr)
        print()

    def print_cache_state(self):
        v_get_addr = self.xbox.read_u32(GET_ADDR)
        v_put_addr = self.xbox.read_u32(PUT_ADDR)

        v_get_state = self.xbox.read_u32(GET_STATE)
        v_put_state = self.xbox.read_u32(PUT_STATE)

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


def apply_anti_aliasing_factor(surface_anti_aliasing, x, y):
    if surface_anti_aliasing == 0:
        return x, y

    if surface_anti_aliasing == 1:
        return x * 2, y

    if surface_anti_aliasing == 2:
        return x * 2, y * 2

    assert False
