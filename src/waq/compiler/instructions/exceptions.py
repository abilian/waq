"""Exception handling instruction compilation (WASM 3.0 proposal)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbepy.ir import (
    Call,
    Global,
    Halt,
    IntConst,
    Jump,
    L,
    Label,
    Temporary,
    W,
)

from waq.compiler.context import ControlFrame
from waq.parser.types import ValueType

if TYPE_CHECKING:
    from collections.abc import Callable

    from qbepy import Function
    from qbepy.ir import Block

    from waq.compiler.context import FunctionContext, ModuleContext


def compile_exception_instruction(
    opcode: int,
    ctx: FunctionContext,
    mod_ctx: ModuleContext,
    func: Function,
    block: Block,
    read_operand: Callable[[str], Any],
) -> Block | None:
    """Compile an exception handling instruction.

    Returns the new current block if control flow changes, or None if unchanged.
    Returns False (via special return) if instruction not handled.
    """
    # try (0x06)
    if opcode == 0x06:
        block_type = read_operand("block_type")
        result_types = _block_type_to_results(block_type, ctx)

        # Create labels for try structure
        try_body_label = ctx.new_label("try_body")
        catch_label = ctx.new_label("catch")
        end_label = ctx.new_label("try_end")

        # Jump to try body
        block.terminator = Jump(target=Label(try_body_label))

        # Create try body block
        try_block = func.add_block(try_body_label[1:])

        # Push try control frame
        frame = ControlFrame(
            kind="try",
            start_depth=ctx.stack.depth,
            result_types=result_types,
            label_name=end_label,  # Branch target for br
            catch_label=catch_label,
            end_label=end_label,
        )
        ctx.push_control(frame)

        # Set up exception handler in runtime
        # Call __wasm_push_exception_handler(catch_label_addr)
        handler_id = ctx.stack.new_temp_no_push(ValueType.I32)
        try_block.instructions.append(
            Call(
                target=Global("__wasm_push_exception_handler"),
                args=[],
                result=Temporary(handler_id.name),
                result_type=W,
            )
        )

        return try_block

    # catch (0x07)
    if opcode == 0x07:
        tag_idx = read_operand("u32")

        # Get the try frame
        if not ctx.control_stack or ctx.control_stack[-1].kind not in ("try", "catch"):
            raise ValueError("catch without matching try")

        frame = ctx.control_stack[-1]

        # End the previous block (try body or previous catch)
        if block.terminator is None:
            # Pop exception handler before leaving try
            block.instructions.append(
                Call(target=Global("__wasm_pop_exception_handler"), args=[])
            )
            block.terminator = Jump(target=Label(frame.end_label))

        # Create catch block
        catch_label = frame.catch_label
        if frame.kind == "catch":
            # Multiple catches - need new label
            catch_label = ctx.new_label("catch")

        catch_block = func.add_block(catch_label[1:])

        # Update frame to catch mode
        frame.kind = "catch"
        frame.exception_tag = tag_idx
        frame.catch_label = ctx.new_label("catch_next")  # For next catch

        # Get exception value from runtime
        # The exception parameters are pushed to the stack
        # For now, we'll get the exception object and extract params
        exc_ref = ctx.stack.new_temp(ValueType.EXTERNREF)
        catch_block.instructions.append(
            Call(
                target=Global("__wasm_get_exception"),
                args=[],
                result=Temporary(exc_ref.name),
                result_type=L,
            )
        )

        return catch_block

    # throw (0x08)
    if opcode == 0x08:
        tag_idx = read_operand("u32")

        # Pop exception parameters from stack based on tag type
        # For now, we support simple exceptions without parameters
        # TODO: Look up tag signature from module and pop appropriate values

        # Call runtime to throw exception
        block.instructions.append(
            Call(
                target=Global("__wasm_throw"),
                args=[(W, IntConst(tag_idx))],
            )
        )

        # Throw doesn't return - mark as unreachable
        block.terminator = Halt()
        return None

    # rethrow (0x09)
    if opcode == 0x09:
        depth = read_operand("u32")

        # Find the catch frame at the given depth
        target = ctx.get_branch_target(depth)
        if target.kind != "catch":
            raise ValueError("rethrow target is not a catch block")

        # Call runtime to rethrow
        block.instructions.append(Call(target=Global("__wasm_rethrow"), args=[]))

        block.terminator = Halt()
        return None

    # delegate (0x18)
    if opcode == 0x18:
        depth = read_operand("u32")

        # Get the try frame
        if not ctx.control_stack or ctx.control_stack[-1].kind != "try":
            raise ValueError("delegate without matching try")

        frame = ctx.pop_control()

        # End try body
        if block.terminator is None:
            block.instructions.append(
                Call(target=Global("__wasm_pop_exception_handler"), args=[])
            )
            block.terminator = Jump(target=Label(frame.end_label))

        # Create end block
        end_block = func.add_block(frame.end_label[1:])

        # Delegate forwards exceptions to outer handler at 'depth'
        # This is handled by the runtime - we just mark the delegation
        # The runtime will pop our handler and re-throw to the outer one

        return end_block

    # catch_all (0x19)
    if opcode == 0x19:
        # Get the try/catch frame
        if not ctx.control_stack or ctx.control_stack[-1].kind not in ("try", "catch"):
            raise ValueError("catch_all without matching try")

        frame = ctx.control_stack[-1]

        # End the previous block
        if block.terminator is None:
            block.instructions.append(
                Call(target=Global("__wasm_pop_exception_handler"), args=[])
            )
            block.terminator = Jump(target=Label(frame.end_label))

        # Create catch_all block
        catch_all_label = ctx.new_label("catch_all")
        catch_all_block = func.add_block(catch_all_label[1:])

        # Update frame
        frame.kind = "catch"
        frame.catch_all_label = catch_all_label
        frame.exception_tag = None  # catch_all catches all tags

        return catch_all_block

    # Not an exception instruction
    return False  # type: ignore[return-value]


def _block_type_to_results(block_type, ctx: FunctionContext) -> tuple[ValueType, ...]:
    """Convert block type to result types."""
    if block_type is None:
        return ()
    if isinstance(block_type, ValueType):
        return (block_type,)
    # Type index - look up function type
    func_type = ctx.module.types[block_type]
    return func_type.results
