; Construct binary using `nasm exchange_u32.asm`

bits 32

exchange_u32:

; Avoid any other CPU stuff overwriting stuff in this risky section
cli

; value
mov eax, dword [esp+4]

; address
mov edx, dword [esp+8]

xchg dword [EDX],EAX

sti

ret 0x8
