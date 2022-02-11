; Construct binary using `nasm kick_fifo.asm`

bits 32

%define CACHE_PUSH_MASTER_STATE     0xFD003200
%define CACHE_PUSH_STATE            0xFD003220
%define DMA_PUSH_ADDR               0xFD003240
%define DMA_PULL_ADDR               0xFD003244

kick_fifo:

push ebp
mov ebp, esp
push ebx

; Load `expected_push` into EDX
mov edx, dword [ebp+8]

; Avoid any other CPU stuff overwriting stuff in this risky section
cli

; if (DMA_PUSH_ADDR != expected_push) return 0xBAD0000
mov eax, 0xBAD0000
cmp edx, dword [DMA_PUSH_ADDR]
jne done

; resume_fifo_pusher(xbox):
;state = xbox.read_u32(CACHE_PUSH_STATE)
;xbox.write_u32(CACHE_PUSH_STATE, state | DMA_PUSH_ACCESS)
or dword [CACHE_PUSH_STATE], 0x00000001

; Do a short busy loop. Ideally this would wait forever until the push buffer becomes
; empty, but it may cause a timeout for the invoker dependent on the interface being
; used.

mov ecx, 0x2000

wait_idle:

dec ecx
jz wait_failed

; if ([NV_PFIFO_CACHE1_DMA_PUSH] & 0x100) goto wait_idle;
mov ebx, dword [CACHE_PUSH_STATE]
test ebx, 0x100
jnz wait_idle

mov eax, 0x1337C0DE
jmp pause_pusher

wait_failed:
; "BUSY"
mov eax, 0x32555359

pause_pusher:
; pause_fifo_pusher(xbox):
;
;state = xbox.read_u32(CACHE_PUSH_STATE)
;xbox.write_u32(CACHE_PUSH_STATE, state & ~DMA_PUSH_ACCESS)
and ebx, 0xFFFFFFFE
mov dword [CACHE_PUSH_STATE], ebx

; if (DMA_PUSH_ADDR != `expected_push`) return 0xBADBAD
cmp edx, dword [DMA_PUSH_ADDR]
je done
mov eax, 0xBADBAD

done:

pop ebx
mov esp, ebp
pop ebp

sti
ret 4
