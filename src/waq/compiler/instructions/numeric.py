"""Numeric instruction compilation (i32, i64, f32, f64 operations)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    BinaryOp,
    Call,
    Comparison,
    Copy,
    D,
    FloatConst,
    Global,
    IntConst,
    L,
    S,
    Temporary,
    W,
)

from waq.parser.types import ValueType

if TYPE_CHECKING:
    from collections.abc import Callable

    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext


def _vtype_to_ir_type(vtype: ValueType):
    """Convert WASM ValueType to qbepy IR type."""
    if vtype == ValueType.I32:
        return W
    if vtype == ValueType.I64:
        return L
    if vtype == ValueType.F32:
        return S
    if vtype == ValueType.F64:
        return D
    if vtype in (ValueType.FUNCREF, ValueType.EXTERNREF):
        return L  # Reference types are pointers (64-bit)
    raise ValueError(f"unknown value type: {vtype}")


# WASM opcode ranges
I32_OPS_START = 0x41
I64_OPS_START = 0x42
F32_OPS_START = 0x43
F64_OPS_START = 0x44


def compile_numeric_instruction(
    opcode: int,
    ctx: FunctionContext,
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a numeric instruction.

    Returns True if the instruction was handled.
    """
    # Constants
    if opcode == 0x41:  # i32.const
        value = read_operand("s32")
        temp = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            Copy(result=Temporary(temp.name), result_type=W, value=IntConst(value))
        )
        return True

    if opcode == 0x42:  # i64.const
        value = read_operand("s64")
        temp = ctx.stack.new_temp(ValueType.I64)
        block.instructions.append(
            Copy(result=Temporary(temp.name), result_type=L, value=IntConst(value))
        )
        return True

    if opcode == 0x43:  # f32.const
        value = read_operand("f32")
        temp = ctx.stack.new_temp(ValueType.F32)
        block.instructions.append(
            Copy(result=Temporary(temp.name), result_type=S, value=FloatConst(value))
        )
        return True

    if opcode == 0x44:  # f64.const
        value = read_operand("f64")
        temp = ctx.stack.new_temp(ValueType.F64)
        block.instructions.append(
            Copy(result=Temporary(temp.name), result_type=D, value=FloatConst(value))
        )
        return True

    # i32 operations: comparisons (0x45-0x4F) and unary/arithmetic (0x67-0x78)
    if 0x45 <= opcode <= 0x4F or 0x67 <= opcode <= 0x78:
        return _compile_i32_op(opcode, ctx, block)

    # i64 operations: comparisons (0x50-0x5A) and unary/arithmetic (0x79-0x8A)
    if 0x50 <= opcode <= 0x5A or 0x79 <= opcode <= 0x8A:
        return _compile_i64_op(opcode, ctx, block)

    # f32 operations: comparisons (0x5B-0x60) and unary/arithmetic (0x8B-0x98)
    if 0x5B <= opcode <= 0x60 or 0x8B <= opcode <= 0x98:
        return _compile_f32_op(opcode, ctx, block)

    # f64 operations: comparisons (0x61-0x66) and unary/arithmetic (0x99-0xA6)
    if 0x61 <= opcode <= 0x66 or 0x99 <= opcode <= 0xA6:
        return _compile_f64_op(opcode, ctx, block)

    # Sign extension operations (WASM 2.0)
    if 0xC0 <= opcode <= 0xC4:
        return _compile_sign_extension(opcode, ctx, block)

    return False


def _compile_i32_op(opcode: int, ctx: FunctionContext, block: Block) -> bool:
    """Compile i32 operations."""
    stack = ctx.stack

    # i32.eqz
    if opcode == 0x45:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Comparison(
                result=Temporary(result.name),
                result_type=W,
                op="ceqw",
                left=Temporary(a.name),
                right=IntConst(0),
            )
        )
        return True

    # i32 comparisons (binary)
    if 0x46 <= opcode <= 0x4F:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        op = _i32_cmp_ops[opcode - 0x46]
        block.instructions.append(
            Comparison(
                result=Temporary(result.name),
                result_type=W,
                op=op,
                left=Temporary(a.name),
                right=Temporary(b.name),
            )
        )
        return True

    # i32.clz, i32.ctz, i32.popcnt (unary, need runtime)
    if opcode == 0x67:  # i32.clz
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_clz"),
                args=[(W, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    if opcode == 0x68:  # i32.ctz
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_ctz"),
                args=[(W, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    if opcode == 0x69:  # i32.popcnt
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_popcnt"),
                args=[(W, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i32.rotl and i32.rotr (need runtime)
    if opcode == 0x77:  # i32.rotl
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_rotl"),
                args=[(W, Temporary(a.name)), (W, Temporary(b.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    if opcode == 0x78:  # i32.rotr
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_rotr"),
                args=[(W, Temporary(a.name)), (W, Temporary(b.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i32 binary arithmetic
    if 0x6A <= opcode <= 0x76:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        op = _i32_arith_ops.get(opcode)
        if op is None:
            return False
        block.instructions.append(
            BinaryOp(
                result=Temporary(result.name),
                result_type=W,
                op=op,
                left=Temporary(a.name),
                right=Temporary(b.name),
            )
        )
        return True

    return False


def _compile_i64_op(opcode: int, ctx: FunctionContext, block: Block) -> bool:
    """Compile i64 operations."""
    stack = ctx.stack

    # i64.eqz
    if opcode == 0x50:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)  # Result is i32
        block.instructions.append(
            Comparison(
                result=Temporary(result.name),
                result_type=W,
                op="ceql",
                left=Temporary(a.name),
                right=IntConst(0),
            )
        )
        return True

    # i64 comparisons (binary) - result is i32
    if 0x51 <= opcode <= 0x5A:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        op = _i64_cmp_ops[opcode - 0x51]
        block.instructions.append(
            Comparison(
                result=Temporary(result.name),
                result_type=W,
                op=op,
                left=Temporary(a.name),
                right=Temporary(b.name),
            )
        )
        return True

    # i64.clz, i64.ctz, i64.popcnt
    if opcode == 0x79:  # i64.clz
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_clz"),
                args=[(L, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    if opcode == 0x7A:  # i64.ctz
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_ctz"),
                args=[(L, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    if opcode == 0x7B:  # i64.popcnt
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_popcnt"),
                args=[(L, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # i64.rotl and i64.rotr (need runtime)
    if opcode == 0x89:  # i64.rotl
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_rotl"),
                args=[(L, Temporary(a.name)), (L, Temporary(b.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    if opcode == 0x8A:  # i64.rotr
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_rotr"),
                args=[(L, Temporary(a.name)), (L, Temporary(b.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # i64 binary arithmetic
    if 0x7C <= opcode <= 0x88:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        op = _i64_arith_ops.get(opcode)
        if op is None:
            return False
        block.instructions.append(
            BinaryOp(
                result=Temporary(result.name),
                result_type=L,
                op=op,
                left=Temporary(a.name),
                right=Temporary(b.name),
            )
        )
        return True

    return False


def _compile_f32_op(opcode: int, ctx: FunctionContext, block: Block) -> bool:
    """Compile f32 operations."""
    stack = ctx.stack

    # f32 comparisons - result is i32
    if 0x5B <= opcode <= 0x60:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        op = _f32_cmp_ops[opcode - 0x5B]
        block.instructions.append(
            Comparison(
                result=Temporary(result.name),
                result_type=W,
                op=op,
                left=Temporary(a.name),
                right=Temporary(b.name),
            )
        )
        return True

    # f32 unary operations
    if opcode == 0x8B:  # f32.abs
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Call(
                target=Global("__wasm_f32_abs"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=S,
            )
        )
        return True

    if opcode == 0x8C:  # f32.neg
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        from qbepy.ir import UnaryOp  # noqa: PLC0415

        block.instructions.append(
            UnaryOp(
                result=Temporary(result.name),
                result_type=S,
                op="neg",
                operand=Temporary(a.name),
            )
        )
        return True

    if opcode == 0x8D:  # f32.ceil
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Call(
                target=Global("__wasm_f32_ceil"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=S,
            )
        )
        return True

    if opcode == 0x8E:  # f32.floor
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Call(
                target=Global("__wasm_f32_floor"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=S,
            )
        )
        return True

    if opcode == 0x8F:  # f32.trunc
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Call(
                target=Global("__wasm_f32_trunc"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=S,
            )
        )
        return True

    if opcode == 0x90:  # f32.nearest
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Call(
                target=Global("__wasm_f32_nearest"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=S,
            )
        )
        return True

    if opcode == 0x91:  # f32.sqrt
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Call(
                target=Global("__wasm_f32_sqrt"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=S,
            )
        )
        return True

    # f32 binary operations
    if 0x92 <= opcode <= 0x98:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        op = _f32_arith_ops.get(opcode)
        if op is None:
            return False
        if op.startswith("$"):
            # Runtime function
            block.instructions.append(
                Call(
                    target=Global(op),
                    args=[(S, Temporary(a.name)), (S, Temporary(b.name))],
                    result=Temporary(result.name),
                    result_type=S,
                )
            )
        else:
            block.instructions.append(
                BinaryOp(
                    result=Temporary(result.name),
                    result_type=S,
                    op=op,
                    left=Temporary(a.name),
                    right=Temporary(b.name),
                )
            )
        return True

    return False


def _compile_f64_op(opcode: int, ctx: FunctionContext, block: Block) -> bool:
    """Compile f64 operations."""
    stack = ctx.stack

    # f64 comparisons - result is i32
    if 0x61 <= opcode <= 0x66:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        op = _f64_cmp_ops[opcode - 0x61]
        block.instructions.append(
            Comparison(
                result=Temporary(result.name),
                result_type=W,
                op=op,
                left=Temporary(a.name),
                right=Temporary(b.name),
            )
        )
        return True

    # f64 unary operations
    if opcode == 0x99:  # f64.abs
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Call(
                target=Global("__wasm_f64_abs"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=D,
            )
        )
        return True

    if opcode == 0x9A:  # f64.neg
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        from qbepy.ir import UnaryOp  # noqa: PLC0415

        block.instructions.append(
            UnaryOp(
                result=Temporary(result.name),
                result_type=D,
                op="neg",
                operand=Temporary(a.name),
            )
        )
        return True

    if opcode == 0x9B:  # f64.ceil
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Call(
                target=Global("__wasm_f64_ceil"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=D,
            )
        )
        return True

    if opcode == 0x9C:  # f64.floor
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Call(
                target=Global("__wasm_f64_floor"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=D,
            )
        )
        return True

    if opcode == 0x9D:  # f64.trunc
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Call(
                target=Global("__wasm_f64_trunc"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=D,
            )
        )
        return True

    if opcode == 0x9E:  # f64.nearest
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Call(
                target=Global("__wasm_f64_nearest"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=D,
            )
        )
        return True

    if opcode == 0x9F:  # f64.sqrt
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Call(
                target=Global("__wasm_f64_sqrt"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=D,
            )
        )
        return True

    # f64 binary operations
    if 0xA0 <= opcode <= 0xA6:
        b = stack.pop()
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        op = _f64_arith_ops.get(opcode)
        if op is None:
            return False
        if op.startswith("$"):
            # Runtime function
            block.instructions.append(
                Call(
                    target=Global(op),
                    args=[(D, Temporary(a.name)), (D, Temporary(b.name))],
                    result=Temporary(result.name),
                    result_type=D,
                )
            )
        else:
            block.instructions.append(
                BinaryOp(
                    result=Temporary(result.name),
                    result_type=D,
                    op=op,
                    left=Temporary(a.name),
                    right=Temporary(b.name),
                )
            )
        return True

    return False


# Opcode to QBE instruction mappings

_i32_cmp_ops = [
    "ceqw",  # 0x46: i32.eq
    "cnew",  # 0x47: i32.ne
    "csltw",  # 0x48: i32.lt_s
    "cultw",  # 0x49: i32.lt_u
    "csgtw",  # 0x4A: i32.gt_s
    "cugtw",  # 0x4B: i32.gt_u
    "cslew",  # 0x4C: i32.le_s
    "culew",  # 0x4D: i32.le_u
    "csgew",  # 0x4E: i32.ge_s
    "cugew",  # 0x4F: i32.ge_u
]

_i32_arith_ops = {
    0x6A: "add",  # i32.add
    0x6B: "sub",  # i32.sub
    0x6C: "mul",  # i32.mul
    0x6D: "div",  # i32.div_s
    0x6E: "udiv",  # i32.div_u
    0x6F: "rem",  # i32.rem_s
    0x70: "urem",  # i32.rem_u
    0x71: "and",  # i32.and
    0x72: "or",  # i32.or
    0x73: "xor",  # i32.xor
    0x74: "shl",  # i32.shl
    0x75: "sar",  # i32.shr_s
    0x76: "shr",  # i32.shr_u
    # 0x77: i32.rotl - needs runtime
    # 0x78: i32.rotr - needs runtime
}

_i64_cmp_ops = [
    "ceql",  # 0x51: i64.eq
    "cnel",  # 0x52: i64.ne
    "csltl",  # 0x53: i64.lt_s
    "cultl",  # 0x54: i64.lt_u
    "csgtl",  # 0x55: i64.gt_s
    "cugtl",  # 0x56: i64.gt_u
    "cslel",  # 0x57: i64.le_s
    "culel",  # 0x58: i64.le_u
    "csgel",  # 0x59: i64.ge_s
    "cugel",  # 0x5A: i64.ge_u
]

_i64_arith_ops = {
    0x7C: "add",  # i64.add
    0x7D: "sub",  # i64.sub
    0x7E: "mul",  # i64.mul
    0x7F: "div",  # i64.div_s
    0x80: "udiv",  # i64.div_u
    0x81: "rem",  # i64.rem_s
    0x82: "urem",  # i64.rem_u
    0x83: "and",  # i64.and
    0x84: "or",  # i64.or
    0x85: "xor",  # i64.xor
    0x86: "shl",  # i64.shl
    0x87: "sar",  # i64.shr_s
    0x88: "shr",  # i64.shr_u
    # 0x89: i64.rotl - needs runtime
    # 0x8A: i64.rotr - needs runtime
}

_f32_cmp_ops = [
    "ceqs",  # 0x5B: f32.eq
    "cnes",  # 0x5C: f32.ne
    "clts",  # 0x5D: f32.lt
    "cgts",  # 0x5E: f32.gt
    "cles",  # 0x5F: f32.le
    "cges",  # 0x60: f32.ge
]

_f32_arith_ops = {
    0x92: "add",  # f32.add
    0x93: "sub",  # f32.sub
    0x94: "mul",  # f32.mul
    0x95: "div",  # f32.div
    0x96: "__wasm_f32_min",  # f32.min
    0x97: "__wasm_f32_max",  # f32.max
    0x98: "__wasm_f32_copysign",  # f32.copysign
}

_f64_cmp_ops = [
    "ceqd",  # 0x61: f64.eq
    "cned",  # 0x62: f64.ne
    "cltd",  # 0x63: f64.lt
    "cgtd",  # 0x64: f64.gt
    "cled",  # 0x65: f64.le
    "cged",  # 0x66: f64.ge
]

_f64_arith_ops = {
    0xA0: "add",  # f64.add
    0xA1: "sub",  # f64.sub
    0xA2: "mul",  # f64.mul
    0xA3: "div",  # f64.div
    0xA4: "__wasm_f64_min",  # f64.min
    0xA5: "__wasm_f64_max",  # f64.max
    0xA6: "__wasm_f64_copysign",  # f64.copysign
}


def _compile_sign_extension(opcode: int, ctx: FunctionContext, block: Block) -> bool:
    """Compile sign extension operations (WASM 2.0).

    0xC0: i32.extend8_s - sign extend i8 to i32
    0xC1: i32.extend16_s - sign extend i16 to i32
    0xC2: i64.extend8_s - sign extend i8 to i64
    0xC3: i64.extend16_s - sign extend i16 to i64
    0xC4: i64.extend32_s - sign extend i32 to i64
    """
    from qbepy.ir import Conversion  # noqa: PLC0415

    stack = ctx.stack

    # i32.extend8_s (0xC0)
    if opcode == 0xC0:
        val = stack.pop()
        result = stack.new_temp(ValueType.I32)
        # Sign extend byte to word: extsb
        block.instructions.append(
            Conversion(
                op="extsb",
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(val.name),
            )
        )
        return True

    # i32.extend16_s (0xC1)
    if opcode == 0xC1:
        val = stack.pop()
        result = stack.new_temp(ValueType.I32)
        # Sign extend halfword to word: extsh
        block.instructions.append(
            Conversion(
                op="extsh",
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(val.name),
            )
        )
        return True

    # i64.extend8_s (0xC2)
    if opcode == 0xC2:
        val = stack.pop()
        result = stack.new_temp(ValueType.I64)
        # Sign extend byte to long: extsb
        block.instructions.append(
            Conversion(
                op="extsb",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(val.name),
            )
        )
        return True

    # i64.extend16_s (0xC3)
    if opcode == 0xC3:
        val = stack.pop()
        result = stack.new_temp(ValueType.I64)
        # Sign extend halfword to long: extsh
        block.instructions.append(
            Conversion(
                op="extsh",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(val.name),
            )
        )
        return True

    # i64.extend32_s (0xC4)
    if opcode == 0xC4:
        val = stack.pop()
        result = stack.new_temp(ValueType.I64)
        # Sign extend word to long: extsw
        block.instructions.append(
            Conversion(
                op="extsw",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(val.name),
            )
        )
        return True

    return False
