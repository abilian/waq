"""Variable instruction compilation (local.get, local.set, local.tee, global.get, global.set)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    D,
    Global as QbeGlobal,
    L,
    Load,
    S,
    Store,
    Temporary,
    W,
)

from waq.parser.types import GlobalType, ValueType

if TYPE_CHECKING:
    from collections.abc import Callable

    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext, ModuleContext


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
    if vtype.is_reference():
        return L  # All reference types are pointers (64-bit)
    raise ValueError(f"unknown value type: {vtype}")


def _vtype_to_load_type(vtype: ValueType) -> str:
    """Convert WASM ValueType to QBE load type suffix."""
    if vtype == ValueType.I32:
        return "loadw"
    if vtype == ValueType.I64:
        return "loadl"
    if vtype == ValueType.F32:
        return "loads"
    if vtype == ValueType.F64:
        return "loadd"
    if vtype.is_reference():
        return "loadl"  # All reference types are 64-bit pointers
    raise ValueError(f"unknown value type: {vtype}")


def _vtype_to_store_type(vtype: ValueType) -> str:
    """Convert WASM ValueType to QBE store type suffix."""
    if vtype == ValueType.I32:
        return "storew"
    if vtype == ValueType.I64:
        return "storel"
    if vtype == ValueType.F32:
        return "stores"
    if vtype == ValueType.F64:
        return "stored"
    if vtype.is_reference():
        return "storel"  # All reference types are 64-bit pointers
    raise ValueError(f"unknown value type: {vtype}")


def compile_variable_instruction(
    opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,
    block: Block,
    read_operand: Callable[[str], Any],
) -> bool:
    """Compile a variable instruction.

    Returns True if the instruction was handled.
    """
    # local.get - load from stack slot
    if opcode == 0x20:
        idx = read_operand("u32")
        vtype = ctx.get_local_type(idx)
        addr_name = ctx.get_local_addr(idx)
        temp = ctx.stack.new_temp(vtype)
        qbe_type = _vtype_to_ir_type(vtype)
        load_type = _vtype_to_load_type(vtype)
        block.instructions.append(
            Load(
                result=Temporary(temp.name),
                result_type=qbe_type,
                address=Temporary(addr_name),
                load_type=load_type,
            )
        )
        return True

    # local.set - store to stack slot
    if opcode == 0x21:
        idx = read_operand("u32")
        value = ctx.stack.pop()
        vtype = ctx.get_local_type(idx)
        addr_name = ctx.get_local_addr(idx)
        store_type = _vtype_to_store_type(vtype)
        block.instructions.append(
            Store(
                store_type=store_type,
                value=Temporary(value.name),
                address=Temporary(addr_name),
            )
        )
        return True

    # local.tee - store to stack slot but keep value on stack
    if opcode == 0x22:
        idx = read_operand("u32")
        value = ctx.stack.peek()  # Don't pop, just peek
        vtype = ctx.get_local_type(idx)
        addr_name = ctx.get_local_addr(idx)
        store_type = _vtype_to_store_type(vtype)
        block.instructions.append(
            Store(
                store_type=store_type,
                value=Temporary(value.name),
                address=Temporary(addr_name),
            )
        )
        return True

    # global.get
    if opcode == 0x23:
        idx = read_operand("u32")
        global_def = _get_global_def(mod_ctx, idx)
        vtype = global_def.type.value_type
        global_name = mod_ctx.get_global_name(idx)
        temp = ctx.stack.new_temp(vtype)
        qbe_type = _vtype_to_ir_type(vtype)
        load_type = _vtype_to_load_type(vtype)
        # Load from global data
        block.instructions.append(
            Load(
                result=Temporary(temp.name),
                result_type=qbe_type,
                address=QbeGlobal(global_name),
                load_type=load_type,
            )
        )
        return True

    # global.set
    if opcode == 0x24:
        idx = read_operand("u32")
        value = ctx.stack.pop()
        global_def = _get_global_def(mod_ctx, idx)
        vtype = global_def.type.value_type
        global_name = mod_ctx.get_global_name(idx)
        store_type = _vtype_to_store_type(vtype)
        # Store to global data
        block.instructions.append(
            Store(
                store_type=store_type,
                value=Temporary(value.name),
                address=QbeGlobal(global_name),
            )
        )
        return True

    return False


def _get_global_def(mod_ctx: ModuleContext, idx: int):
    """Get global definition by index, handling imports."""
    num_imports = mod_ctx.module.num_imported_globals()
    if idx < num_imports:
        # Imported global - find it
        import_idx = 0
        for imp in mod_ctx.module.imports:
            if imp.kind.value == 3:  # GLOBAL
                if import_idx == idx:
                    # Return a pseudo-global with the type
                    from waq.parser.module import Global  # noqa: PLC0415

                    assert isinstance(imp.desc, GlobalType)
                    return Global(imp.desc, b"")
                import_idx += 1
        raise ValueError(f"global import {idx} not found")
    # Defined global
    local_idx = idx - num_imports
    return mod_ctx.module.globals[local_idx]
