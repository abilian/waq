"""Table instruction compilation (WASM 2.0)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    Call,
    Global,
    IntConst,
    L,
    Temporary,
    W,
)

from waq.parser.types import ValueType

if TYPE_CHECKING:
    from collections.abc import Callable

    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext, ModuleContext


def compile_table_instruction(
    opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,  # noqa: ARG001
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a table instruction.

    Returns True if the instruction was handled.
    """
    # table.get (0x25)
    if opcode == 0x25:
        table_idx = read_operand("u32")
        elem_idx = ctx.stack.pop()
        # Result type is funcref/externref - we represent as i64 (pointer)
        result = ctx.stack.new_temp(ValueType.I64)
        block.instructions.append(
            Call(
                target=Global("__wasm_table_get"),
                args=[
                    (W, IntConst(table_idx)),
                    (W, Temporary(elem_idx.name)),
                ],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # table.set (0x26)
    if opcode == 0x26:
        table_idx = read_operand("u32")
        ref = ctx.stack.pop()
        elem_idx = ctx.stack.pop()
        block.instructions.append(
            Call(
                target=Global("__wasm_table_set"),
                args=[
                    (W, IntConst(table_idx)),
                    (W, Temporary(elem_idx.name)),
                    (L, Temporary(ref.name)),
                ],
            )
        )
        return True

    return False


def compile_table_bulk_instruction(
    sub_opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,  # noqa: ARG001
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a table bulk instruction (0xFC prefix).

    Returns True if the instruction was handled.
    """
    # table.init (0xFC 0x0C)
    if sub_opcode == 0x0C:
        elem_idx = read_operand("u32")
        table_idx = read_operand("u32")

        # Stack: [dest, src, len] -> []
        length = ctx.stack.pop()
        src = ctx.stack.pop()
        dest = ctx.stack.pop()

        block.instructions.append(
            Call(
                target=Global("__wasm_table_init"),
                args=[
                    (W, IntConst(table_idx)),
                    (W, IntConst(elem_idx)),
                    (W, Temporary(dest.name)),
                    (W, Temporary(src.name)),
                    (W, Temporary(length.name)),
                ],
            )
        )
        return True

    # elem.drop (0xFC 0x0D)
    if sub_opcode == 0x0D:
        elem_idx = read_operand("u32")
        block.instructions.append(
            Call(
                target=Global("__wasm_elem_drop"),
                args=[(W, IntConst(elem_idx))],
            )
        )
        return True

    # table.copy (0xFC 0x0E)
    if sub_opcode == 0x0E:
        dest_table = read_operand("u32")
        src_table = read_operand("u32")

        # Stack: [dest, src, len] -> []
        length = ctx.stack.pop()
        src = ctx.stack.pop()
        dest = ctx.stack.pop()

        block.instructions.append(
            Call(
                target=Global("__wasm_table_copy"),
                args=[
                    (W, IntConst(dest_table)),
                    (W, IntConst(src_table)),
                    (W, Temporary(dest.name)),
                    (W, Temporary(src.name)),
                    (W, Temporary(length.name)),
                ],
            )
        )
        return True

    # table.grow (0xFC 0x0F)
    if sub_opcode == 0x0F:
        table_idx = read_operand("u32")

        # Stack: [ref, delta] -> [old_size]
        delta = ctx.stack.pop()
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)

        block.instructions.append(
            Call(
                target=Global("__wasm_table_grow"),
                args=[
                    (W, IntConst(table_idx)),
                    (L, Temporary(ref.name)),
                    (W, Temporary(delta.name)),
                ],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # table.size (0xFC 0x10)
    if sub_opcode == 0x10:
        table_idx = read_operand("u32")
        result = ctx.stack.new_temp(ValueType.I32)

        block.instructions.append(
            Call(
                target=Global("__wasm_table_size_op"),
                args=[(W, IntConst(table_idx))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # table.fill (0xFC 0x11)
    if sub_opcode == 0x11:
        table_idx = read_operand("u32")

        # Stack: [dest, ref, len] -> []
        length = ctx.stack.pop()
        ref = ctx.stack.pop()
        dest = ctx.stack.pop()

        block.instructions.append(
            Call(
                target=Global("__wasm_table_fill"),
                args=[
                    (W, IntConst(table_idx)),
                    (W, Temporary(dest.name)),
                    (L, Temporary(ref.name)),
                    (W, Temporary(length.name)),
                ],
            )
        )
        return True

    return False
