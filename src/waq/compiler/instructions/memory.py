"""Memory instruction compilation (load, store, memory.size, memory.grow)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    BinaryOp,
    Call,
    Conversion,
    Global,
    IntConst,
    L,
    Load,
    Store,
    Temporary,
    W,
)

from waq.parser.types import ValueType

if TYPE_CHECKING:
    from collections.abc import Callable

    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext, ModuleContext


def _vtype_to_ir_type(vtype: ValueType):
    """Convert WASM ValueType to qbepy IR type."""
    from qbepy.ir import D, S  # noqa: PLC0415

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


def _is_memory64(ctx: FunctionContext, memory_idx: int = 0) -> bool:
    """Check if memory at given index is Memory64."""
    if memory_idx < len(ctx.module.memories):
        return ctx.module.memories[memory_idx].is_memory64
    return False


def _get_memory_base(
    ctx: FunctionContext,
    block: Block,
    memory_idx: int = 0,
) -> str:
    """Get the memory base pointer for the given memory index.

    Returns the name of a temporary holding the base pointer.
    For single memory (idx=0), uses __wasm_memory global.
    For multiple memories (idx>0), calls __wasm_memory_base(idx).
    """
    base_temp = ctx.stack.new_temp_no_push(ValueType.I64)

    if memory_idx == 0 and len(ctx.module.memories) <= 1:
        # Optimization: single memory case, use direct global
        block.instructions.append(
            Load(
                result=Temporary(base_temp.name),
                result_type=L,
                address=Global("__wasm_memory"),
            )
        )
    else:
        # Multiple memories: call runtime to get base pointer
        block.instructions.append(
            Call(
                target=Global("__wasm_memory_base"),
                args=[(W, IntConst(memory_idx))],
                result=Temporary(base_temp.name),
                result_type=L,
            )
        )

    return base_temp.name


def compile_memory_instruction(
    opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a memory instruction.

    Returns True if the instruction was handled.
    """
    # Load instructions: 0x28-0x35
    if 0x28 <= opcode <= 0x35:
        return _compile_load(opcode, ctx, block, read_operand)

    # Store instructions: 0x36-0x3E
    if 0x36 <= opcode <= 0x3E:
        return _compile_store(opcode, ctx, block, read_operand)

    # memory.size (0x3F)
    if opcode == 0x3F:
        memory_idx = read_operand("u32")
        is_mem64 = _is_memory64(ctx, memory_idx)

        if is_mem64:
            # Memory64: returns i64
            result = ctx.stack.new_temp(ValueType.I64)
            block.instructions.append(
                Call(
                    target=Global("__wasm_memory_size_pages64"),
                    args=[(W, IntConst(memory_idx))],
                    result=Temporary(result.name),
                    result_type=L,
                )
            )
        else:
            # Memory32: returns i32
            result = ctx.stack.new_temp(ValueType.I32)
            block.instructions.append(
                Call(
                    target=Global("__wasm_memory_size_pages"),
                    args=[(W, IntConst(memory_idx))],
                    result=Temporary(result.name),
                    result_type=W,
                )
            )
        return True

    # memory.grow (0x40)
    if opcode == 0x40:
        memory_idx = read_operand("u32")
        is_mem64 = _is_memory64(ctx, memory_idx)
        pages = ctx.stack.pop()

        if is_mem64:
            # Memory64: takes/returns i64
            result = ctx.stack.new_temp(ValueType.I64)
            block.instructions.append(
                Call(
                    target=Global("__wasm_memory_grow64"),
                    args=[(W, IntConst(memory_idx)), (L, Temporary(pages.name))],
                    result=Temporary(result.name),
                    result_type=L,
                )
            )
        else:
            # Memory32: takes/returns i32
            result = ctx.stack.new_temp(ValueType.I32)
            block.instructions.append(
                Call(
                    target=Global("__wasm_memory_grow"),
                    args=[(W, IntConst(memory_idx)), (W, Temporary(pages.name))],
                    result=Temporary(result.name),
                    result_type=W,
                )
            )
        return True

    return False


def _compile_load(
    opcode: int,
    ctx: FunctionContext,
    block: Block,
    read_operand: Callable[[str], Any],
    memory_idx: int = 0,
) -> bool:
    """Compile a load instruction."""
    # Read memarg: align (unused), offset
    _align = read_operand("u32")
    offset = read_operand("u32")

    # Pop address from stack
    addr = ctx.stack.pop()

    # Check if this is memory64
    is_mem64 = _is_memory64(ctx, memory_idx)

    # Calculate effective address: base + addr + offset
    # Get memory base pointer (handles multiple memories)
    base_temp_name = _get_memory_base(ctx, block, memory_idx)

    if is_mem64:
        # Memory64: address is already i64
        addr64_temp = addr
    else:
        # Memory32: extend address to 64-bit (it's i32)
        addr64_temp = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="extuw",  # Extend unsigned word to long
                result=Temporary(addr64_temp.name),
                result_type=L,
                operand=Temporary(addr.name),
            )
        )

    # Add base + addr
    eff_addr = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(eff_addr.name),
            result_type=L,
            op="add",
            left=Temporary(base_temp_name),
            right=Temporary(addr64_temp.name),
        )
    )

    # Add offset if non-zero
    if offset > 0:
        eff_addr2 = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(eff_addr2.name),
                result_type=L,
                op="add",
                left=Temporary(eff_addr.name),
                right=IntConst(offset),
            )
        )
        eff_addr = eff_addr2

    # Determine load type based on opcode
    load_info = _LOAD_OPCODES.get(opcode)
    if load_info is None:
        return False

    result_type, load_op = load_info
    result = ctx.stack.new_temp(result_type)
    qbe_type = _vtype_to_ir_type(result_type)

    block.instructions.append(
        Load(
            result=Temporary(result.name),
            result_type=qbe_type,
            address=Temporary(eff_addr.name),
            load_type=load_op,
        )
    )
    return True


def _compile_store(
    opcode: int,
    ctx: FunctionContext,
    block: Block,
    read_operand: Callable[[str], Any],
    memory_idx: int = 0,
) -> bool:
    """Compile a store instruction."""
    # Read memarg: align (unused), offset
    _align = read_operand("u32")
    offset = read_operand("u32")

    # Pop value and address from stack
    value = ctx.stack.pop()
    addr = ctx.stack.pop()

    # Check if this is memory64
    is_mem64 = _is_memory64(ctx, memory_idx)

    # Calculate effective address (same as load)
    # Get memory base pointer (handles multiple memories)
    base_temp_name = _get_memory_base(ctx, block, memory_idx)

    if is_mem64:
        # Memory64: address is already i64
        addr64_temp = addr
    else:
        # Memory32: extend address to 64-bit
        addr64_temp = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            Conversion(
                op="extuw",
                result=Temporary(addr64_temp.name),
                result_type=L,
                operand=Temporary(addr.name),
            )
        )

    eff_addr = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(eff_addr.name),
            result_type=L,
            op="add",
            left=Temporary(base_temp_name),
            right=Temporary(addr64_temp.name),
        )
    )

    if offset > 0:
        eff_addr2 = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(eff_addr2.name),
                result_type=L,
                op="add",
                left=Temporary(eff_addr.name),
                right=IntConst(offset),
            )
        )
        eff_addr = eff_addr2

    # Determine store type based on opcode
    store_op = _STORE_OPCODES.get(opcode)
    if store_op is None:
        return False

    block.instructions.append(
        Store(
            address=Temporary(eff_addr.name),
            value=Temporary(value.name),
            store_type=store_op,
        )
    )
    return True


# Load opcode mappings: opcode -> (result_type, load_op)
_LOAD_OPCODES = {
    0x28: (ValueType.I32, "loadw"),  # i32.load
    0x29: (ValueType.I64, "loadl"),  # i64.load
    0x2A: (ValueType.F32, "loads"),  # f32.load
    0x2B: (ValueType.F64, "loadd"),  # f64.load
    0x2C: (ValueType.I32, "loadsb"),  # i32.load8_s
    0x2D: (ValueType.I32, "loadub"),  # i32.load8_u
    0x2E: (ValueType.I32, "loadsh"),  # i32.load16_s
    0x2F: (ValueType.I32, "loaduh"),  # i32.load16_u
    0x30: (ValueType.I64, "loadsb"),  # i64.load8_s
    0x31: (ValueType.I64, "loadub"),  # i64.load8_u
    0x32: (ValueType.I64, "loadsh"),  # i64.load16_s
    0x33: (ValueType.I64, "loaduh"),  # i64.load16_u
    0x34: (ValueType.I64, "loadsw"),  # i64.load32_s
    0x35: (ValueType.I64, "loaduw"),  # i64.load32_u
}

# Store opcode mappings: opcode -> store_op
_STORE_OPCODES = {
    0x36: "storew",  # i32.store
    0x37: "storel",  # i64.store
    0x38: "stores",  # f32.store
    0x39: "stored",  # f64.store
    0x3A: "storeb",  # i32.store8
    0x3B: "storeh",  # i32.store16
    0x3C: "storeb",  # i64.store8
    0x3D: "storeh",  # i64.store16
    0x3E: "storew",  # i64.store32
}


def compile_bulk_memory_instruction(
    sub_opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a bulk memory instruction (0xFC prefix).

    Returns True if the instruction was handled.
    """
    # memory.init (0xFC 0x08)
    if sub_opcode == 0x08:
        data_idx = read_operand("u32")
        _mem_idx = read_operand("u32")  # Always 0 in WASM 1.0

        # Stack: [dest, src_offset, len] -> []
        length = ctx.stack.pop()
        src_offset = ctx.stack.pop()
        dest = ctx.stack.pop()

        block.instructions.append(
            Call(
                target=Global("__wasm_memory_init_seg"),
                args=[
                    (W, IntConst(data_idx)),
                    (W, Temporary(dest.name)),
                    (W, Temporary(src_offset.name)),
                    (W, Temporary(length.name)),
                ],
            )
        )
        return True

    # data.drop (0xFC 0x09)
    if sub_opcode == 0x09:
        data_idx = read_operand("u32")

        block.instructions.append(
            Call(
                target=Global("__wasm_data_drop"),
                args=[(W, IntConst(data_idx))],
            )
        )
        return True

    # memory.copy (0xFC 0x0A)
    if sub_opcode == 0x0A:
        _dest_mem = read_operand("u32")  # Always 0 in WASM 1.0
        _src_mem = read_operand("u32")  # Always 0 in WASM 1.0

        # Stack: [dest, src, len] -> []
        length = ctx.stack.pop()
        src = ctx.stack.pop()
        dest = ctx.stack.pop()

        block.instructions.append(
            Call(
                target=Global("__wasm_memory_copy"),
                args=[
                    (W, Temporary(dest.name)),
                    (W, Temporary(src.name)),
                    (W, Temporary(length.name)),
                ],
            )
        )
        return True

    # memory.fill (0xFC 0x0B)
    if sub_opcode == 0x0B:
        _mem_idx = read_operand("u32")  # Always 0 in WASM 1.0

        # Stack: [dest, val, len] -> []
        length = ctx.stack.pop()
        val = ctx.stack.pop()
        dest = ctx.stack.pop()

        block.instructions.append(
            Call(
                target=Global("__wasm_memory_fill"),
                args=[
                    (W, Temporary(dest.name)),
                    (W, Temporary(val.name)),
                    (W, Temporary(length.name)),
                ],
            )
        )
        return True

    return False
