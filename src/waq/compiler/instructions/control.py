"""Control flow instruction compilation (block, loop, br, br_if, return, etc.)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    BinaryOp,
    Branch,
    Call,
    Comparison,
    Global,
    Halt,
    IntConst,
    Jump,
    L,
    Label,
    Load,
    Phi,
    Return,
    Temporary,
    W,
)

from waq.compiler.context import ControlFrame
from waq.parser.types import BlockType, ValueType

if TYPE_CHECKING:
    from collections.abc import Callable

    from qbepy import Function
    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext


def compile_control_instruction(
    opcode: int,
    ctx: FunctionContext,
    func: Function,
    block: Block,
    read_operand: Callable[[str], Any],
) -> Block | None:
    """Compile a control flow instruction.

    Returns the new current block if it changed, or None if unchanged.
    """
    # unreachable
    if opcode == 0x00:
        block.instructions.append(
            Call(target=Global("__wasm_trap_unreachable"), args=[])
        )
        block.terminator = Halt()
        return None

    # nop
    if opcode == 0x01:
        return None

    # block
    if opcode == 0x02:
        block_type = read_operand("block_type")
        result_types = _block_type_to_results(block_type, ctx)
        end_label = ctx.new_label("block_end")

        frame = ControlFrame(
            kind="block",
            start_depth=ctx.stack.depth,
            result_types=result_types,
            label_name=end_label,
        )
        ctx.push_control(frame)
        return None

    # loop
    if opcode == 0x03:
        block_type = read_operand("block_type")
        result_types = _block_type_to_results(block_type, ctx)
        loop_label = ctx.new_label("loop")

        # Jump to loop label
        block.terminator = Jump(target=Label(loop_label))

        # Create loop block (strip @ prefix for add_block)
        loop_block = func.add_block(loop_label.removeprefix("@"))

        frame = ControlFrame(
            kind="loop",
            start_depth=ctx.stack.depth,
            result_types=result_types,
            label_name=loop_label,  # Branch target is loop start
        )
        ctx.push_control(frame)
        return loop_block

    # if
    if opcode == 0x04:
        block_type = read_operand("block_type")
        result_types = _block_type_to_results(block_type, ctx)

        cond = ctx.stack.pop()
        then_label = ctx.new_label("then")
        else_label = ctx.new_label("else")
        end_label = ctx.new_label("if_end")

        # Conditional jump
        block.terminator = Branch(
            condition=Temporary(cond.name),
            if_true=Label(then_label),
            if_false=Label(else_label),
        )

        # Create then block (strip @ prefix for add_block)
        then_block = func.add_block(then_label.removeprefix("@"))

        frame = ControlFrame(
            kind="if",
            start_depth=ctx.stack.depth,
            result_types=result_types,
            label_name=end_label,
            else_label=else_label,
            end_label=end_label,
        )
        ctx.push_control(frame)
        return then_block

    # else
    if opcode == 0x05:
        frame = ctx.control_stack[-1]
        if frame.kind != "if":
            raise ValueError("else without matching if")

        # If we have result types, capture values from then branch for phi
        if frame.result_types:
            # Peek the stack values (don't pop - they represent the results)
            then_values = []
            for i in range(len(frame.result_types)):
                # Get value from top of stack (reverse order for peek)
                val = ctx.stack.peek_at(len(frame.result_types) - 1 - i)
                then_values.append(val.name)
            frame.then_values = then_values
            frame.then_label = block.name  # Current block's name (no @ prefix)
            # Pop the values - they're consumed, else will push new ones
            ctx.stack.pop_n(len(frame.result_types))

        # Jump from then block to end
        assert frame.end_label is not None
        block.terminator = Jump(target=Label(frame.end_label))

        # Create else block (strip @ prefix for add_block)
        assert frame.else_label is not None
        else_label = frame.else_label
        # Clear else_label so end doesn't try to create a duplicate
        frame.else_label = None
        return func.add_block(else_label.removeprefix("@"))

    # end (0x0B)
    if opcode == 0x0B:
        if not ctx.control_stack:
            # End of function
            return None

        frame = ctx.pop_control()

        if frame.kind == "if" and frame.else_label:
            # If without else - else just falls through
            # Need to emit the else label pointing to end
            assert frame.end_label is not None
            block.terminator = Jump(target=Label(frame.end_label))
            else_label = frame.else_label
            else_block = func.add_block(else_label.removeprefix("@"))
            else_block.terminator = Jump(target=Label(frame.end_label))

        # Handle if/else with results using phi nodes
        if frame.kind == "if" and frame.then_values is not None and frame.result_types:
            # We had an else branch with results
            # Capture else branch values and current block label
            else_values = []
            for i in range(len(frame.result_types)):
                val = ctx.stack.peek_at(len(frame.result_types) - 1 - i)
                else_values.append(val.name)
            # Strip @ prefix - Label() will add it back
            else_label_for_phi = block.name  # Use name, not label (no @ prefix)

            # Pop else values from stack
            ctx.stack.pop_n(len(frame.result_types))

            # Jump to end
            block.terminator = Jump(target=Label(frame.label_name))

            # Create end block
            end_block = func.add_block(frame.label_name.removeprefix("@"))

            # Emit phi nodes for each result
            # then_label is already without @ prefix
            then_label_for_phi = frame.then_label
            for i, vtype in enumerate(frame.result_types):
                phi_result = ctx.stack.new_temp(vtype)
                qbe_type = _vtype_to_ir_type(vtype)
                incoming = [
                    (Label(then_label_for_phi), Temporary(frame.then_values[i])),
                    (Label(else_label_for_phi), Temporary(else_values[i])),
                ]
                end_block.phis.append(
                    Phi(
                        result=Temporary(phi_result.name),
                        result_type=qbe_type,
                        incoming=incoming,
                    )
                )

            return end_block

        # Jump to end label (for block and if without results)
        if frame.kind != "loop":
            if block.terminator is None:
                block.terminator = Jump(target=Label(frame.label_name))
            label = frame.label_name
            return func.add_block(label.removeprefix("@"))

        return None

    # br
    if opcode == 0x0C:
        depth = read_operand("u32")
        target = ctx.get_branch_target(depth)
        _emit_branch(ctx, block, target)
        return None

    # br_if
    if opcode == 0x0D:
        depth = read_operand("u32")
        cond = ctx.stack.pop()
        target = ctx.get_branch_target(depth)

        cont_label = ctx.new_label("br_if_cont")
        branch_label = ctx.new_label("br_if_branch")

        # Test condition
        block.terminator = Branch(
            condition=Temporary(cond.name),
            if_true=Label(branch_label),
            if_false=Label(cont_label),
        )

        # Branch block
        branch_block = func.add_block(branch_label.removeprefix("@"))
        _emit_branch(ctx, branch_block, target)

        # Continue block
        return func.add_block(cont_label.removeprefix("@"))

    # br_table
    if opcode == 0x0E:
        # Read table of label indices
        num_targets = read_operand("u32")
        targets = [read_operand("u32") for _ in range(num_targets)]
        default_target = read_operand("u32")

        idx = ctx.stack.pop()

        # For now, emit a chain of conditionals
        # TODO: Generate jump table for dense cases
        for i, depth in enumerate(targets):
            target = ctx.get_branch_target(depth)
            check_label = ctx.new_label(f"br_table_{i}")
            next_label = ctx.new_label(f"br_table_next_{i}")

            # Check if idx == i
            cmp_temp = ctx.stack.new_temp_no_push(ValueType.I32)
            block.instructions.append(
                Comparison(
                    result=Temporary(cmp_temp.name),
                    result_type=W,
                    op="ceqw",
                    left=Temporary(idx.name),
                    right=IntConst(i),
                )
            )
            block.terminator = Branch(
                condition=Temporary(cmp_temp.name),
                if_true=Label(check_label),
                if_false=Label(next_label),
            )

            # Branch block
            check_block = func.add_block(check_label.removeprefix("@"))
            _emit_branch(ctx, check_block, target)

            # Next check
            block = func.add_block(next_label.removeprefix("@"))

        # Default case
        default_frame = ctx.get_branch_target(default_target)
        _emit_branch(ctx, block, default_frame)
        return None

    # return
    if opcode == 0x0F:
        _emit_return(ctx, block)
        return None

    # call
    if opcode == 0x10:
        func_idx = read_operand("u32")
        _emit_call(ctx, block, func_idx)
        return None

    # call_indirect
    if opcode == 0x11:
        type_idx = read_operand("u32")
        _table_idx = read_operand("u32")  # Always 0 in WASM 1.0
        _emit_call_indirect(ctx, block, type_idx)
        return None

    return None


def _block_type_to_results(
    block_type: BlockType, ctx: FunctionContext
) -> tuple[ValueType, ...]:
    """Convert block type to result types."""
    if block_type is None:
        return ()
    if isinstance(block_type, ValueType):
        return (block_type,)
    # Type index - look up function type
    func_type = ctx.module.types[block_type]
    return func_type.results


def _emit_branch(ctx: FunctionContext, block: Block, target: ControlFrame) -> None:
    """Emit a branch to a control frame."""
    # For loop, branch goes to start (no results needed at branch point)
    # For block/if, branch goes to end with results
    block.terminator = Jump(target=Label(target.label_name))


def _emit_return(ctx: FunctionContext, block: Block) -> None:
    """Emit a function return."""
    result_types = ctx.func_type.results
    if not result_types:
        block.terminator = Return(value=None)
    elif len(result_types) == 1:
        value = ctx.stack.pop()
        block.terminator = Return(value=Temporary(value.name))
    else:
        # Multi-value return - Phase 3
        raise NotImplementedError("multi-value return")


def _vtype_to_ir_type(vtype: ValueType):
    """Convert WASM ValueType to qbepy IR type."""
    from qbepy.ir import D, L, S  # noqa: PLC0415

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


def _emit_call(ctx: FunctionContext, block: Block, func_idx: int) -> None:
    """Emit a function call."""

    # Get function type
    func_type = ctx.module.get_func_type(func_idx)

    # Pop arguments (in reverse order)
    args = ctx.stack.pop_n(len(func_type.params))

    # Build argument list for Call instruction
    call_args = []
    for arg, ptype in zip(args, func_type.params, strict=True):
        qbe_type = _vtype_to_ir_type(ptype)
        call_args.append((qbe_type, Temporary(arg.name)))

    # Get function name (we need ModuleContext for this)
    # For now, generate a placeholder
    func_name = f"__wasm_func_{func_idx}"

    # Emit call
    if not func_type.results:
        block.instructions.append(Call(target=Global(func_name), args=call_args))
    elif len(func_type.results) == 1:
        result = ctx.stack.new_temp(func_type.results[0])
        qbe_type = _vtype_to_ir_type(func_type.results[0])
        block.instructions.append(
            Call(
                target=Global(func_name),
                args=call_args,
                result=Temporary(result.name),
                result_type=qbe_type,
            )
        )
    else:
        # Multi-value return - Phase 3
        raise NotImplementedError("multi-value return")


def _emit_call_indirect(ctx: FunctionContext, block: Block, type_idx: int) -> None:
    """Emit an indirect function call through a table."""

    # Get function type from type index
    func_type = ctx.module.types[type_idx]

    # Pop table index (i32) from stack
    table_idx = ctx.stack.pop()

    # Pop arguments (in reverse order)
    args = ctx.stack.pop_n(len(func_type.params))

    # Build argument list for Call instruction
    call_args = []
    for arg, ptype in zip(args, func_type.params, strict=True):
        qbe_type = _vtype_to_ir_type(ptype)
        call_args.append((qbe_type, Temporary(arg.name)))

    # Load table base pointer
    table_base = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        Load(
            result=Temporary(table_base.name),
            result_type=L,
            address=Global("__wasm_table"),
        )
    )

    # Calculate offset: table_idx * 8 (pointer size)
    # First extend table_idx to 64-bit
    from qbepy.ir import Conversion  # noqa: PLC0415

    idx64 = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        Conversion(
            op="extuw",
            result=Temporary(idx64.name),
            result_type=L,
            operand=Temporary(table_idx.name),
        )
    )

    offset = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(offset.name),
            result_type=L,
            op="mul",
            left=Temporary(idx64.name),
            right=IntConst(8),  # sizeof(void*)
        )
    )

    # Calculate address: table_base + offset
    addr = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        BinaryOp(
            result=Temporary(addr.name),
            result_type=L,
            op="add",
            left=Temporary(table_base.name),
            right=Temporary(offset.name),
        )
    )

    # Load function pointer
    func_ptr = ctx.stack.new_temp_no_push(ValueType.I64)
    block.instructions.append(
        Load(
            result=Temporary(func_ptr.name),
            result_type=L,
            address=Temporary(addr.name),
        )
    )

    # Emit indirect call
    if not func_type.results:
        block.instructions.append(Call(target=Temporary(func_ptr.name), args=call_args))
    elif len(func_type.results) == 1:
        result = ctx.stack.new_temp(func_type.results[0])
        qbe_type = _vtype_to_ir_type(func_type.results[0])
        block.instructions.append(
            Call(
                target=Temporary(func_ptr.name),
                args=call_args,
                result=Temporary(result.name),
                result_type=qbe_type,
            )
        )
    else:
        # Multi-value return - Phase 3
        raise NotImplementedError("multi-value return")
