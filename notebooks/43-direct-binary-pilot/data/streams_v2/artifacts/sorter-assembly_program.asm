global _start
default rel

section .rodata
err_message: db 'ERR', 10

section .bss
input_buffer:  resb 4097
align 4
values:        resd 128
output_buffer: resb 1536
scratch:       resb 16

section .text
_start:
    xor r12d, r12d

read_input:
    xor eax, eax
    xor edi, edi
    lea rsi, [rel input_buffer]
    add rsi, r12
    mov edx, 4097
    sub rdx, r12
    syscall
    test rax, rax
    jz parse_input
    js read_failed
    add r12, rax
    cmp r12, 4096
    ja invalid_input
    jmp read_input

read_failed:
    cmp rax, -4
    je read_input
    jmp invalid_input

parse_input:
    lea rsi, [rel input_buffer]
    mov rdi, rsi
    add rdi, r12
    lea rbx, [rel values]
    xor r8d, r8d

scan_token:
    cmp rsi, rdi
    je sort_values
    movzx ecx, byte [rsi]
    cmp ecx, 32
    je skip_delimiter
    cmp ecx, 9
    je skip_delimiter
    cmp ecx, 10
    je skip_delimiter

    cmp r8d, 128
    jae invalid_input
    xor eax, eax
    xor r9d, r9d
    mov r10d, 2147483647
    cmp ecx, '-'
    jne first_digit
    mov r9d, 1
    inc r10
    inc rsi
    cmp rsi, rdi
    je invalid_input

first_digit:
    movzx ecx, byte [rsi]
    sub ecx, '0'
    cmp ecx, 9
    ja invalid_input

accumulate_digit:
    imul rax, rax, 10
    add rax, rcx
    cmp rax, r10
    ja invalid_input
    inc rsi
    cmp rsi, rdi
    je store_value

    movzx ecx, byte [rsi]
    sub ecx, '0'
    cmp ecx, 9
    jbe accumulate_digit

    add ecx, '0'
    cmp ecx, 32
    je store_value
    cmp ecx, 9
    je store_value
    cmp ecx, 10
    jne invalid_input

store_value:
    test r9d, r9d
    jz store_signed_value
    neg eax

store_signed_value:
    mov [rbx + r8*4], eax
    inc r8d
    jmp scan_token

skip_delimiter:
    inc rsi
    jmp scan_token

sort_values:
    cmp r8d, 1
    jbe format_output
    mov ecx, 1

sort_outer:
    mov eax, [rbx + rcx*4]
    mov rdx, rcx

sort_inner:
    test rdx, rdx
    jz insert_value
    mov esi, [rbx + rdx*4 - 4]
    cmp esi, eax
    jle insert_value
    mov [rbx + rdx*4], esi
    dec rdx
    jmp sort_inner

insert_value:
    mov [rbx + rdx*4], eax
    inc rcx
    cmp rcx, r8
    jb sort_outer

format_output:
    lea rdi, [rel output_buffer]
    xor r9d, r9d
    mov r10d, 10
    test r8d, r8d
    jz output_ready

format_value:
    movsxd rax, dword [rbx + r9*4]
    test rax, rax
    jns format_magnitude
    mov byte [rdi], '-'
    inc rdi
    neg rax

format_magnitude:
    lea rsi, [rel scratch + 16]
    xor r11d, r11d

convert_digit:
    xor edx, edx
    div r10
    add dl, '0'
    dec rsi
    mov [rsi], dl
    inc r11d
    test rax, rax
    jnz convert_digit

copy_digits:
    mov al, [rsi]
    mov [rdi], al
    inc rsi
    inc rdi
    dec r11d
    jnz copy_digits

    mov byte [rdi], 10
    inc rdi
    inc r9d
    cmp r9, r8
    jb format_value

output_ready:
    lea rsi, [rel output_buffer]
    mov rdx, rdi
    sub rdx, rsi
    xor r12d, r12d
    jmp write_output

invalid_input:
    lea rsi, [rel err_message]
    mov edx, 4
    mov r12d, 2

write_output:
    test rdx, rdx
    jz exit_program
    mov eax, 1
    mov edi, 1
    syscall
    test rax, rax
    jg write_progress
    cmp rax, -4
    je write_output
    mov r12d, 2
    jmp exit_program

write_progress:
    add rsi, rax
    sub rdx, rax
    jmp write_output

exit_program:
    mov edi, r12d
    mov eax, 60
    syscall

section .note.GNU-stack noalloc noexec nowrite progbits
