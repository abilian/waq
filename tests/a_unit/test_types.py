"""Unit tests for WASM types."""

from __future__ import annotations

import pytest

from waq.parser.types import (
    FuncType,
    GlobalType,
    Limits,
    MemoryType,
    TableType,
    ValueType,
)


class TestValueType:
    """Tests for ValueType enum."""

    def test_to_qbe(self):
        assert ValueType.I32.to_qbe() == "w"
        assert ValueType.I64.to_qbe() == "l"
        assert ValueType.F32.to_qbe() == "s"
        assert ValueType.F64.to_qbe() == "d"
        assert ValueType.FUNCREF.to_qbe() == "l"

    def test_str(self):
        assert str(ValueType.I32) == "i32"
        assert str(ValueType.F64) == "f64"


class TestFuncType:
    """Tests for FuncType."""

    def test_no_params_no_results(self):
        ft = FuncType(params=(), results=())
        assert str(ft) == "() -> ()"

    def test_params_and_results(self):
        ft = FuncType(
            params=(ValueType.I32, ValueType.I64),
            results=(ValueType.I32,),
        )
        assert str(ft) == "(i32, i64) -> (i32)"

    def test_frozen(self):
        ft = FuncType(params=(ValueType.I32,), results=())
        with pytest.raises(AttributeError):
            ft.params = ()  # Should be immutable


class TestLimits:
    """Tests for Limits."""

    def test_min_only(self):
        lim = Limits(min=1)
        assert str(lim) == "1.."

    def test_min_and_max(self):
        lim = Limits(min=1, max=10)
        assert str(lim) == "1..10"


class TestMemoryType:
    """Tests for MemoryType."""

    def test_basic(self):
        mt = MemoryType(limits=Limits(min=1))
        assert str(mt) == "memory 1.."

    def test_memory64(self):
        mt = MemoryType(limits=Limits(min=1), is_memory64=True)
        assert "(memory64)" in str(mt)


class TestTableType:
    """Tests for TableType."""

    def test_funcref_table(self):
        tt = TableType(limits=Limits(min=0, max=10), elem_type=ValueType.FUNCREF)
        assert "funcref" in str(tt)


class TestGlobalType:
    """Tests for GlobalType."""

    def test_immutable(self):
        gt = GlobalType(value_type=ValueType.I32, mutable=False)
        assert str(gt) == "i32"

    def test_mutable(self):
        gt = GlobalType(value_type=ValueType.I64, mutable=True)
        assert str(gt) == "mut i64"
