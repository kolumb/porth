#!/usr/bin/env python3

import os
import sys
import subprocess
import shlex
from os import path
from typing import *
from enum import Enum, auto
from dataclasses import dataclass

debug=False

Loc=Tuple[str, int, int]

class Keyword(Enum):
    IF=auto()
    END=auto()
    ELSE=auto()
    WHILE=auto()
    DO=auto()
    MACRO=auto()
    INCLUDE=auto()

class Intrinsic(Enum):
    PLUS=auto()
    MINUS=auto()
    MUL=auto()
    DIVMOD=auto()
    EQ=auto()
    GT=auto()
    LT=auto()
    GE=auto()
    LE=auto()
    NE=auto()
    SHR=auto()
    SHL=auto()
    BOR=auto()
    BAND=auto()
    PRINT=auto()
    DUP=auto()
    SWAP=auto()
    DROP=auto()
    OVER=auto()
    MEM=auto()
    # TODO: implement typing for load/store operations
    LOAD=auto()
    STORE=auto()
    SYSCALL0=auto()
    SYSCALL1=auto()
    SYSCALL2=auto()
    SYSCALL3=auto()
    SYSCALL4=auto()
    SYSCALL5=auto()
    SYSCALL6=auto()

class OpType(Enum):
    PUSH_INT=auto()
    PUSH_STR=auto()
    INTRINSIC=auto()
    IF=auto()
    END=auto()
    ELSE=auto()
    WHILE=auto()
    DO=auto()

OpAddr=int

@dataclass
class Op:
    typ: OpType
    loc: Loc
    operand: Optional[Union[int, str, Intrinsic, OpAddr]] = None

Program=List[Op]

class TokenType(Enum):
    WORD=auto()
    INT=auto()
    STR=auto()
    CHAR=auto()
    KEYWORD=auto()

assert len(TokenType) == 5, "Exhaustive Token type definition. The `value` field of the Token dataclass may require an update"
@dataclass
class Token:
    typ: TokenType
    loc: Loc
    value: Union[int, str, Keyword]

STR_CAPACITY = 640_000 # should be enough for everyone
MEM_CAPACITY = 640_000

def simulate_little_endian_linux(program: Program):
    stack: List[int] = []
    mem = bytearray(STR_CAPACITY + MEM_CAPACITY)
    str_offsets = {}
    str_size = 0
    ip = 0
    while ip < len(program):
        assert len(OpType) == 8, "Exhaustive op handling in simulate_little_endian_linux"
        op = program[ip]
        if op.typ == OpType.PUSH_INT:
            assert isinstance(op.operand, int), "This could be a bug in the compilation step"
            stack.append(op.operand)
            ip += 1
        elif op.typ == OpType.PUSH_STR:
            assert isinstance(op.operand, str), "This could be a bug in the compilation step"
            value = op.operand.encode('utf-8')
            n = len(value)
            stack.append(n)
            if ip not in str_offsets:
                str_offsets[ip] = str_size
                mem[str_size:str_size+n] = value
                str_size += n
                assert str_size <= STR_CAPACITY, "String buffer overflow"
            stack.append(str_offsets[ip])
            ip += 1
        elif op.typ == OpType.IF:
            a = stack.pop()
            if a == 0:
                assert isinstance(op.operand, OpAddr), "This could be a bug in the compilation step"
                ip = op.operand
            else:
                ip += 1
        elif op.typ == OpType.ELSE:
            assert isinstance(op.operand, OpAddr), "This could be a bug in the compilation step"
            ip = op.operand
        elif op.typ == OpType.END:
            assert isinstance(op.operand, OpAddr), "This could be a bug in the compilation step"
            ip = op.operand
        elif op.typ == OpType.WHILE:
            ip += 1
        elif op.typ == OpType.DO:
            a = stack.pop()
            if a == 0:
                assert isinstance(op.operand, OpAddr), "This could be a bug in the compilation step"
                ip = op.operand
            else:
                ip += 1
        elif op.typ == OpType.INTRINSIC:
            assert len(Intrinsic) == 29, "Exhaustive handling of intrinsic in simulate_little_endian_linux()"
            if op.operand == Intrinsic.PLUS:
                a = stack.pop()
                b = stack.pop()
                stack.append(a + b)
                ip += 1
            elif op.operand == Intrinsic.MINUS:
                a = stack.pop()
                b = stack.pop()
                stack.append(b - a)
                ip += 1
            elif op.operand == Intrinsic.MUL:
                a = stack.pop()
                b = stack.pop()
                stack.append(b * a)
                ip += 1
            elif op.operand == Intrinsic.DIVMOD:
                a = stack.pop()
                b = stack.pop()
                stack.append(b // a)
                stack.append(b % a)
                ip += 1
            elif op.operand == Intrinsic.EQ:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(a == b))
                ip += 1
            elif op.operand == Intrinsic.GT:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b > a))
                ip += 1
            elif op.operand == Intrinsic.LT:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b < a))
                ip += 1
            elif op.operand == Intrinsic.GE:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b >= a))
                ip += 1
            elif op.operand == Intrinsic.LE:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b <= a))
                ip += 1
            elif op.operand == Intrinsic.NE:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b != a))
                ip += 1
            elif op.operand == Intrinsic.SHR:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b >> a))
                ip += 1
            elif op.operand == Intrinsic.SHL:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(b << a))
                ip += 1
            elif op.operand == Intrinsic.BOR:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(a | b))
                ip += 1
            elif op.operand == Intrinsic.BAND:
                a = stack.pop()
                b = stack.pop()
                stack.append(int(a & b))
                ip += 1
            elif op.operand == Intrinsic.PRINT:
                a = stack.pop()
                print(a)
                ip += 1
            elif op.operand == Intrinsic.DUP:
                a = stack.pop()
                stack.append(a)
                stack.append(a)
                ip += 1
            elif op.operand == Intrinsic.SWAP:
                a = stack.pop()
                b = stack.pop()
                stack.append(a)
                stack.append(b)
                ip += 1
            elif op.operand == Intrinsic.DROP:
                stack.pop()
                ip += 1
            elif op.operand == Intrinsic.OVER:
                a = stack.pop()
                b = stack.pop()
                stack.append(b)
                stack.append(a)
                stack.append(b)
                ip += 1
            elif op.operand == Intrinsic.MEM:
                stack.append(STR_CAPACITY)
                ip += 1
            elif op.operand == Intrinsic.LOAD:
                addr = stack.pop()
                byte = mem[addr]
                stack.append(byte)
                ip += 1
            elif op.operand == Intrinsic.STORE:
                store_value = stack.pop()
                store_addr = stack.pop()
                mem[store_addr] = store_value & 0xFF
                ip += 1
            elif op.operand == Intrinsic.SYSCALL0:
                syscall_number = stack.pop()
                if syscall_number == 39:
                    stack.append(os.getpid())
                else:
                    assert False, "unknown syscall number %d" % syscall_number
                ip += 1
            elif op.operand == Intrinsic.SYSCALL1:
                assert False, "not implemented"
            elif op.operand == Intrinsic.SYSCALL2:
                assert False, "not implemented"
            elif op.operand == Intrinsic.SYSCALL3:
                syscall_number = stack.pop()
                arg1 = stack.pop()
                arg2 = stack.pop()
                arg3 = stack.pop()
                if syscall_number == 1:
                    fd = arg1
                    buf = arg2
                    count = arg3
                    s = mem[buf:buf+count].decode('utf-8')
                    if fd == 1:
                        print(s, end='')
                    elif fd == 2:
                        print(s, end='', file=sys.stderr)
                    else:
                        assert False, "unknown file descriptor %d" % fd
                    stack.append(count)
                else:
                    assert False, "unknown syscall number %d" % syscall_number
                ip += 1
            elif op.operand == Intrinsic.SYSCALL4:
                assert False, "not implemented"
            elif op.operand == Intrinsic.SYSCALL5:
                assert False, "not implemented"
            elif op.operand == Intrinsic.SYSCALL6:
                assert False, "not implemented"
            else:
                assert False, "unreachable"
        else:
            assert False, "unreachable"
    if debug:
        print("[INFO] Memory dump")
        print(mem[:20])

def generate_nasm_linux_x86_64(program: Program, out_file_path: str):
    strs: List[bytes] = []
    with open(out_file_path, "w") as out:
        out.write("BITS 64\n")
        out.write("segment .text\n")
        out.write("print:\n")
        out.write("    mov     r9, -3689348814741910323\n")
        out.write("    sub     rsp, 40\n")
        out.write("    mov     BYTE [rsp+31], 10\n")
        out.write("    lea     rcx, [rsp+30]\n")
        out.write(".L2:\n")
        out.write("    mov     rax, rdi\n")
        out.write("    lea     r8, [rsp+32]\n")
        out.write("    mul     r9\n")
        out.write("    mov     rax, rdi\n")
        out.write("    sub     r8, rcx\n")
        out.write("    shr     rdx, 3\n")
        out.write("    lea     rsi, [rdx+rdx*4]\n")
        out.write("    add     rsi, rsi\n")
        out.write("    sub     rax, rsi\n")
        out.write("    add     eax, 48\n")
        out.write("    mov     BYTE [rcx], al\n")
        out.write("    mov     rax, rdi\n")
        out.write("    mov     rdi, rdx\n")
        out.write("    mov     rdx, rcx\n")
        out.write("    sub     rcx, 1\n")
        out.write("    cmp     rax, 9\n")
        out.write("    ja      .L2\n")
        out.write("    lea     rax, [rsp+32]\n")
        out.write("    mov     edi, 1\n")
        out.write("    sub     rdx, rax\n")
        out.write("    xor     eax, eax\n")
        out.write("    lea     rsi, [rsp+32+rdx]\n")
        out.write("    mov     rdx, r8\n")
        out.write("    mov     rax, 1\n")
        out.write("    syscall\n")
        out.write("    add     rsp, 40\n")
        out.write("    ret\n")
        out.write("global _start\n")
        out.write("_start:\n")
        for ip in range(len(program)):
            op = program[ip]
            assert len(OpType) == 8, "Exhaustive ops handling in generate_nasm_linux_x86_64"
            out.write("addr_%d:\n" % ip)
            if op.typ == OpType.PUSH_INT:
                assert isinstance(op.operand, int), "This could be a bug in the compilation step"
                out.write("    ;; -- push int %d --\n" % op.operand)
                out.write("    mov rax, %d\n" % op.operand)
                out.write("    push rax\n")
            elif op.typ == OpType.PUSH_STR:
                assert isinstance(op.operand, str), "This could be a bug in the compilation step"
                value = op.operand.encode('utf-8')
                n = len(value)
                out.write("    ;; -- push str --\n")
                out.write("    mov rax, %d\n" % n)
                out.write("    push rax\n")
                out.write("    push str_%d\n" % len(strs))
                strs.append(value)
            elif op.typ == OpType.IF:
                out.write("    ;; -- if --\n")
                out.write("    pop rax\n")
                out.write("    test rax, rax\n")
                assert isinstance(op.operand, int), "This could be a bug in the compilation step"
                out.write("    jz addr_%d\n" % op.operand)
            elif op.typ == OpType.ELSE:
                out.write("    ;; -- else --\n")
                assert isinstance(op.operand, int), "This could be a bug in the compilation step"
                out.write("    jmp addr_%d\n" % op.operand)
            elif op.typ == OpType.END:
                assert isinstance(op.operand, int), "This could be a bug in the compilation step"
                out.write("    ;; -- end --\n")
                if ip + 1 != op.operand:
                    out.write("    jmp addr_%d\n" % op.operand)
            elif op.typ == OpType.WHILE:
                out.write("    ;; -- while --\n")
            elif op.typ == OpType.DO:
                out.write("    ;; -- do --\n")
                out.write("    pop rax\n")
                out.write("    test rax, rax\n")
                assert isinstance(op.operand, int), "This could be a bug in the compilation step"
                out.write("    jz addr_%d\n" % op.operand)
            elif op.typ == OpType.INTRINSIC:
                assert len(Intrinsic) == 29, "Exhaustive intrinsic handling in generate_nasm_linux_x86_64()"
                if op.operand == Intrinsic.PLUS:
                    out.write("    ;; -- plus --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    add rax, rbx\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.MINUS:
                    out.write("    ;; -- minus --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    sub rbx, rax\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.MUL:
                    out.write("    ;; -- mul --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    mul rbx\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.DIVMOD:
                    out.write("    ;; -- mod --\n")
                    out.write("    xor rdx, rdx\n")
                    out.write("    pop rbx\n")
                    out.write("    pop rax\n")
                    out.write("    div rbx\n")
                    out.write("    push rax\n");
                    out.write("    push rdx\n");
                elif op.operand == Intrinsic.SHR:
                    out.write("    ;; -- shr --\n")
                    out.write("    pop rcx\n")
                    out.write("    pop rbx\n")
                    out.write("    shr rbx, cl\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.SHL:
                    out.write("    ;; -- shl --\n")
                    out.write("    pop rcx\n")
                    out.write("    pop rbx\n")
                    out.write("    shl rbx, cl\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.BOR:
                    out.write("    ;; -- bor --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    or rbx, rax\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.BAND:
                    out.write("    ;; -- band --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    and rbx, rax\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.PRINT:
                    out.write("    ;; -- print --\n")
                    out.write("    pop rdi\n")
                    out.write("    call print\n")
                elif op.operand == Intrinsic.EQ:
                    out.write("    ;; -- equal -- \n")
                    out.write("    mov rcx, 0\n");
                    out.write("    mov rdx, 1\n");
                    out.write("    pop rax\n");
                    out.write("    pop rbx\n");
                    out.write("    cmp rax, rbx\n");
                    out.write("    cmove rcx, rdx\n");
                    out.write("    push rcx\n")
                elif op.operand == Intrinsic.GT:
                    out.write("    ;; -- gt --\n")
                    out.write("    mov rcx, 0\n");
                    out.write("    mov rdx, 1\n");
                    out.write("    pop rbx\n");
                    out.write("    pop rax\n");
                    out.write("    cmp rax, rbx\n");
                    out.write("    cmovg rcx, rdx\n");
                    out.write("    push rcx\n")
                elif op.operand == Intrinsic.LT:
                    out.write("    ;; -- gt --\n")
                    out.write("    mov rcx, 0\n");
                    out.write("    mov rdx, 1\n");
                    out.write("    pop rbx\n");
                    out.write("    pop rax\n");
                    out.write("    cmp rax, rbx\n");
                    out.write("    cmovl rcx, rdx\n");
                    out.write("    push rcx\n")
                elif op.operand == Intrinsic.GE:
                    out.write("    ;; -- gt --\n")
                    out.write("    mov rcx, 0\n");
                    out.write("    mov rdx, 1\n");
                    out.write("    pop rbx\n");
                    out.write("    pop rax\n");
                    out.write("    cmp rax, rbx\n");
                    out.write("    cmovge rcx, rdx\n");
                    out.write("    push rcx\n")
                elif op.operand == Intrinsic.LE:
                    out.write("    ;; -- gt --\n")
                    out.write("    mov rcx, 0\n");
                    out.write("    mov rdx, 1\n");
                    out.write("    pop rbx\n");
                    out.write("    pop rax\n");
                    out.write("    cmp rax, rbx\n");
                    out.write("    cmovle rcx, rdx\n");
                    out.write("    push rcx\n")
                elif op.operand == Intrinsic.NE:
                    out.write("    ;; -- ne --\n")
                    out.write("    mov rcx, 0\n")
                    out.write("    mov rdx, 1\n")
                    out.write("    pop rbx\n")
                    out.write("    pop rax\n")
                    out.write("    cmp rax, rbx\n")
                    out.write("    cmovne rcx, rdx\n")
                    out.write("    push rcx\n")
                elif op.operand == Intrinsic.DUP:
                    out.write("    ;; -- dup -- \n")
                    out.write("    pop rax\n")
                    out.write("    push rax\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SWAP:
                    out.write("    ;; -- swap --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    push rax\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.DROP:
                    out.write("    ;; -- drop --\n")
                    out.write("    pop rax\n")
                elif op.operand == Intrinsic.OVER:
                    out.write("    ;; -- over --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rbx\n")
                    out.write("    push rbx\n")
                    out.write("    push rax\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.MEM:
                    out.write("    ;; -- mem --\n")
                    out.write("    push mem\n")
                elif op.operand == Intrinsic.LOAD:
                    out.write("    ;; -- load --\n")
                    out.write("    pop rax\n")
                    out.write("    xor rbx, rbx\n")
                    out.write("    mov bl, [rax]\n")
                    out.write("    push rbx\n")
                elif op.operand == Intrinsic.STORE:
                    out.write("    ;; -- store --\n")
                    out.write("    pop rbx\n");
                    out.write("    pop rax\n");
                    out.write("    mov [rax], bl\n");
                elif op.operand == Intrinsic.SYSCALL0:
                    out.write("    ;; -- syscall0 --\n")
                    out.write("    pop rax\n")
                    out.write("    syscall\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SYSCALL1:
                    out.write("    ;; -- syscall1 --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rdi\n")
                    out.write("    syscall\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SYSCALL2:
                    out.write("    ;; -- syscall2 -- \n")
                    out.write("    pop rax\n");
                    out.write("    pop rdi\n");
                    out.write("    pop rsi\n");
                    out.write("    syscall\n");
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SYSCALL3:
                    out.write("    ;; -- syscall3 --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rdi\n")
                    out.write("    pop rsi\n")
                    out.write("    pop rdx\n")
                    out.write("    syscall\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SYSCALL4:
                    out.write("    ;; -- syscall4 --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rdi\n")
                    out.write("    pop rsi\n")
                    out.write("    pop rdx\n")
                    out.write("    pop r10\n")
                    out.write("    syscall\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SYSCALL5:
                    out.write("    ;; -- syscall5 --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rdi\n")
                    out.write("    pop rsi\n")
                    out.write("    pop rdx\n")
                    out.write("    pop r10\n")
                    out.write("    pop r8\n")
                    out.write("    syscall\n")
                    out.write("    push rax\n")
                elif op.operand == Intrinsic.SYSCALL6:
                    out.write("    ;; -- syscall6 --\n")
                    out.write("    pop rax\n")
                    out.write("    pop rdi\n")
                    out.write("    pop rsi\n")
                    out.write("    pop rdx\n")
                    out.write("    pop r10\n")
                    out.write("    pop r8\n")
                    out.write("    pop r9\n")
                    out.write("    syscall\n")
                    out.write("    push rax\n")
                else:
                    assert False, "unreachable"
            else:
                assert False, "unreachable"

        out.write("addr_%d:\n" % len(program))
        out.write("    mov rax, 60\n")
        out.write("    mov rdi, 0\n")
        out.write("    syscall\n")
        out.write("segment .data\n")
        for index, s in enumerate(strs):
            out.write("str_%d: db %s\n" % (index, ','.join(map(hex, list(s)))))
        out.write("segment .bss\n")
        out.write("mem: resb %d\n" % MEM_CAPACITY)

assert len(Keyword) == 7, "Exhaustive KEYWORD_NAMES definition."
KEYWORD_NAMES = {
    'if': Keyword.IF,
    'end': Keyword.END,
    'else': Keyword.ELSE,
    'while': Keyword.WHILE,
    'do': Keyword.DO,
    'macro': Keyword.MACRO,
    'include': Keyword.INCLUDE,
}

assert len(Intrinsic) == 29, "Exhaustive INTRINSIC_NAMES definition"
INTRINSIC_NAMES = {
    '+': Intrinsic.PLUS,
    '-': Intrinsic.MINUS,
    '*': Intrinsic.MUL,
    'divmod': Intrinsic.DIVMOD,
    'print': Intrinsic.PRINT,
    '=': Intrinsic.EQ,
    '>': Intrinsic.GT,
    '<': Intrinsic.LT,
    '>=': Intrinsic.GE,
    '<=': Intrinsic.LE,
    '!=': Intrinsic.NE,
    'shr': Intrinsic.SHR,
    'shl': Intrinsic.SHL,
    'bor': Intrinsic.BOR,
    'band': Intrinsic.BAND,
    'dup': Intrinsic.DUP,
    'swap': Intrinsic.SWAP,
    'drop': Intrinsic.DROP,
    'over': Intrinsic.OVER,
    'mem': Intrinsic.MEM,
    '.': Intrinsic.STORE,
    ',': Intrinsic.LOAD,
    'syscall0': Intrinsic.SYSCALL0,
    'syscall1': Intrinsic.SYSCALL1,
    'syscall2': Intrinsic.SYSCALL2,
    'syscall3': Intrinsic.SYSCALL3,
    'syscall4': Intrinsic.SYSCALL4,
    'syscall5': Intrinsic.SYSCALL5,
    'syscall6': Intrinsic.SYSCALL6,
}

@dataclass
class Macro:
    loc: Loc
    tokens: List[Token]

def human(typ: TokenType) -> str:
    '''Human readable representation of an object that can be used in error messages'''
    assert len(TokenType) == 5, "Exhaustive handling of token types in human()"
    if typ == TokenType.WORD:
        return "a word"
    elif typ == TokenType.INT:
        return "an integer"
    elif typ == TokenType.STR:
        return "a string"
    elif typ == TokenType.CHAR:
        return "a character"
    elif typ == TokenType.KEYWORD:
        return "a keyword"
    else:
        assert False, "unreachable"

def compile_tokens_to_program(tokens: List[Token], include_paths: List[str]) -> Program:
    stack: List[OpAddr] = []
    program: List[Op] = []
    rtokens: List[Token] = list(reversed(tokens))
    macros: Dict[str, Macro] = {}
    ip: OpAddr = 0;
    while len(rtokens) > 0:
        # TODO: some sort of safety mechanism for recursive macros
        token = rtokens.pop()
        assert len(TokenType) == 5, "Exhaustive token handling in compile_tokens_to_program"
        if token.typ == TokenType.WORD:
            assert isinstance(token.value, str), "This could be a bug in the lexer"
            if token.value in INTRINSIC_NAMES:
                program.append(Op(typ=OpType.INTRINSIC, loc=token.loc, operand=INTRINSIC_NAMES[token.value]))
                ip += 1
            elif token.value in macros:
                rtokens += reversed(macros[token.value].tokens)
            else:
                print("%s:%d:%d: unknown word `%s`" % (token.loc + (token.value, )))
                exit(1)
        elif token.typ == TokenType.INT:
            assert isinstance(token.value, int), "This could be a bug in the lexer"
            program.append(Op(typ=OpType.PUSH_INT, operand=token.value, loc=token.loc))
            ip += 1
        elif token.typ == TokenType.STR:
            assert isinstance(token.value, str), "This could be a bug in the lexer"
            program.append(Op(typ=OpType.PUSH_STR, operand=token.value, loc=token.loc));
            ip += 1
        elif token.typ == TokenType.CHAR:
            assert isinstance(token.value, int)
            program.append(Op(typ=OpType.PUSH_INT, operand=token.value, loc=token.loc));
            ip += 1
        elif token.typ == TokenType.KEYWORD:
            assert len(Keyword) == 7, "Exhaustive keywords handling in compile_tokens_to_program()"
            if token.value == Keyword.IF:
                program.append(Op(typ=OpType.IF, loc=token.loc))
                stack.append(ip)
                ip += 1
            elif token.value == Keyword.ELSE:
                program.append(Op(typ=OpType.ELSE, loc=token.loc))
                if_ip = stack.pop()
                if program[if_ip].typ != OpType.IF:
                    print('%s:%d:%d: ERROR: `else` can only be used in `if`-blocks' % program[if_ip].loc)
                    exit(1)
                program[if_ip].operand = ip + 1
                stack.append(ip)
                ip += 1
            elif token.value == Keyword.END:
                program.append(Op(typ=OpType.END, loc=token.loc))
                block_ip = stack.pop()
                if program[block_ip].typ == OpType.IF or program[block_ip].typ == OpType.ELSE:
                    program[block_ip].operand = ip
                    program[ip].operand = ip + 1
                elif program[block_ip].typ == OpType.DO:
                    assert program[block_ip].operand is not None
                    program[ip].operand = program[block_ip].operand
                    program[block_ip].operand = ip + 1
                else:
                    print('%s:%d:%d: ERROR: `end` can only close `if`, `else` or `do` blocks for now' % program[block_ip].loc)
                    exit(1)
                ip += 1
            elif token.value == Keyword.WHILE:
                program.append(Op(typ=OpType.WHILE, loc=token.loc))
                stack.append(ip)
                ip += 1
            elif token.value == Keyword.DO:
                program.append(Op(typ=OpType.DO, loc=token.loc))
                while_ip = stack.pop()
                program[ip].operand = while_ip
                stack.append(ip)
                ip += 1
            elif token.value == Keyword.INCLUDE:
                if len(rtokens) == 0:
                    print("%s:%d:%d: ERROR: expected path to the include file but found nothing" % token.loc)
                    exit(1)
                token = rtokens.pop()
                if token.typ != TokenType.STR:
                    print("%s:%d:%d: ERROR: expected path to the include file to be %s but found %s" % (token.loc + (human(TokenType.STR), human(token.typ))))
                    exit(1)
                assert isinstance(token.value, str), "This is probably a bug in the lexer"
                # TODO: safety mechanism for recursive includes
                file_included = False
                for include_path in include_paths:
                    try:
                        rtokens += reversed(lex_file(path.join(include_path, token.value)))
                        file_included = True
                        break
                    except FileNotFoundError:
                        continue
                if not file_included:
                    print("%s:%d:%d: ERROR: file `%s` not found" % (token.loc + (token.value, )))
                    exit(1)
            # TODO: capability to define macros from command line
            elif token.value == Keyword.MACRO:
                if len(rtokens) == 0:
                    print("%s:%d:%d: ERROR: expected macro name but found nothing" % token.loc)
                    exit(1)
                token = rtokens.pop()
                if token.typ != TokenType.WORD:
                    print("%s:%d:%d: ERROR: expected macro name to be %s but found %s" % (token.loc + (human(TokenType.WORD), human(token.typ))))
                    exit(1)
                assert isinstance(token.value, str), "This is probably a bug in the lexer"
                if token.value in macros:
                    print("%s:%d:%d: ERROR: redefinition of already existing macro `%s`" % (token.loc + (token.value, )))
                    print("%s:%d:%d: NOTE: the first definition is located here" % macros[token.value].loc)
                    exit(1)
                if token.value in INTRINSIC_NAMES:
                    print("%s:%d:%d: ERROR: redefinition of an intrinsic word `%s`. Please choose a different name for your macro." % (token.loc + (token.value, )))
                    exit(1)
                macro = Macro(token.loc, [])
                macros[token.value] = macro
                nesting_depth = 0
                while len(rtokens) > 0:
                    token = rtokens.pop()
                    if token.typ == TokenType.KEYWORD and token.value == Keyword.END and nesting_depth == 0:
                        break
                    else:
                        macro.tokens.append(token)
                        if token.typ == TokenType.KEYWORD:
                            if token.value in [Keyword.IF, Keyword.WHILE, Keyword.MACRO]:
                                nesting_depth += 1
                            elif token.value == Keyword.END:
                                nesting_depth -= 1
                if token.typ != TokenType.KEYWORD or token.value != Keyword.END:
                    print("%s:%d:%d: ERROR: expected `end` at the end of the macro definition but got `%s`" % (token.loc + (token.value, )))
                    exit(1)
            else:
                assert False, 'unreachable';
        else:
            assert False, 'unreachable'


    if len(stack) > 0:
        print('%s:%d:%d: ERROR: unclosed block' % program[stack.pop()].loc)
        exit(1)

    return program

def find_col(line: str, start: int, predicate: Callable[[str], bool]) -> int:
    while start < len(line) and not predicate(line[start]):
        start += 1
    return start

def unescape_string(s: str) -> str:
    # NOTE: unicode_escape assumes latin-1 encoding, so we kinda have
    # to do this weird round trip
    return s.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')

def find_string_literal_end(line: str, start: int) -> int:
    prev = line[start]
    while start < len(line):
        curr = line[start]
        if curr == '"' and prev != '\\':
            break
        prev = curr
        start += 1
    return start

def lex_lines(file_path: str, lines: List[str]) -> Generator[Token, None, None]:
    assert len(TokenType) == 5, 'Exhaustive handling of token types in lex_lines'
    row = 0
    str_literal_buf = ""
    while row < len(lines):
        line = lines[row]
        col = find_col(line, 0, lambda x: not x.isspace())
        col_end = 0 
        while col < len(line):
            loc = (file_path, row + 1, col + 1)
            if line[col] == '"':
                while row < len(lines):
                    start = col
                    if str_literal_buf == "":
                        start += 1
                    else:
                        line = lines[row]
                    col_end = find_string_literal_end(line, start)
                    if col_end >= len(line) or line[col_end] != '"':
                        str_literal_buf += line[start:]
                        row +=1 
                        col = 0
                    else:
                        str_literal_buf += line[start:col_end]
                        break
                if row >= len(lines): 
                    print("%s:%d:%d: ERROR: unclosed string literal" % loc)
                    exit(1)
                text_of_token = str_literal_buf
                str_literal_buf = ""
                yield Token(TokenType.STR, loc, unescape_string(text_of_token))
                col = find_col(line, col_end+1, lambda x: not x.isspace())
            elif line[col] == "'":
                col_end = find_col(line, col+1, lambda x: x == "'")
                if col_end >= len(line) or line[col_end] != "'":
                    print("%s:%d:%d: ERROR: unclosed character literal" % loc)
                    exit(1)
                char_bytes = unescape_string(line[col+1:col_end]).encode('utf-8')
                if len(char_bytes) != 1:
                    print("%s:%d:%d: ERROR: only a single byte is allowed inside of a character literal" % loc)
                    exit(1)
                yield Token(TokenType.CHAR, loc, char_bytes[0])
                col = find_col(line, col_end+1, lambda x: not x.isspace())
            else:
                col_end = find_col(line, col, lambda x: x.isspace())
                text_of_token = line[col:col_end]
                
                try:
                    yield Token(TokenType.INT, loc, int(text_of_token))
                except ValueError:
                    if text_of_token in KEYWORD_NAMES:
                        yield Token(TokenType.KEYWORD, loc, KEYWORD_NAMES[text_of_token])
                    else:
                        if text_of_token.startswith("//"):
                            break
                        yield Token(TokenType.WORD, loc, text_of_token)
                col = find_col(line, col_end, lambda x: not x.isspace())
        row += 1

def lex_file(file_path: str) -> List[Token]:
    with open(file_path, "r", encoding='utf-8') as f:
        return [token for token in lex_lines(file_path, f.readlines())]

def compile_file_to_program(file_path: str, include_paths: List[str]) -> Program:
    return compile_tokens_to_program(lex_file(file_path), include_paths)

def cmd_call_echoed(cmd: List[str], silent: bool=False) -> int:
    if not silent:
        print("[CMD] %s" % " ".join(map(shlex.quote, cmd)))
    return subprocess.call(cmd)

def usage(compiler_name: str):
    print("Usage: %s [OPTIONS] <SUBCOMMAND> [ARGS]" % compiler_name)
    print("  OPTIONS:")
    print("    -debug                Enable debug mode.")
    print("    -I <path>             Add the path to the include search list")
    print("  SUBCOMMAND:")
    print("    sim <file>            Simulate the program")
    print("    com [OPTIONS] <file>  Compile the program")
    print("      OPTIONS:")
    print("        -r                  Run the program after successful compilation")
    print("        -o <file|dir>       Customize the output path")
    print("        -s                  Silent mode. Don't print any info about compilation phases.")
    print("    help                  Print this help to stdout and exit with 0 code")

# TODO: there is no way to access command line arguments

if __name__ == '__main__' and '__file__' in globals():
    argv = sys.argv
    assert len(argv) >= 1
    compiler_name, *argv = argv

    include_paths = ['.', './std/']

    while len(argv) > 0:
        if argv[0] == '-debug':
            argv = argv[1:]
            debug = True
        elif argv[0] == '-I':
            argv = argv[1:]
            if len(argv) == 0:
                usage(compiler_name)
                print("[ERROR] no path is provided for `-I` flag")
                exit(1)
            include_path, *argv = argv
            include_paths.append(include_path)
        else:
            break

    if debug:
        print("[INFO] Debug mode is enabled")

    if len(argv) < 1:
        usage(compiler_name)
        print("[ERROR] no subcommand is provided")
        exit(1)
    subcommand, *argv = argv

    program_path: Optional[str] = None

    if subcommand == "sim":
        if len(argv) < 1:
            usage(compiler_name)
            print("[ERROR] no input file is provided for the simulation")
            exit(1)
        program_path, *argv = argv
        program = compile_file_to_program(program_path, include_paths);
        simulate_little_endian_linux(program)
    elif subcommand == "com":
        silent = False
        run = False
        output_path = None
        while len(argv) > 0:
            arg, *argv = argv
            if arg == '-r':
                run = True
            elif arg == '-s':
                silent = True
            elif arg == '-o':
                if len(argv) == 0:
                    usage(compiler_name)
                    print("[ERROR] no argument is provided for parameter -o")
                    exit(1)
                output_path, *argv = argv
            else:
                program_path = arg
                break

        if program_path is None:
            usage(compiler_name)
            print("[ERROR] no input file is provided for the compilation")
            exit(1)

        basename = None
        basedir = None
        if output_path is not None:
            if path.isdir(output_path):
                basename = path.basename(program_path)
                porth_ext = '.porth'
                if basename.endswith(porth_ext):
                    basename = basename[:-len(porth_ext)]
                basedir = path.dirname(output_path)
            else:
                basename = path.basename(output_path)
                basedir = path.dirname(output_path)
        else:
            basename = path.basename(program_path)
            porth_ext = '.porth'
            if basename.endswith(porth_ext):
                basename = basename[:-len(porth_ext)]
            basedir = path.dirname(program_path)
        
        # if basedir is empty we should "fix" the path appending the current working directory.
        # So we avoid `com -r` to run command from $PATH.
        if basedir == "":
            basedir = os.getcwd()
        basepath = path.join(basedir, basename)

        if not silent:
            print("[INFO] Generating %s" % (basepath + ".asm"))
        program = compile_file_to_program(program_path, include_paths);
        generate_nasm_linux_x86_64(program, basepath + ".asm")
        cmd_call_echoed(["nasm", "-felf64", basepath + ".asm"], silent)
        cmd_call_echoed(["ld", "-o", basepath, basepath + ".o"], silent)
        if run:
            exit(cmd_call_echoed([basepath] + argv, silent))
    elif subcommand == "help":
        usage(compiler_name)
        exit(0)
    else:
        usage(compiler_name)
        print("[ERROR] unknown subcommand %s" % (subcommand))
        exit(1)
