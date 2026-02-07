"""Main code generation: WASM module to QBE module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbepy import Function, Module
from qbepy.ir import (
    Alloc,
    BinaryOp,
    Branch,
    Call,
    D,
    DataDef,
    Global,
    Halt,
    IntConst,
    Jump,
    L,
    Label,
    Phi,
    Return,
    S,
    Store,
    Temporary,
    W,
)

from waq.errors import CompileError
from waq.parser.binary import BinaryReader
from waq.parser.module import ExportKind, WasmModule
from waq.parser.types import ValueType

from .context import FunctionContext, ModuleContext
from .instructions.control import compile_control_instruction
from .instructions.conversion import (
    compile_conversion_instruction,
    compile_saturating_conversion,
)
from .instructions.exceptions import compile_exception_instruction
from .instructions.gc import compile_gc_instruction
from .instructions.memory import (
    compile_bulk_memory_instruction,
    compile_memory_instruction,
)
from .instructions.numeric import compile_numeric_instruction
from .instructions.reference import compile_reference_instruction
from .instructions.table import (
    compile_table_bulk_instruction,
    compile_table_instruction,
)
from .instructions.variable import compile_variable_instruction
from .stack import ValueStack

if TYPE_CHECKING:
    from qbepy.ir import Block


def compile_module(wasm_module: WasmModule, target: str = "amd64_sysv") -> Module:
    """Compile a WASM module to a QBE module."""
    qbe_module = Module()

    mod_ctx = ModuleContext(module=wasm_module, qbe_module=qbe_module)

    # Compile globals
    _compile_globals(mod_ctx, qbe_module)

    # Compile functions
    num_imports = wasm_module.num_imported_funcs()
    for i, body in enumerate(wasm_module.code):
        func_idx = num_imports + i
        _compile_function(mod_ctx, qbe_module, func_idx, body)

    return qbe_module


def _compile_globals(mod_ctx: ModuleContext, qbe_module: Module) -> None:
    """Compile global variable definitions."""
    for i, glob in enumerate(mod_ctx.module.globals):
        global_name = mod_ctx.get_global_name(i + mod_ctx.module.num_imported_globals())
        vtype = glob.type.value_type

        # Evaluate init expression to get initial value
        init_value = _eval_init_expr(glob.init_expr, mod_ctx)

        # Create data definition
        data = DataDef(global_name)
        if vtype == ValueType.I32:
            data.add_words(int(init_value))
        elif vtype == ValueType.I64:
            data.add_longs(int(init_value))
        elif vtype == ValueType.F32:
            data.add_singles(float(init_value))
        elif vtype == ValueType.F64:
            data.add_doubles(float(init_value))
        qbe_module.add_data(data)


def _eval_init_expr(expr: bytes, mod_ctx: ModuleContext) -> int | float:
    """Evaluate a constant initialization expression."""
    if not expr:
        return 0

    reader = BinaryReader(expr)
    opcode = reader.read_byte()

    if opcode == 0x41:  # i32.const
        return reader.read_s32_leb128()
    if opcode == 0x42:  # i64.const
        return reader.read_s64_leb128()
    if opcode == 0x43:  # f32.const
        return reader.read_f32()
    if opcode == 0x44:  # f64.const
        return reader.read_f64()
    if opcode == 0x23:  # global.get
        _idx = reader.read_u32_leb128()
        # For imported globals, we'd need to look up the value
        # For now, return 0
        return 0

    return 0


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


def _vtype_size(vtype: ValueType) -> int:
    """Get the size in bytes for a WASM value type."""
    if vtype == ValueType.I32:
        return 4
    if vtype == ValueType.I64:
        return 8
    if vtype == ValueType.F32:
        return 4
    if vtype == ValueType.F64:
        return 8
    if vtype.is_reference():
        return 8  # All reference types are 64-bit pointers
    raise ValueError(f"unknown value type: {vtype}")


def _vtype_to_store_type(vtype: ValueType) -> str:
    """Get the QBE store type for a WASM value type."""
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


def _vtype_to_load_type(vtype: ValueType) -> str:
    """Get the QBE load type for a WASM value type."""
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


def _compile_function(
    mod_ctx: ModuleContext,
    qbe_module: Module,
    func_idx: int,
    body,
) -> None:
    """Compile a single function."""
    wasm_module = mod_ctx.module
    func_type = wasm_module.get_func_type(func_idx)
    func_name = mod_ctx.get_func_name(func_idx)

    # Determine if exported
    is_exported = any(
        exp.kind == ExportKind.FUNC and exp.index == func_idx
        for exp in wasm_module.exports
    )

    # Build parameter list (no % prefix - qbepy adds it)
    params = []
    for i, ptype in enumerate(func_type.params):
        qbe_type = _vtype_to_ir_type(ptype)
        param_name = f"p{i}"
        params.append((qbe_type, param_name))

    # Build return type
    if not func_type.results:
        ret_type = None
    elif len(func_type.results) == 1:
        ret_type = _vtype_to_ir_type(func_type.results[0])
    else:
        # Multi-value return not yet supported
        raise CompileError("multi-value return not yet supported")

    # Create QBE function
    qbe_func = Function(
        func_name, return_type=ret_type, params=params, export=is_exported
    )

    # Set up function context
    locals_list = list(func_type.params) + body.all_locals()
    func_ctx = FunctionContext(
        module=wasm_module,
        func_idx=func_idx,
        func_type=func_type,
        locals=locals_list,
        qbe_func=qbe_func,
        stack=ValueStack(),
    )

    # Create entry block
    entry_block = qbe_func.add_block("entry")

    # Allocate stack space for ALL locals (including parameters)
    # This allows locals to be mutable across loop iterations
    for i, vtype in enumerate(locals_list):
        addr_name = f"local_addr{i}"
        size = _vtype_size(vtype)
        align = 8 if size == 8 else 4
        entry_block.instructions.append(
            Alloc(result=Temporary(addr_name), size=IntConst(size), align=align)
        )
        func_ctx.set_local_addr(i, addr_name)

    # Store parameters into their stack slots
    for i, (_qbe_type, param_name) in enumerate(params):
        vtype = locals_list[i]
        addr_name = func_ctx.get_local_addr(i)
        store_type = _vtype_to_store_type(vtype)
        entry_block.instructions.append(
            Store(
                store_type=store_type,
                value=Temporary(param_name),
                address=Temporary(addr_name),
            )
        )

    # Initialize non-parameter locals to zero
    for i in range(len(func_type.params), len(locals_list)):
        vtype = locals_list[i]
        addr_name = func_ctx.get_local_addr(i)
        store_type = _vtype_to_store_type(vtype)
        entry_block.instructions.append(
            Store(
                store_type=store_type, value=IntConst(0), address=Temporary(addr_name)
            )
        )

    # Compile function body
    current_block = entry_block
    reader = BinaryReader(body.code)

    while not reader.at_end:
        new_block = _compile_instruction(
            func_ctx, mod_ctx, qbe_func, current_block, reader
        )
        if new_block is not None:
            current_block = new_block

    # Add implicit return if needed (only if block doesn't already have a terminator)
    if current_block.terminator is None:
        if not func_type.results:
            current_block.terminator = Return(value=None)
        elif func_ctx.stack.depth > 0:
            # Return top of stack
            value = func_ctx.stack.pop()
            current_block.terminator = Return(value=Temporary(value.name))
        else:
            current_block.terminator = Return(value=None)

    # Add function to module
    qbe_module.add_function(qbe_func)


def _compile_instruction(
    func_ctx: FunctionContext,
    mod_ctx: ModuleContext,
    qbe_func: Function,
    block: Block,
    reader: BinaryReader,
) -> Block | None:
    """Compile a single WASM instruction.

    Returns new current block if changed, None otherwise.
    """
    opcode = reader.read_byte()

    def read_operand(kind: str):
        """Read instruction operand."""
        if kind == "u32":
            return reader.read_u32_leb128()
        if kind == "s32":
            return reader.read_s32_leb128()
        if kind == "s64":
            return reader.read_s64_leb128()
        if kind == "f32":
            return reader.read_f32()
        if kind == "f64":
            return reader.read_f64()
        if kind == "block_type":
            return reader.read_block_type()
        raise ValueError(f"unknown operand kind: {kind}")

    # Try exception instructions first (0x06-0x09, 0x18-0x19)
    # These opcodes overlap with control flow range, so check them first
    if opcode in (0x06, 0x07, 0x08, 0x09, 0x18, 0x19):
        exc_result = compile_exception_instruction(
            opcode, func_ctx, mod_ctx, qbe_func, block, read_operand
        )
        if exc_result is not False:
            return exc_result

    # Try control flow instructions
    result = compile_control_instruction(
        opcode, func_ctx, qbe_func, block, read_operand
    )
    if result is not None or opcode in range(0x12):
        return result

    # Try variable instructions
    if compile_variable_instruction(opcode, func_ctx, mod_ctx, block, read_operand):
        return None

    # Try numeric instructions
    if compile_numeric_instruction(opcode, func_ctx, block, read_operand):
        return None

    # Try memory instructions
    if compile_memory_instruction(opcode, func_ctx, mod_ctx, block, read_operand):
        return None

    # Try table instructions (table.get 0x25, table.set 0x26)
    if compile_table_instruction(opcode, func_ctx, mod_ctx, block, read_operand):
        return None

    # Try conversion instructions
    if compile_conversion_instruction(opcode, func_ctx, block):
        return None

    # Try reference instructions (ref.null 0xD0, ref.is_null 0xD1, ref.func 0xD2)
    if compile_reference_instruction(opcode, func_ctx, mod_ctx, block, read_operand):
        return None

    # drop
    if opcode == 0x1A:
        func_ctx.stack.pop()
        return None

    # select
    if opcode == 0x1B:
        cond = func_ctx.stack.pop()
        val2 = func_ctx.stack.pop()
        val1 = func_ctx.stack.pop()
        # select: if cond != 0, return val1, else val2
        result = func_ctx.stack.new_temp(val1.type)
        qbe_type = _vtype_to_ir_type(val1.type)

        # Use conditional blocks for select
        then_label = func_ctx.new_label("select_then")
        else_label = func_ctx.new_label("select_else")
        merge_label = func_ctx.new_label("select_merge")

        # Branch on condition
        block.terminator = Branch(
            condition=Temporary(cond.name),
            if_true=Label(then_label),
            if_false=Label(else_label),
        )

        # Then block - jumps to merge
        then_block = qbe_func.add_block(then_label[1:])  # Remove @ prefix
        then_block.terminator = Jump(target=Label(merge_label))

        # Else block - jumps to merge
        else_block = qbe_func.add_block(else_label[1:])  # Remove @ prefix
        else_block.terminator = Jump(target=Label(merge_label))

        # Merge block with phi
        merge_block = qbe_func.add_block(merge_label[1:])  # Remove @ prefix
        merge_block.phis.append(
            Phi(
                result=Temporary(result.name),
                result_type=qbe_type,
                incoming=[
                    (Label(then_label), Temporary(val1.name)),
                    (Label(else_label), Temporary(val2.name)),
                ],
            )
        )
        return merge_block

    # select with type (0x1C) - typed select (WASM 2.0)
    if opcode == 0x1C:
        # Read the type vector (count + value types)
        num_types = read_operand("u32")
        _types = [read_operand("u32") for _ in range(num_types)]  # Value types
        # Behavior is identical to basic select - type is just for validation
        cond = func_ctx.stack.pop()
        val2 = func_ctx.stack.pop()
        val1 = func_ctx.stack.pop()
        result = func_ctx.stack.new_temp(val1.type)
        qbe_type = _vtype_to_ir_type(val1.type)

        then_label = func_ctx.new_label("select_then")
        else_label = func_ctx.new_label("select_else")
        merge_label = func_ctx.new_label("select_merge")

        block.terminator = Branch(
            condition=Temporary(cond.name),
            if_true=Label(then_label),
            if_false=Label(else_label),
        )

        then_block = qbe_func.add_block(then_label[1:])
        then_block.terminator = Jump(target=Label(merge_label))

        else_block = qbe_func.add_block(else_label[1:])
        else_block.terminator = Jump(target=Label(merge_label))

        merge_block = qbe_func.add_block(merge_label[1:])
        merge_block.phis.append(
            Phi(
                result=Temporary(result.name),
                result_type=qbe_type,
                incoming=[
                    (Label(then_label), Temporary(val1.name)),
                    (Label(else_label), Temporary(val2.name)),
                ],
            )
        )
        return merge_block

    # ref.as_non_null (0xD4) - assert reference is non-null, trap if null
    if opcode == 0xD4:
        ref = func_ctx.stack.pop()
        # Check if ref is null
        is_null = func_ctx.stack.new_temp_no_push(ValueType.I32)
        block.instructions.append(
            BinaryOp(
                result=Temporary(is_null.name),
                result_type=W,
                op="ceql",
                left=Temporary(ref.name),
                right=IntConst(0),
            )
        )

        # Branch: if null, trap; otherwise continue
        trap_label = func_ctx.new_label("ref_null_trap")
        cont_label = func_ctx.new_label("ref_non_null")

        block.terminator = Branch(
            condition=Temporary(is_null.name),
            if_true=Label(trap_label),
            if_false=Label(cont_label),
        )

        # Trap block
        trap_block = qbe_func.add_block(trap_label[1:])
        trap_block.instructions.append(
            Call(target=Global("__wasm_trap_null_reference"), args=[])
        )
        trap_block.terminator = Halt()

        # Continue block - ref is non-null, push it back
        cont_block = qbe_func.add_block(cont_label[1:])
        func_ctx.stack.push(ref)
        return cont_block

    # br_on_null (0xD5) - branch if reference is null
    if opcode == 0xD5:
        depth = read_operand("u32")
        ref = func_ctx.stack.pop()

        # Check if ref is null
        is_null = func_ctx.stack.new_temp_no_push(ValueType.I32)
        block.instructions.append(
            BinaryOp(
                result=Temporary(is_null.name),
                result_type=W,
                op="ceql",
                left=Temporary(ref.name),
                right=IntConst(0),
            )
        )

        target = func_ctx.get_branch_target(depth)
        branch_label = func_ctx.new_label("br_on_null_branch")
        cont_label = func_ctx.new_label("br_on_null_cont")

        block.terminator = Branch(
            condition=Temporary(is_null.name),
            if_true=Label(branch_label),
            if_false=Label(cont_label),
        )

        # Branch block - jump to target
        branch_block = qbe_func.add_block(branch_label[1:])
        branch_block.terminator = Jump(target=Label(target.label_name))

        # Continue block - ref is non-null, push it back
        cont_block = qbe_func.add_block(cont_label[1:])
        func_ctx.stack.push(ref)
        return cont_block

    # br_on_non_null (0xD6) - branch if reference is non-null
    if opcode == 0xD6:
        depth = read_operand("u32")
        ref = func_ctx.stack.pop()

        # Check if ref is non-null
        is_not_null = func_ctx.stack.new_temp_no_push(ValueType.I32)
        block.instructions.append(
            BinaryOp(
                result=Temporary(is_not_null.name),
                result_type=W,
                op="cnel",  # compare not equal (long)
                left=Temporary(ref.name),
                right=IntConst(0),
            )
        )

        target = func_ctx.get_branch_target(depth)
        branch_label = func_ctx.new_label("br_on_non_null_branch")
        cont_label = func_ctx.new_label("br_on_non_null_cont")

        block.terminator = Branch(
            condition=Temporary(is_not_null.name),
            if_true=Label(branch_label),
            if_false=Label(cont_label),
        )

        # Branch block - push ref and jump to target
        branch_block = qbe_func.add_block(branch_label[1:])
        # Note: When branching, the non-null ref is passed to the target
        branch_block.terminator = Jump(target=Label(target.label_name))

        # Continue block - ref was null, don't push anything
        return qbe_func.add_block(cont_label[1:])

    # 0xFB prefix: GC instructions (struct, array, i31, ref.cast, ref.test)
    if opcode == 0xFB:
        sub_opcode = reader.read_u32_leb128()
        if compile_gc_instruction(sub_opcode, func_ctx, mod_ctx, block, read_operand):
            return None
        raise CompileError(f"unhandled 0xFB sub-opcode: 0x{sub_opcode:02x}")

    # 0xFC prefix: bulk memory, table, saturating conversions, and other extended instructions
    if opcode == 0xFC:
        sub_opcode = reader.read_u32_leb128()
        # Saturating conversions (0x00-0x07)
        if compile_saturating_conversion(sub_opcode, func_ctx, block):
            return None
        if compile_bulk_memory_instruction(
            sub_opcode, func_ctx, mod_ctx, block, read_operand
        ):
            return None
        if compile_table_bulk_instruction(
            sub_opcode, func_ctx, mod_ctx, block, read_operand
        ):
            return None
        raise CompileError(f"unhandled 0xFC sub-opcode: 0x{sub_opcode:02x}")

    # Unhandled opcode
    raise CompileError(f"unhandled opcode: 0x{opcode:02x}")
