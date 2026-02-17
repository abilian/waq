"""Module-level validation."""

from __future__ import annotations

from waq.parser.binary import BinaryReader
from waq.parser.module import ExportKind, ImportKind, WasmModule
from waq.parser.types import FuncType, ValueType

from .types import ValidationContext, ValidationResult


def validate_module(module: WasmModule) -> ValidationResult:
    """Validate a WASM module.

    Performs structural validation, type checking, and index validation.

    Args:
        module: The parsed WASM module to validate

    Returns:
        ValidationResult with any errors or warnings found
    """
    ctx = ValidationContext(module=module)

    # Validate imports
    _validate_imports(ctx)

    # Validate exports
    _validate_exports(ctx)

    # Validate functions
    _validate_functions(ctx)

    # Validate globals
    _validate_globals(ctx)

    # Validate tables
    _validate_tables(ctx)

    # Validate memories
    _validate_memories(ctx)

    # Validate start function
    _validate_start(ctx)

    return ctx.result


def _validate_imports(ctx: ValidationContext) -> None:
    """Validate import section."""
    for i, imp in enumerate(ctx.module.imports):
        if imp.kind == ImportKind.FUNC:
            type_idx = imp.desc
            if not isinstance(type_idx, int):
                ctx.result.add_error(
                    f"import {i}: function import has non-integer type index",
                    location=f"import {i}",
                )
                continue
            if type_idx >= len(ctx.module.types):
                ctx.result.add_error(
                    f"import {i}: type index {type_idx} out of bounds",
                    location=f"import {i}",
                )


def _validate_exports(ctx: ValidationContext) -> None:
    """Validate export section."""
    num_funcs = ctx.module.num_imported_funcs() + len(ctx.module.func_types)
    num_tables = ctx.module.num_imported_tables() + len(ctx.module.tables)
    num_memories = ctx.module.num_imported_memories() + len(ctx.module.memories)
    num_globals = ctx.module.num_imported_globals() + len(ctx.module.globals)

    seen_names: set[str] = set()

    for exp in ctx.module.exports:
        # Check for duplicate export names
        if exp.name in seen_names:
            ctx.result.add_error(
                f"duplicate export name: '{exp.name}'",
                location=f"export '{exp.name}'",
            )
        seen_names.add(exp.name)

        # Check index bounds
        if exp.kind == ExportKind.FUNC and exp.index >= num_funcs:
            ctx.result.add_error(
                f"export '{exp.name}': function index {exp.index} out of bounds",
                location=f"export '{exp.name}'",
            )
        elif exp.kind == ExportKind.TABLE and exp.index >= num_tables:
            ctx.result.add_error(
                f"export '{exp.name}': table index {exp.index} out of bounds",
                location=f"export '{exp.name}'",
            )
        elif exp.kind == ExportKind.MEMORY and exp.index >= num_memories:
            ctx.result.add_error(
                f"export '{exp.name}': memory index {exp.index} out of bounds",
                location=f"export '{exp.name}'",
            )
        elif exp.kind == ExportKind.GLOBAL and exp.index >= num_globals:
            ctx.result.add_error(
                f"export '{exp.name}': global index {exp.index} out of bounds",
                location=f"export '{exp.name}'",
            )


def _validate_functions(ctx: ValidationContext) -> None:
    """Validate function section and code section."""
    # Check type indices in function section
    for i, type_idx in enumerate(ctx.module.func_types):
        if type_idx >= len(ctx.module.types):
            ctx.result.add_error(
                f"function {i}: type index {type_idx} out of bounds",
                location=f"function {i}",
            )
            continue

        type_def = ctx.module.types[type_idx]
        if not isinstance(type_def, FuncType):
            ctx.result.add_error(
                f"function {i}: type index {type_idx} is not a function type",
                location=f"function {i}",
            )

    # Check code section matches function section
    if len(ctx.module.code) != len(ctx.module.func_types):
        ctx.result.add_error(
            f"code section has {len(ctx.module.code)} entries but function section has {len(ctx.module.func_types)}",
            location="code section",
        )
        return

    # Validate each function body
    num_imports = ctx.module.num_imported_funcs()
    for i, (type_idx, body) in enumerate(
        zip(ctx.module.func_types, ctx.module.code, strict=True)
    ):
        func_idx = num_imports + i
        if type_idx >= len(ctx.module.types):
            continue  # Already reported

        type_def = ctx.module.types[type_idx]
        if not isinstance(type_def, FuncType):
            continue  # Already reported

        local_types = body.all_locals()
        ctx.reset_for_function(func_idx, type_def, local_types)

        # Validate function body instructions
        _validate_function_body(ctx, body.code)


def _validate_function_body(ctx: ValidationContext, code: bytes) -> None:
    """Validate a function body's instructions."""
    reader = BinaryReader(code)

    while not reader.at_end:
        ctx.current_offset = reader.pos
        _validate_instruction(ctx, reader)

    # Check final stack state
    if ctx.current_func_type:
        expected_results = len(ctx.current_func_type.results)
        actual_depth = len(ctx.value_stack)

        # Account for the implicit function block
        if ctx.control_stack:
            frame = ctx.control_stack[0]
            expected_depth = frame.start_depth + expected_results
            if actual_depth != expected_depth and not frame.unreachable:
                ctx.error(
                    f"function ends with wrong stack depth: expected {expected_results} values, got {actual_depth - frame.start_depth}"
                )


def _validate_instruction(ctx: ValidationContext, reader: BinaryReader) -> None:
    """Validate a single instruction."""
    opcode = reader.read_byte()

    # nop
    if opcode == 0x01:
        return

    # unreachable
    if opcode == 0x00:
        if ctx.control_stack:
            ctx.control_stack[-1].unreachable = True
        return

    # block
    if opcode == 0x02:
        block_type = reader.read_block_type()
        result_types = _block_type_to_results(block_type, ctx)
        ctx.push_control("block", result_types)
        return

    # loop
    if opcode == 0x03:
        block_type = reader.read_block_type()
        result_types = _block_type_to_results(block_type, ctx)
        ctx.push_control("loop", result_types)
        return

    # if
    if opcode == 0x04:
        block_type = reader.read_block_type()
        result_types = _block_type_to_results(block_type, ctx)
        ctx.pop_expect(ValueType.I32)  # condition
        ctx.push_control("if", result_types)
        return

    # else
    if opcode == 0x05:
        if not ctx.control_stack or ctx.control_stack[-1].kind != "if":
            ctx.error("else without matching if")
            return
        # Pop values for then branch, will be regenerated for else
        frame = ctx.control_stack[-1]
        ctx.value_stack = ctx.value_stack[: frame.start_depth]
        return

    # end
    if opcode == 0x0B:
        ctx.pop_control()
        return

    # br
    if opcode == 0x0C:
        depth = reader.read_u32_leb128()
        if depth >= len(ctx.control_stack):
            ctx.error(f"branch depth {depth} exceeds control stack")
        if ctx.control_stack:
            ctx.control_stack[-1].unreachable = True
        return

    # br_if
    if opcode == 0x0D:
        _depth = reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)  # condition
        return

    # br_table
    if opcode == 0x0E:
        count = reader.read_u32_leb128()
        for _ in range(count + 1):  # +1 for default
            reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)  # index
        if ctx.control_stack:
            ctx.control_stack[-1].unreachable = True
        return

    # return
    if opcode == 0x0F:
        if ctx.current_func_type:
            for rtype in reversed(ctx.current_func_type.results):
                ctx.pop_expect(rtype)
        if ctx.control_stack:
            ctx.control_stack[-1].unreachable = True
        return

    # call
    if opcode == 0x10:
        func_idx = reader.read_u32_leb128()
        func_type = ctx.get_func_type(func_idx)
        if func_type:
            # Pop arguments
            for ptype in reversed(func_type.params):
                ctx.pop_expect(ptype)
            # Push results
            for rtype in func_type.results:
                ctx.push_value(rtype)
        return

    # call_indirect
    if opcode == 0x11:
        type_idx = reader.read_u32_leb128()
        _table_idx = reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)  # table index

        if type_idx < len(ctx.module.types):
            type_def = ctx.module.types[type_idx]
            if isinstance(type_def, FuncType):
                for ptype in reversed(type_def.params):
                    ctx.pop_expect(ptype)
                for rtype in type_def.results:
                    ctx.push_value(rtype)
        else:
            ctx.error(f"call_indirect: type index {type_idx} out of bounds")
        return

    # drop
    if opcode == 0x1A:
        ctx.pop_value()
        return

    # select
    if opcode == 0x1B:
        ctx.pop_expect(ValueType.I32)  # condition
        val2 = ctx.pop_value()
        val1 = ctx.pop_value()
        if val1 and val2 and val1 != val2:
            ctx.error(f"select type mismatch: {val1} vs {val2}")
        if val1:
            ctx.push_value(val1)
        return

    # local.get
    if opcode == 0x20:
        local_idx = reader.read_u32_leb128()
        local_type = ctx.get_local_type(local_idx)
        if local_type:
            ctx.push_value(local_type)
        return

    # local.set
    if opcode == 0x21:
        local_idx = reader.read_u32_leb128()
        local_type = ctx.get_local_type(local_idx)
        if local_type:
            ctx.pop_expect(local_type)
        return

    # local.tee
    if opcode == 0x22:
        local_idx = reader.read_u32_leb128()
        local_type = ctx.get_local_type(local_idx)
        if local_type:
            ctx.pop_expect(local_type)
            ctx.push_value(local_type)
        return

    # global.get
    if opcode == 0x23:
        global_idx = reader.read_u32_leb128()
        num_globals = ctx.module.num_imported_globals() + len(ctx.module.globals)
        if global_idx >= num_globals:
            ctx.error(f"global index {global_idx} out of bounds")
        else:
            # Get global type
            num_imports = ctx.module.num_imported_globals()
            if global_idx < num_imports:
                for imp in ctx.module.imports:
                    if imp.kind == ImportKind.GLOBAL:
                        if global_idx == 0:
                            ctx.push_value(imp.desc.value_type)
                            return
                        global_idx -= 1
            else:
                local_idx = global_idx - num_imports
                ctx.push_value(ctx.module.globals[local_idx].type.value_type)
        return

    # global.set
    if opcode == 0x24:
        global_idx = reader.read_u32_leb128()
        num_globals = ctx.module.num_imported_globals() + len(ctx.module.globals)
        if global_idx >= num_globals:
            ctx.error(f"global index {global_idx} out of bounds")
        else:
            # Get global type and check mutability
            num_imports = ctx.module.num_imported_globals()
            if global_idx < num_imports:
                for imp in ctx.module.imports:
                    if imp.kind == ImportKind.GLOBAL:
                        if global_idx == 0:
                            if not imp.desc.mutable:
                                ctx.error(f"cannot set immutable global {global_idx}")
                            ctx.pop_expect(imp.desc.value_type)
                            return
                        global_idx -= 1
            else:
                local_idx = global_idx - num_imports
                glob = ctx.module.globals[local_idx]
                if not glob.type.mutable:
                    ctx.error(f"cannot set immutable global {global_idx}")
                ctx.pop_expect(glob.type.value_type)
        return

    # Memory load/store instructions (0x28-0x3E)
    if 0x28 <= opcode <= 0x3E:
        _align = reader.read_u32_leb128()
        _offset = reader.read_u32_leb128()
        _validate_memory_instruction(ctx, opcode)
        return

    # memory.size
    if opcode == 0x3F:
        _mem_idx = reader.read_u32_leb128()
        ctx.push_value(ValueType.I32)
        return

    # memory.grow
    if opcode == 0x40:
        _mem_idx = reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.I32)
        return

    # i32.const
    if opcode == 0x41:
        reader.read_s32_leb128()
        ctx.push_value(ValueType.I32)
        return

    # i64.const
    if opcode == 0x42:
        reader.read_s64_leb128()
        ctx.push_value(ValueType.I64)
        return

    # f32.const
    if opcode == 0x43:
        reader.read_f32()
        ctx.push_value(ValueType.F32)
        return

    # f64.const
    if opcode == 0x44:
        reader.read_f64()
        ctx.push_value(ValueType.F64)
        return

    # Numeric instructions - simplified validation
    # i32 unary (0x45-0x4F, etc.)
    if opcode in (0x45, 0x50, 0x67, 0x68, 0x69):  # eqz, clz, ctz, popcnt
        if opcode == 0x50:  # i64.eqz returns i32
            ctx.pop_expect(ValueType.I64)
            ctx.push_value(ValueType.I32)
        elif opcode == 0x45:  # i32.eqz
            ctx.pop_expect(ValueType.I32)
            ctx.push_value(ValueType.I32)
        else:
            ctx.pop_expect(ValueType.I32)
            ctx.push_value(ValueType.I32)
        return

    # i32 binary (0x46-0x4E, 0x6A-0x78)
    if 0x46 <= opcode <= 0x4E or 0x6A <= opcode <= 0x78:
        ctx.pop_expect(ValueType.I32)
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.I32)
        return

    # i64 comparison (0x51-0x5A)
    if 0x51 <= opcode <= 0x5A:
        ctx.pop_expect(ValueType.I64)
        ctx.pop_expect(ValueType.I64)
        ctx.push_value(ValueType.I32)  # comparisons return i32
        return

    # i64 binary (0x7C-0x8A)
    if 0x7C <= opcode <= 0x8A:
        ctx.pop_expect(ValueType.I64)
        ctx.pop_expect(ValueType.I64)
        ctx.push_value(ValueType.I64)
        return

    # f32 comparison (0x5B-0x60)
    if 0x5B <= opcode <= 0x60:
        ctx.pop_expect(ValueType.F32)
        ctx.pop_expect(ValueType.F32)
        ctx.push_value(ValueType.I32)
        return

    # f64 comparison (0x61-0x66)
    if 0x61 <= opcode <= 0x66:
        ctx.pop_expect(ValueType.F64)
        ctx.pop_expect(ValueType.F64)
        ctx.push_value(ValueType.I32)
        return

    # f32 unary (0x8B-0x91)
    if 0x8B <= opcode <= 0x91:
        ctx.pop_expect(ValueType.F32)
        ctx.push_value(ValueType.F32)
        return

    # f32 binary (0x92-0x98)
    if 0x92 <= opcode <= 0x98:
        ctx.pop_expect(ValueType.F32)
        ctx.pop_expect(ValueType.F32)
        ctx.push_value(ValueType.F32)
        return

    # f64 unary (0x99-0x9F)
    if 0x99 <= opcode <= 0x9F:
        ctx.pop_expect(ValueType.F64)
        ctx.push_value(ValueType.F64)
        return

    # f64 binary (0xA0-0xA6)
    if 0xA0 <= opcode <= 0xA6:
        ctx.pop_expect(ValueType.F64)
        ctx.pop_expect(ValueType.F64)
        ctx.push_value(ValueType.F64)
        return

    # Conversion instructions (0xA7-0xBF)
    if 0xA7 <= opcode <= 0xBF:
        _validate_conversion_instruction(ctx, opcode)
        return

    # Extended instructions (0xFC prefix)
    if opcode == 0xFC:
        sub_opcode = reader.read_u32_leb128()
        _validate_fc_instruction(ctx, sub_opcode, reader)
        return

    # For other opcodes, just skip operands and issue a warning
    ctx.warning(f"unvalidated opcode 0x{opcode:02x}")


def _validate_memory_instruction(ctx: ValidationContext, opcode: int) -> None:
    """Validate a memory load/store instruction's stack effect."""
    # Loads
    if opcode in (0x28, 0x2C, 0x2D, 0x2E, 0x2F):  # i32.load, i32.load8_s/u, i32.load16_s/u
        ctx.pop_expect(ValueType.I32)  # address
        ctx.push_value(ValueType.I32)
    elif opcode in (0x29, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35):  # i64.load variants
        ctx.pop_expect(ValueType.I32)  # address
        ctx.push_value(ValueType.I64)
    elif opcode == 0x2A:  # f32.load
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.F32)
    elif opcode == 0x2B:  # f64.load
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.F64)
    # Stores
    elif opcode in (0x36, 0x3A, 0x3B):  # i32.store, i32.store8, i32.store16
        ctx.pop_expect(ValueType.I32)  # value
        ctx.pop_expect(ValueType.I32)  # address
    elif opcode in (0x37, 0x3C, 0x3D, 0x3E):  # i64.store variants
        ctx.pop_expect(ValueType.I64)  # value
        ctx.pop_expect(ValueType.I32)  # address
    elif opcode == 0x38:  # f32.store
        ctx.pop_expect(ValueType.F32)
        ctx.pop_expect(ValueType.I32)
    elif opcode == 0x39:  # f64.store
        ctx.pop_expect(ValueType.F64)
        ctx.pop_expect(ValueType.I32)


def _validate_conversion_instruction(ctx: ValidationContext, opcode: int) -> None:
    """Validate a conversion instruction's stack effect."""
    # i32 wrap/extend
    if opcode == 0xA7:  # i32.wrap_i64
        ctx.pop_expect(ValueType.I64)
        ctx.push_value(ValueType.I32)
    elif opcode in (0xA8, 0xA9, 0xAA, 0xAB):  # i32.trunc_f32/f64 variants
        ctx.pop_expect(ValueType.F32 if opcode in (0xA8, 0xA9) else ValueType.F64)
        ctx.push_value(ValueType.I32)
    # i64 extend/trunc
    elif opcode in (0xAC, 0xAD):  # i64.extend_i32_s/u
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.I64)
    elif opcode in (0xAE, 0xAF, 0xB0, 0xB1):  # i64.trunc_f32/f64 variants
        ctx.pop_expect(ValueType.F32 if opcode in (0xAE, 0xAF) else ValueType.F64)
        ctx.push_value(ValueType.I64)
    # f32 convert/demote
    elif opcode in (0xB2, 0xB3):  # f32.convert_i32_s/u
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.F32)
    elif opcode in (0xB4, 0xB5):  # f32.convert_i64_s/u
        ctx.pop_expect(ValueType.I64)
        ctx.push_value(ValueType.F32)
    elif opcode == 0xB6:  # f32.demote_f64
        ctx.pop_expect(ValueType.F64)
        ctx.push_value(ValueType.F32)
    # f64 convert/promote
    elif opcode in (0xB7, 0xB8):  # f64.convert_i32_s/u
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.F64)
    elif opcode in (0xB9, 0xBA):  # f64.convert_i64_s/u
        ctx.pop_expect(ValueType.I64)
        ctx.push_value(ValueType.F64)
    elif opcode == 0xBB:  # f64.promote_f32
        ctx.pop_expect(ValueType.F32)
        ctx.push_value(ValueType.F64)
    # Reinterpret
    elif opcode == 0xBC:  # i32.reinterpret_f32
        ctx.pop_expect(ValueType.F32)
        ctx.push_value(ValueType.I32)
    elif opcode == 0xBD:  # i64.reinterpret_f64
        ctx.pop_expect(ValueType.F64)
        ctx.push_value(ValueType.I64)
    elif opcode == 0xBE:  # f32.reinterpret_i32
        ctx.pop_expect(ValueType.I32)
        ctx.push_value(ValueType.F32)
    elif opcode == 0xBF:  # f64.reinterpret_i64
        ctx.pop_expect(ValueType.I64)
        ctx.push_value(ValueType.F64)


def _validate_fc_instruction(
    ctx: ValidationContext, sub_opcode: int, reader: BinaryReader
) -> None:
    """Validate a 0xFC-prefixed instruction."""
    # Saturating conversions (0x00-0x07)
    if sub_opcode <= 0x07:
        if sub_opcode in (0x00, 0x01):  # i32.trunc_sat_f32
            ctx.pop_expect(ValueType.F32)
            ctx.push_value(ValueType.I32)
        elif sub_opcode in (0x02, 0x03):  # i32.trunc_sat_f64
            ctx.pop_expect(ValueType.F64)
            ctx.push_value(ValueType.I32)
        elif sub_opcode in (0x04, 0x05):  # i64.trunc_sat_f32
            ctx.pop_expect(ValueType.F32)
            ctx.push_value(ValueType.I64)
        elif sub_opcode in (0x06, 0x07):  # i64.trunc_sat_f64
            ctx.pop_expect(ValueType.F64)
            ctx.push_value(ValueType.I64)
        return

    # memory.init
    if sub_opcode == 0x08:
        _data_idx = reader.read_u32_leb128()
        _mem_idx = reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)  # n
        ctx.pop_expect(ValueType.I32)  # s
        ctx.pop_expect(ValueType.I32)  # d
        return

    # data.drop
    if sub_opcode == 0x09:
        _data_idx = reader.read_u32_leb128()
        return

    # memory.copy
    if sub_opcode == 0x0A:
        _dst_mem = reader.read_u32_leb128()
        _src_mem = reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)  # n
        ctx.pop_expect(ValueType.I32)  # s
        ctx.pop_expect(ValueType.I32)  # d
        return

    # memory.fill
    if sub_opcode == 0x0B:
        _mem_idx = reader.read_u32_leb128()
        ctx.pop_expect(ValueType.I32)  # n
        ctx.pop_expect(ValueType.I32)  # val
        ctx.pop_expect(ValueType.I32)  # d
        return

    # table operations (0x0C-0x11)
    # Skip for now
    ctx.warning(f"unvalidated 0xFC sub-opcode 0x{sub_opcode:02x}")


def _validate_globals(ctx: ValidationContext) -> None:
    """Validate global section."""
    for i, glob in enumerate(ctx.module.globals):
        # Validate init expression type matches global type
        # (simplified - just check it's not empty)
        if not glob.init_expr:
            ctx.result.add_error(
                f"global {i} has empty init expression",
                location=f"global {i}",
            )


def _validate_tables(ctx: ValidationContext) -> None:
    """Validate table section."""
    for i, table in enumerate(ctx.module.tables):
        if table.limits.max is not None and table.limits.min > table.limits.max:
            ctx.result.add_error(
                f"table {i}: min {table.limits.min} > max {table.limits.max}",
                location=f"table {i}",
            )


def _validate_memories(ctx: ValidationContext) -> None:
    """Validate memory section."""
    if len(ctx.module.memories) > 1:
        ctx.result.add_warning(
            "multiple memories are a WASM 2.0 feature",
            location="memory section",
        )

    for i, mem in enumerate(ctx.module.memories):
        if mem.limits.max is not None and mem.limits.min > mem.limits.max:
            ctx.result.add_error(
                f"memory {i}: min {mem.limits.min} > max {mem.limits.max}",
                location=f"memory {i}",
            )

        # WASM spec limit
        max_pages = 65536
        if mem.limits.min > max_pages:
            ctx.result.add_error(
                f"memory {i}: min pages {mem.limits.min} exceeds maximum {max_pages}",
                location=f"memory {i}",
            )


def _validate_start(ctx: ValidationContext) -> None:
    """Validate start section."""
    if ctx.module.start is None:
        return

    num_funcs = ctx.module.num_imported_funcs() + len(ctx.module.func_types)
    if ctx.module.start >= num_funcs:
        ctx.result.add_error(
            f"start function index {ctx.module.start} out of bounds",
            location="start section",
        )
        return

    # Start function must have no params and no results
    func_type = ctx.module.get_func_type(ctx.module.start)
    if func_type.params:
        ctx.result.add_error(
            f"start function has {len(func_type.params)} parameters (must have 0)",
            location="start section",
        )
    if func_type.results:
        ctx.result.add_error(
            f"start function has {len(func_type.results)} results (must have 0)",
            location="start section",
        )


def _block_type_to_results(
    block_type, ctx: ValidationContext
) -> tuple[ValueType, ...]:
    """Convert block type to result types."""
    if block_type is None:
        return ()
    if isinstance(block_type, ValueType):
        return (block_type,)
    if isinstance(block_type, int):
        # Type index
        if block_type >= len(ctx.module.types):
            ctx.error(f"block type index {block_type} out of bounds")
            return ()
        type_def = ctx.module.types[block_type]
        if isinstance(type_def, FuncType):
            return type_def.results
        ctx.error(f"block type index {block_type} is not a function type")
        return ()
    return ()
