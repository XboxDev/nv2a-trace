; Construct binary using `nasm kick_fifo.asm`

bits 32

%define CACHE_PUSH_MASTER_STATE     0xFD003200
%define CACHE_PUSH_STATE            0xFD003220
%define DMA_PUSH_ADDR               0xFD003240
%define DMA_PULL_ADDR               0xFD003244

kick_fifo:

; Load `expected_push` into EDX
mov edx, dword [ebp+4]

; Avoid any other CPU stuff overwriting stuff in this risky section
cli

mov eax, 0xBAD0000
cmp edx, dword [DMA_PUSH_ADDR]
jne done

; resume_fifo_pusher(xbox):
or dword [CACHE_PUSH_STATE], 0x00000001

; Do a short busy loop. Ideally this would wait forever until the push buffer becomes
; empty, but it may cause a timeout for the invoker dependent on the interface being
; used.

mov ecx, 0x2000

wait_idle:

dec ecx
jz wait_failed

mov ebx, dword [CACHE_PUSH_STATE]
test ebx, 0x100
jnz wait_idle

mov eax, 0x1337C0DE
jmp pause_pusher

wait_failed:
; "BUSY"
mov eax, 0x32555359

pause_pusher:
and ebx, 0xFFFFFFFE
mov dword [CACHE_PUSH_STATE], ebx

cmp edx, dword [DMA_PUSH_ADDR]
je done
mov eax, 0xBADBAD

done:

sti
ret 4
