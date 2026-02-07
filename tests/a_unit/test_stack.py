"""Unit tests for the value stack (SSA conversion)."""

from __future__ import annotations

import pytest

from waq.compiler.stack import StackValue, ValueStack
from waq.errors import CompileError
from waq.parser.types import ValueType


class TestStackValue:
    """Tests for StackValue."""

    def test_create(self):
        val = StackValue(name="t0", type=ValueType.I32)
        assert val.name == "t0"
        assert val.type == ValueType.I32

    def test_str(self):
        val = StackValue(name="t42", type=ValueType.I64)
        assert str(val) == "t42"


class TestValueStack:
    """Tests for ValueStack operations."""

    def test_push_pop(self):
        stack = ValueStack()
        val = StackValue("t0", ValueType.I32)
        stack.push(val)
        assert stack.pop() == val

    def test_pop_empty(self):
        stack = ValueStack()
        with pytest.raises(CompileError, match="stack underflow"):
            stack.pop()

    def test_peek(self):
        stack = ValueStack()
        val = StackValue("t0", ValueType.I32)
        stack.push(val)
        assert stack.peek() == val
        assert stack.depth == 1  # Still there

    def test_new_temp(self):
        stack = ValueStack()
        temp = stack.new_temp(ValueType.I32)
        assert temp.name == "t0"
        assert temp.type == ValueType.I32
        assert stack.depth == 1

        temp2 = stack.new_temp(ValueType.I64)
        assert temp2.name == "t1"
        assert stack.depth == 2

    def test_new_temp_no_push(self):
        stack = ValueStack()
        temp = stack.new_temp_no_push(ValueType.F32)
        assert temp.name == "t0"
        assert stack.depth == 0  # Not pushed

    def test_pop_n(self):
        stack = ValueStack()
        stack.new_temp(ValueType.I32)  # %t0
        stack.new_temp(ValueType.I32)  # %t1
        stack.new_temp(ValueType.I32)  # %t2

        values = stack.pop_n(2)
        assert len(values) == 2
        assert values[0].name == "t1"
        assert values[1].name == "t2"
        assert stack.depth == 1

    def test_pop_n_underflow(self):
        stack = ValueStack()
        stack.new_temp(ValueType.I32)
        with pytest.raises(CompileError, match="stack underflow"):
            stack.pop_n(5)

    def test_clone(self):
        stack = ValueStack()
        stack.new_temp(ValueType.I32)
        stack.new_temp(ValueType.I64)

        clone = stack.clone()
        assert clone.depth == 2
        clone.pop()
        assert stack.depth == 2  # Original unchanged

    def test_truncate(self):
        stack = ValueStack()
        stack.new_temp(ValueType.I32)
        stack.new_temp(ValueType.I64)
        stack.new_temp(ValueType.F32)

        removed = stack.truncate(1)
        assert len(removed) == 2
        assert stack.depth == 1

    def test_clear(self):
        stack = ValueStack()
        stack.new_temp(ValueType.I32)
        stack.new_temp(ValueType.I64)
        stack.clear()
        assert stack.depth == 0
