"""Type conversion instruction compilation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbepy.ir import (
    Call,
    Conversion,
    Copy,
    D,
    Global,
    L,
    S,
    Temporary,
    W,
)

from waq.parser.types import ValueType

if TYPE_CHECKING:
    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext


def compile_conversion_instruction(
    opcode: int,
    ctx: FunctionContext,
    block: Block,
) -> bool:
    """Compile a type conversion instruction.

    Returns True if the instruction was handled.
    """
    # Check if it's a conversion opcode (0xA7-0xBF)
    if opcode < 0xA7 or opcode > 0xBF:
        return False

    stack = ctx.stack

    # i32.wrap_i64 (0xA7)
    if opcode == 0xA7:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        # In QBE, wrapping is just copying with w type (truncates)
        block.instructions.append(
            Copy(
                result=Temporary(result.name),
                result_type=W,
                value=Temporary(a.name),
            )
        )
        return True

    # i32.trunc_f32_s (0xA8)
    if opcode == 0xA8:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Conversion(
                op="stosi",  # single to signed int
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(a.name),
            )
        )
        return True

    # i32.trunc_f32_u (0xA9)
    if opcode == 0xA9:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Conversion(
                op="stoui",  # single to unsigned int
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(a.name),
            )
        )
        return True

    # i32.trunc_f64_s (0xAA)
    if opcode == 0xAA:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Conversion(
                op="dtosi",  # double to signed int
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(a.name),
            )
        )
        return True

    # i32.trunc_f64_u (0xAB)
    if opcode == 0xAB:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Conversion(
                op="dtoui",  # double to unsigned int
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.extend_i32_s (0xAC)
    if opcode == 0xAC:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="extsw",  # extend signed word
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.extend_i32_u (0xAD)
    if opcode == 0xAD:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="extuw",  # extend unsigned word
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.trunc_f32_s (0xAE)
    if opcode == 0xAE:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="stosi",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.trunc_f32_u (0xAF)
    if opcode == 0xAF:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="stoui",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.trunc_f64_s (0xB0)
    if opcode == 0xB0:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="dtosi",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.trunc_f64_u (0xB1)
    if opcode == 0xB1:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="dtoui",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # f32.convert_i32_s (0xB2)
    if opcode == 0xB2:
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Conversion(
                op="swtof",  # signed word to float
                result=Temporary(result.name),
                result_type=S,
                operand=Temporary(a.name),
            )
        )
        return True

    # f32.convert_i32_u (0xB3)
    if opcode == 0xB3:
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Conversion(
                op="uwtof",  # unsigned word to float
                result=Temporary(result.name),
                result_type=S,
                operand=Temporary(a.name),
            )
        )
        return True

    # f32.convert_i64_s (0xB4)
    if opcode == 0xB4:
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Conversion(
                op="sltof",  # signed long to float
                result=Temporary(result.name),
                result_type=S,
                operand=Temporary(a.name),
            )
        )
        return True

    # f32.convert_i64_u (0xB5)
    if opcode == 0xB5:
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Conversion(
                op="ultof",  # unsigned long to float
                result=Temporary(result.name),
                result_type=S,
                operand=Temporary(a.name),
            )
        )
        return True

    # f32.demote_f64 (0xB6)
    if opcode == 0xB6:
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Conversion(
                op="truncd",  # truncate double to single
                result=Temporary(result.name),
                result_type=S,
                operand=Temporary(a.name),
            )
        )
        return True

    # f64.convert_i32_s (0xB7)
    if opcode == 0xB7:
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Conversion(
                op="swtof",  # signed word to float (produces double)
                result=Temporary(result.name),
                result_type=D,
                operand=Temporary(a.name),
            )
        )
        return True

    # f64.convert_i32_u (0xB8)
    if opcode == 0xB8:
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Conversion(
                op="uwtof",
                result=Temporary(result.name),
                result_type=D,
                operand=Temporary(a.name),
            )
        )
        return True

    # f64.convert_i64_s (0xB9)
    if opcode == 0xB9:
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Conversion(
                op="sltof",
                result=Temporary(result.name),
                result_type=D,
                operand=Temporary(a.name),
            )
        )
        return True

    # f64.convert_i64_u (0xBA)
    if opcode == 0xBA:
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Conversion(
                op="ultof",
                result=Temporary(result.name),
                result_type=D,
                operand=Temporary(a.name),
            )
        )
        return True

    # f64.promote_f32 (0xBB)
    if opcode == 0xBB:
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Conversion(
                op="exts",  # extend single to double
                result=Temporary(result.name),
                result_type=D,
                operand=Temporary(a.name),
            )
        )
        return True

    # i32.reinterpret_f32 (0xBC)
    if opcode == 0xBC:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        # Reinterpret is a cast - store and load with different type
        # In QBE we use cast
        block.instructions.append(
            Conversion(
                op="cast",
                result=Temporary(result.name),
                result_type=W,
                operand=Temporary(a.name),
            )
        )
        return True

    # i64.reinterpret_f64 (0xBD)
    if opcode == 0xBD:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="cast",
                result=Temporary(result.name),
                result_type=L,
                operand=Temporary(a.name),
            )
        )
        return True

    # f32.reinterpret_i32 (0xBE)
    if opcode == 0xBE:
        a = stack.pop()
        result = stack.new_temp(ValueType.F32)
        block.instructions.append(
            Conversion(
                op="cast",
                result=Temporary(result.name),
                result_type=S,
                operand=Temporary(a.name),
            )
        )
        return True

    # f64.reinterpret_i64 (0xBF)
    if opcode == 0xBF:
        a = stack.pop()
        result = stack.new_temp(ValueType.F64)
        block.instructions.append(
            Conversion(
                op="cast",
                result=Temporary(result.name),
                result_type=D,
                operand=Temporary(a.name),
            )
        )
        return True

    return False


def compile_saturating_conversion(
    sub_opcode: int,
    ctx: FunctionContext,
    block: Block,
) -> bool:
    """Compile a saturating float-to-int conversion (0xFC prefix).

    These conversions don't trap on overflow, they saturate to min/max.

    Returns True if the instruction was handled.
    """
    stack = ctx.stack

    # i32.trunc_sat_f32_s (0xFC 0x00)
    if sub_opcode == 0x00:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_trunc_sat_f32_s"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i32.trunc_sat_f32_u (0xFC 0x01)
    if sub_opcode == 0x01:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_trunc_sat_f32_u"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i32.trunc_sat_f64_s (0xFC 0x02)
    if sub_opcode == 0x02:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_trunc_sat_f64_s"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i32.trunc_sat_f64_u (0xFC 0x03)
    if sub_opcode == 0x03:
        a = stack.pop()
        result = stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i32_trunc_sat_f64_u"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i64.trunc_sat_f32_s (0xFC 0x04)
    if sub_opcode == 0x04:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_trunc_sat_f32_s"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # i64.trunc_sat_f32_u (0xFC 0x05)
    if sub_opcode == 0x05:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_trunc_sat_f32_u"),
                args=[(S, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # i64.trunc_sat_f64_s (0xFC 0x06)
    if sub_opcode == 0x06:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_trunc_sat_f64_s"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # i64.trunc_sat_f64_u (0xFC 0x07)
    if sub_opcode == 0x07:
        a = stack.pop()
        result = stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_i64_trunc_sat_f64_u"),
                args=[(D, Temporary(a.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    return False
