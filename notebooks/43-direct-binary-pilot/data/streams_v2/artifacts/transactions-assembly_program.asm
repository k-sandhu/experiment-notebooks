bits 64
default rel

global _start

section .rodata
header: db 'account,amount_cents', 10
header_len equ $ - header
error_message: db 'ERR', 10

section .bss
input_buffer: resb 4097
totals: resq 64
seen: resb 64
output_buffer: resb 2048
digits: resb 32

section .text
_start:
    cld
    xor r12d, r12d
    lea r13, [rel input_buffer]

.read:
    xor eax, eax
    xor edi, edi
    lea rsi, [r13 + r12]
    mov edx, 4097
    sub rdx, r12
    syscall
    test rax, rax
    js .read_error
    jz .parse
    add r12, rax
    cmp r12, 4096
    ja .error
    jmp .read

.read_error:
    cmp rax, -4
    je .read
    jmp .error

.parse:
    cmp r12, header_len
    jb .error
    mov rsi, r13
    lea rdi, [rel header]
    mov ecx, header_len
    repe cmpsb
    jne .error

    lea rdi, [r13 + r12]
    lea r14, [rel totals]
    lea r15, [rel seen]
    xor r8d, r8d

.next_record:
    cmp rsi, rdi
    je .parsed
    inc r8d
    cmp r8d, 128
    ja .error

    xor r9d, r9d
    movzx edx, byte [rsi]
    sub edx, '0'
    cmp edx, 9
    ja .error

.account_digit:
    lea r9, [r9 + r9*4]
    lea r9, [rdx + r9*2]
    cmp r9, 63
    ja .error
    inc rsi
    cmp rsi, rdi
    je .error
    movzx edx, byte [rsi]
    cmp dl, ','
    je .account_done
    sub edx, '0'
    cmp edx, 9
    jbe .account_digit
    jmp .error

.account_done:
    inc rsi
    cmp rsi, rdi
    je .error
    xor r10d, r10d
    cmp byte [rsi], '-'
    jne .amount_start
    mov r10d, 1
    inc rsi
    cmp rsi, rdi
    je .error

.amount_start:
    xor eax, eax
    movzx edx, byte [rsi]
    sub edx, '0'
    cmp edx, 9
    ja .error

.amount_digit:
    lea rax, [rax + rax*4]
    lea rax, [rdx + rax*2]
    cmp rax, 1000000000
    ja .error
    inc rsi
    cmp rsi, rdi
    je .commit
    movzx edx, byte [rsi]
    cmp dl, 10
    je .newline
    sub edx, '0'
    cmp edx, 9
    jbe .amount_digit
    jmp .error

.newline:
    inc rsi

.commit:
    test r10d, r10d
    jz .add_amount
    neg rax

.add_amount:
    add qword [r14 + r9*8], rax
    mov byte [r15 + r9], 1
    jmp .next_record

.parsed:
    lea rbx, [rel output_buffer]
    xor r8d, r8d

.output_account:
    cmp r8d, 64
    jae .output_ready
    cmp byte [r15 + r8], 0
    je .output_next

    mov eax, r8d
    call emit_unsigned
    mov byte [rbx], ','
    inc rbx

    mov rax, [r14 + r8*8]
    test rax, rax
    jns .output_total
    mov byte [rbx], '-'
    inc rbx
    neg rax

.output_total:
    call emit_unsigned
    mov byte [rbx], 10
    inc rbx

.output_next:
    inc r8d
    jmp .output_account

.output_ready:
    lea rsi, [rel output_buffer]
    mov rdx, rbx
    sub rdx, rsi
    xor r12d, r12d
    jmp .write

.error:
    lea rsi, [rel error_message]
    mov edx, 4
    mov r12d, 2

.write:
    test rdx, rdx
    jz .exit
    mov eax, 1
    mov edi, 1
    syscall
    test rax, rax
    jg .write_progress
    cmp rax, -4
    je .write
    mov r12d, 2
    jmp .exit

.write_progress:
    add rsi, rax
    sub rdx, rax
    jmp .write

.exit:
    mov edi, r12d
    mov eax, 60
    syscall

emit_unsigned:
    lea rsi, [rel digits + 32]
    mov r11d, 10
    xor ecx, ecx

.convert:
    xor edx, edx
    div r11
    add dl, '0'
    dec rsi
    mov byte [rsi], dl
    inc ecx
    test rax, rax
    jnz .convert

.copy:
    mov dl, byte [rsi]
    mov byte [rbx], dl
    inc rsi
    inc rbx
    dec ecx
    jnz .copy
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
