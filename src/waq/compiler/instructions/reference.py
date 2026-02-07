"""Reference instruction compilation (WASM 2.0)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    BinaryOp,
    Copy,
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


def compile_reference_instruction(
    opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a reference instruction.

    Returns True if the instruction was handled.
    """
    # ref.null (0xD0)
    if opcode == 0xD0:
        ref_type = read_operand("u32")  # heaptype (funcref=0x70, externref=0x6F)
        # Determine result type based on heaptype
        if ref_type == 0x70:
            result_type = ValueType.FUNCREF
        elif ref_type == 0x6F:
            result_type = ValueType.EXTERNREF
        else:
            # Other heaptypes (func, extern) map to funcref/externref
            result_type = ValueType.FUNCREF

        result = ctx.stack.new_temp(result_type)
        block.instructions.append(
            Copy(
                result=Temporary(result.name),
                result_type=L,
                value=IntConst(0),  # null = 0
            )
        )
        return True

    # ref.is_null (0xD1)
    if opcode == 0xD1:
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)
        # ref == 0 ? 1 : 0
        block.instructions.append(
            BinaryOp(
                result=Temporary(result.name),
                result_type=W,
                op="ceql",  # compare equal (long)
                left=Temporary(ref.name),
                right=IntConst(0),
            )
        )
        return True

    # ref.func (0xD2)
    if opcode == 0xD2:
        func_idx = read_operand("u32")
        result = ctx.stack.new_temp(ValueType.FUNCREF)
        # Get function address as a reference
        func_name = mod_ctx.get_func_name(func_idx)
        block.instructions.append(
            Copy(
                result=Temporary(result.name),
                result_type=L,
                value=Global(func_name),
            )
        )
        return True

    # ref.eq (0xD3) - compare two references for equality
    if opcode == 0xD3:
        ref2 = ctx.stack.pop()
        ref1 = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            BinaryOp(
                result=Temporary(result.name),
                result_type=W,
                op="ceql",  # compare equal (long)
                left=Temporary(ref1.name),
                right=Temporary(ref2.name),
            )
        )
        return True

    # Note: ref.as_non_null (0xD4), br_on_null (0xD5), br_on_non_null (0xD6)
    # are handled in codegen.py as they involve control flow

    return False
