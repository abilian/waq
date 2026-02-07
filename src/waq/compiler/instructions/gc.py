"""GC instruction compilation (WASM GC proposal)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    BinaryOp,
    Call,
    Copy,
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


def compile_gc_instruction(
    sub_opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a GC instruction (0xFB prefix).

    Returns True if the instruction was handled.
    """
    # struct.new (0xFB 0x00)
    if sub_opcode == 0x00:
        type_idx = read_operand("u32")
        struct_type = ctx.module.get_struct_type(type_idx)

        # Pop field values from stack (in reverse order)
        field_values = []
        for _field in reversed(struct_type.fields):
            field_values.insert(0, ctx.stack.pop())

        # Allocate struct via runtime
        result = ctx.stack.new_temp(ValueType.STRUCTREF)
        block.instructions.append(
            Call(
                target=Global("__wasm_struct_new"),
                args=[(W, IntConst(type_idx)), (W, IntConst(len(struct_type.fields)))],
                result=Temporary(result.name),
                result_type=L,
            )
        )

        # Store field values
        for i, (field_val, field_type) in enumerate(
            zip(field_values, struct_type.fields, strict=True)
        ):
            offset = ctx.stack.new_temp_no_push(ValueType.I64)
            block.instructions.append(
                BinaryOp(
                    result=Temporary(offset.name),
                    result_type=L,
                    op="add",
                    left=Temporary(result.name),
                    right=IntConst(i * 8),  # 8 bytes per field (simplified)
                )
            )
            block.instructions.append(
                Store(
                    store_type=L,
                    address=Temporary(offset.name),
                    value=Temporary(field_val.name),
                )
            )

        return True

    # struct.new_default (0xFB 0x01)
    if sub_opcode == 0x01:
        type_idx = read_operand("u32")
        struct_type = ctx.module.get_struct_type(type_idx)

        # Allocate struct with default (zero) values
        result = ctx.stack.new_temp(ValueType.STRUCTREF)
        block.instructions.append(
            Call(
                target=Global("__wasm_struct_new_default"),
                args=[(W, IntConst(type_idx)), (W, IntConst(len(struct_type.fields)))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # struct.get (0xFB 0x02)
    if sub_opcode == 0x02:
        type_idx = read_operand("u32")
        field_idx = read_operand("u32")
        struct_type = ctx.module.get_struct_type(type_idx)
        field_type = struct_type.fields[field_idx]

        struct_ref = ctx.stack.pop()

        # Calculate field offset and load
        offset = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(offset.name),
                result_type=L,
                op="add",
                left=Temporary(struct_ref.name),
                right=IntConst(field_idx * 8),
            )
        )

        # Determine result type
        result_vtype = _storage_type_to_value_type(field_type.storage_type)
        result = ctx.stack.new_temp(result_vtype)
        block.instructions.append(
            Load(
                result=Temporary(result.name),
                result_type=L,
                address=Temporary(offset.name),
            )
        )
        return True

    # struct.get_s (0xFB 0x03) - signed extend for packed types
    if sub_opcode == 0x03:
        type_idx = read_operand("u32")
        field_idx = read_operand("u32")
        _compile_struct_get(ctx, block, type_idx, field_idx, signed=True)
        return True

    # struct.get_u (0xFB 0x04) - unsigned extend for packed types
    if sub_opcode == 0x04:
        type_idx = read_operand("u32")
        field_idx = read_operand("u32")
        _compile_struct_get(ctx, block, type_idx, field_idx, signed=False)
        return True

    # struct.set (0xFB 0x05)
    if sub_opcode == 0x05:
        type_idx = read_operand("u32")
        field_idx = read_operand("u32")

        value = ctx.stack.pop()
        struct_ref = ctx.stack.pop()

        # Calculate field offset and store
        offset = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(offset.name),
                result_type=L,
                op="add",
                left=Temporary(struct_ref.name),
                right=IntConst(field_idx * 8),
            )
        )
        block.instructions.append(
            Store(
                store_type=L,
                address=Temporary(offset.name),
                value=Temporary(value.name),
            )
        )
        return True

    # array.new (0xFB 0x06)
    if sub_opcode == 0x06:
        type_idx = read_operand("u32")

        length = ctx.stack.pop()
        init_value = ctx.stack.pop()

        result = ctx.stack.new_temp(ValueType.ARRAYREF)
        block.instructions.append(
            Call(
                target=Global("__wasm_array_new"),
                args=[
                    (W, IntConst(type_idx)),
                    (W, Temporary(length.name)),
                    (L, Temporary(init_value.name)),
                ],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # array.new_default (0xFB 0x07)
    if sub_opcode == 0x07:
        type_idx = read_operand("u32")

        length = ctx.stack.pop()

        result = ctx.stack.new_temp(ValueType.ARRAYREF)
        block.instructions.append(
            Call(
                target=Global("__wasm_array_new_default"),
                args=[(W, IntConst(type_idx)), (W, Temporary(length.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # array.new_fixed (0xFB 0x08)
    if sub_opcode == 0x08:
        type_idx = read_operand("u32")
        length = read_operand("u32")

        # Pop 'length' values from stack
        values = [ctx.stack.pop() for _ in range(length)]
        values.reverse()

        result = ctx.stack.new_temp(ValueType.ARRAYREF)
        block.instructions.append(
            Call(
                target=Global("__wasm_array_new_default"),
                args=[(W, IntConst(type_idx)), (W, IntConst(length))],
                result=Temporary(result.name),
                result_type=L,
            )
        )

        # Store each value
        for i, val in enumerate(values):
            offset = ctx.stack.new_temp_no_push(ValueType.I64)
            block.instructions.append(
                BinaryOp(
                    result=Temporary(offset.name),
                    result_type=L,
                    op="add",
                    left=Temporary(result.name),
                    right=IntConst(8 + i * 8),  # 8 byte header + element offset
                )
            )
            block.instructions.append(
                Store(
                    store_type=L,
                    address=Temporary(offset.name),
                    value=Temporary(val.name),
                )
            )
        return True

    # array.get (0xFB 0x0B)
    if sub_opcode == 0x0B:
        type_idx = read_operand("u32")
        _compile_array_get(ctx, block, type_idx)
        return True

    # array.get_s (0xFB 0x0C)
    if sub_opcode == 0x0C:
        type_idx = read_operand("u32")
        _compile_array_get(ctx, block, type_idx, signed=True)
        return True

    # array.get_u (0xFB 0x0D)
    if sub_opcode == 0x0D:
        type_idx = read_operand("u32")
        _compile_array_get(ctx, block, type_idx, signed=False)
        return True

    # array.set (0xFB 0x0E)
    if sub_opcode == 0x0E:
        type_idx = read_operand("u32")

        value = ctx.stack.pop()
        index = ctx.stack.pop()
        array_ref = ctx.stack.pop()

        # Calculate element offset: array_ref + 8 + index * 8
        idx64 = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            Copy(
                result=Temporary(idx64.name),
                result_type=L,
                value=Temporary(index.name),
            )
        )

        offset_mul = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(offset_mul.name),
                result_type=L,
                op="mul",
                left=Temporary(idx64.name),
                right=IntConst(8),
            )
        )

        offset = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(offset.name),
                result_type=L,
                op="add",
                left=Temporary(array_ref.name),
                right=Temporary(offset_mul.name),
            )
        )

        final_addr = ctx.stack.new_temp_no_push(ValueType.I64)
        block.instructions.append(
            BinaryOp(
                result=Temporary(final_addr.name),
                result_type=L,
                op="add",
                left=Temporary(offset.name),
                right=IntConst(8),  # Skip header
            )
        )

        block.instructions.append(
            Store(
                store_type=L,
                address=Temporary(final_addr.name),
                value=Temporary(value.name),
            )
        )
        return True

    # array.len (0xFB 0x0F)
    if sub_opcode == 0x0F:
        array_ref = ctx.stack.pop()

        # Length is stored at offset 0 of array
        result = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            Load(
                result=Temporary(result.name),
                result_type=W,
                address=Temporary(array_ref.name),
            )
        )
        return True

    # ref.i31 (0xFB 0x1C)
    if sub_opcode == 0x1C:
        value = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I31REF)
        # i31ref encodes the value in the lower 31 bits with a tag bit
        # For now, just copy (runtime handles tagging)
        block.instructions.append(
            Call(
                target=Global("__wasm_ref_i31"),
                args=[(W, Temporary(value.name))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # i31.get_s (0xFB 0x1D)
    if sub_opcode == 0x1D:
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i31_get_s"),
                args=[(L, Temporary(ref.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # i31.get_u (0xFB 0x1E)
    if sub_opcode == 0x1E:
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_i31_get_u"),
                args=[(L, Temporary(ref.name))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # ref.test (0xFB 0x14)
    if sub_opcode == 0x14:
        type_idx = read_operand("u32")
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_ref_test"),
                args=[(L, Temporary(ref.name)), (W, IntConst(type_idx))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # ref.test null (0xFB 0x15)
    if sub_opcode == 0x15:
        type_idx = read_operand("u32")
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.I32)
        block.instructions.append(
            Call(
                target=Global("__wasm_ref_test_null"),
                args=[(L, Temporary(ref.name)), (W, IntConst(type_idx))],
                result=Temporary(result.name),
                result_type=W,
            )
        )
        return True

    # ref.cast (0xFB 0x16)
    if sub_opcode == 0x16:
        type_idx = read_operand("u32")
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.STRUCTREF)  # Could be any ref type
        block.instructions.append(
            Call(
                target=Global("__wasm_ref_cast"),
                args=[(L, Temporary(ref.name)), (W, IntConst(type_idx))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    # ref.cast null (0xFB 0x17)
    if sub_opcode == 0x17:
        type_idx = read_operand("u32")
        ref = ctx.stack.pop()
        result = ctx.stack.new_temp(ValueType.STRUCTREF)
        block.instructions.append(
            Call(
                target=Global("__wasm_ref_cast_null"),
                args=[(L, Temporary(ref.name)), (W, IntConst(type_idx))],
                result=Temporary(result.name),
                result_type=L,
            )
        )
        return True

    return False


def _compile_struct_get(
    ctx: FunctionContext,
    block: Block,
    type_idx: int,
    field_idx: int,
    signed: bool = False,
) -> None:
    """Compile struct.get with optional sign/zero extension."""
    struct_type = ctx.module.get_struct_type(type_idx)
    field_type = struct_type.fields[field_idx]

    struct_ref = ctx.stack.pop()

    # Calculate field offset and load
    offset = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(offset.name),
            result_type=L,
            op="add",
            left=Temporary(struct_ref.name),
            right=IntConst(field_idx * 8),
        )
    )

    result_vtype = _storage_type_to_value_type(field_type.storage_type)
    result = ctx.stack.new_temp(result_vtype)
    block.instructions.append(
        Load(
            result=Temporary(result.name),
            result_type=L,
            address=Temporary(offset.name),
        )
    )


def _compile_array_get(
    ctx: FunctionContext,
    block: Block,
    type_idx: int,
    signed: bool = False,
) -> None:
    """Compile array.get with optional sign/zero extension."""
    index = ctx.stack.pop()
    array_ref = ctx.stack.pop()

    # Calculate element offset: array_ref + 8 + index * 8
    idx64 = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        Copy(
            result=Temporary(idx64.name),
            result_type=L,
            value=Temporary(index.name),
        )
    )

    offset_mul = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(offset_mul.name),
            result_type=L,
            op="mul",
            left=Temporary(idx64.name),
            right=IntConst(8),
        )
    )

    offset = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(offset.name),
            result_type=L,
            op="add",
            left=Temporary(array_ref.name),
            right=Temporary(offset_mul.name),
        )
    )

    final_addr = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(final_addr.name),
            result_type=L,
            op="add",
            left=Temporary(offset.name),
            right=IntConst(8),  # Skip header
        )
    )

    array_type = ctx.module.get_array_type(type_idx)
    result_vtype = _storage_type_to_value_type(array_type.element_type.storage_type)
    result = ctx.stack.new_temp(result_vtype)
    block.instructions.append(
        Load(
            result=Temporary(result.name),
            result_type=L,
            address=Temporary(final_addr.name),
        )
    )


def _storage_type_to_value_type(storage_type: ValueType | int) -> ValueType:
    """Convert storage type to value type for stack operations."""
    if isinstance(storage_type, int):
        # Type index - treat as reference type
        return ValueType.EQREF
    if storage_type in (ValueType.I8, ValueType.I16):
        return ValueType.I32
    return storage_type
