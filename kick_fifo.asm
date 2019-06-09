; Construct binary using `nasm kick_fifo.asm`

bits 32

kick_fifo:

; Load expected_put into reg
mov edx, dword [esp+4]

; Avoid any other CPU stuff overwriting stuff in this risky section
cli

mov eax, 0xBAD

; Check if DMA_PUT_ADDR is what it must be, or abort otherwise
cmp edx, dword [0xFD003240]
jne skip

mov eax, 0x1337C0DE

; resume_fifo_pusher(xbox):
;s2 = xbox.read_u32(PUT_STATE)
;xbox.write_u32(PUT_STATE, (s2 & 0xFFFFFFFE) | 1) # Recover pusher state
or dword [0xFD003220], 0x00000001

;FIXME: Do a short busy loop? what if GPU does not find enough time to run?

; pause_fifo_pusher(xbox):
;s1 = xbox.read_u32(PUT_STATE)
;xbox.write_u32(PUT_STATE, s1 & 0xFFFFFFFE)

wait_idle:
mov ecx, dword [0xFD003220]

# Make sure that pushbuffer is empty before we hand control back
test ecx, 0x100
jnz wait_idle

and ecx, 0xFFFFFFFE
mov dword [0xFD003220], ecx

; Mark run as very bad if PUT changed
cmp edx, dword [0xFD003240]
je skip
mov eax, 0xBADBAD

skip:

sti
ret 4
