"""Value stack simulation for stack-to-SSA conversion."""

from __future__ import annotations

from dataclasses import dataclass, field

from waq.errors import CompileError
from waq.parser.types import ValueType


@dataclass(frozen=True, slots=True)
class StackValue:
    """A value on the operand stack.

    Maps to a QBE temporary.
    Note: name should NOT include the % prefix - qbepy adds it.
    """

    name: str  # QBE temporary name (e.g., "t0" - no % prefix)
    type: ValueType

    def __str__(self) -> str:
        return self.name


@dataclass
class ValueStack:
    """Simulates the WASM operand stack.

    Converts stack operations to SSA form by tracking temporaries.
    """

    _stack: list[StackValue] = field(default_factory=list)
    _temp_counter: int = 0

    def push(self, value: StackValue) -> None:
        """Push a value onto the stack."""
        self._stack.append(value)

    def pop(self) -> StackValue:
        """Pop a value from the stack."""
        if not self._stack:
            raise CompileError("stack underflow")
        return self._stack.pop()

    def pop_n(self, n: int) -> list[StackValue]:
        """Pop n values from the stack (in order: first popped is last in list)."""
        if len(self._stack) < n:
            raise CompileError(f"stack underflow: need {n}, have {len(self._stack)}")
        result = self._stack[-n:]
        self._stack = self._stack[:-n]
        return result

    def peek(self) -> StackValue:
        """Peek at the top value without removing it."""
        if not self._stack:
            raise CompileError("stack underflow on peek")
        return self._stack[-1]

    def peek_at(self, index: int) -> StackValue:
        """Peek at a value at given index from top (0 = top)."""
        if index >= len(self._stack):
            raise CompileError(f"stack underflow on peek_at({index})")
        return self._stack[-(index + 1)]

    def new_temp(self, vtype: ValueType) -> StackValue:
        """Create a new temporary and push it onto the stack."""
        name = f"t{self._temp_counter}"  # No % prefix - qbepy adds it
        self._temp_counter += 1
        value = StackValue(name, vtype)
        self.push(value)
        return value

    def new_temp_no_push(self, vtype: ValueType) -> StackValue:
        """Create a new temporary without pushing it."""
        name = f"t{self._temp_counter}"  # No % prefix - qbepy adds it
        self._temp_counter += 1
        return StackValue(name, vtype)

    @property
    def depth(self) -> int:
        """Current stack depth."""
        return len(self._stack)

    def clone(self) -> ValueStack:
        """Create a copy of this stack."""
        new_stack = ValueStack()
        new_stack._stack = self._stack.copy()
        new_stack._temp_counter = self._temp_counter
        return new_stack

    def truncate(self, depth: int) -> list[StackValue]:
        """Truncate stack to given depth, returning removed values."""
        if depth > len(self._stack):
            raise CompileError(
                f"cannot truncate to depth {depth}, only have {len(self._stack)}"
            )
        removed = self._stack[depth:]
        self._stack = self._stack[:depth]
        return removed

    def clear(self) -> None:
        """Clear the stack."""
        self._stack.clear()

    def __len__(self) -> int:
        return len(self._stack)

    def __repr__(self) -> str:
        items = ", ".join(str(v) for v in self._stack)
        return f"ValueStack([{items}])"
