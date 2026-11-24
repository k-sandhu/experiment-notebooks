global _start
default rel

section .bss
    input_buffer  resb 4096
    output_buffer resb 8192

section .text
_start:
    xor r12d, r12d

.read:
    cmp r12, 4096
    je .encode
    xor eax, eax
    xor edi, edi
    lea rsi, [input_buffer]
    add rsi, r12
    mov edx, 4096
    sub edx, r12d
    syscall
    cmp rax, -4
    je .read
    test rax, rax
    jle .encode
    add r12, rax
    jmp .read

.encode:
    test r12, r12
    jz .exit
    lea rsi, [input_buffer]
    lea r8, [rsi + r12]
    lea rdi, [output_buffer]

.next_pair:
    mov al, [rsi]
    xor ecx, ecx

.count:
    inc ecx
    inc rsi
    cmp ecx, 255
    je .emit
    cmp rsi, r8
    jae .emit
    cmp byte [rsi], al
    je .count

.emit:
    mov [rdi], cl
    mov [rdi + 1], al
    add rdi, 2
    cmp rsi, r8
    jb .next_pair

    lea r13, [output_buffer]
    mov r12, rdi
    sub r12, r13

.write:
    mov eax, 1
    mov edi, 1
    mov rsi, r13
    mov rdx, r12
    syscall
    cmp rax, -4
    je .write
    test rax, rax
    jle .exit
    add r13, rax
    sub r12, rax
    jnz .write

.exit:
    mov eax, 60
    xor edi, edi
    syscall
