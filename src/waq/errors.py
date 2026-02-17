"""Error definitions for the WASM-to-QBE compiler."""

from __future__ import annotations


class WasmError(Exception):
    """Base class for all WASM compiler errors."""


class ParseError(WasmError):
    """Error during WASM binary parsing."""

    def __init__(self, message: str, offset: int | None = None) -> None:
        self.offset = offset
        if offset is not None:
            message = f"at offset 0x{offset:x}: {message}"
        super().__init__(message)


class ValidationError(WasmError):
    """Error during WASM module validation."""


class CompileError(WasmError):
    """Error during compilation to QBE.

    Attributes:
        func_idx: Function index where error occurred, if applicable
        instr_offset: Instruction byte offset within function, if applicable
        func_name: Function name, if known
    """

    def __init__(
        self,
        message: str,
        func_idx: int | None = None,
        instr_offset: int | None = None,
        func_name: str | None = None,
    ) -> None:
        self.func_idx = func_idx
        self.instr_offset = instr_offset
        self.func_name = func_name

        # Build location string
        location_parts = []
        if func_name:
            location_parts.append(f"function '{func_name}'")
        elif func_idx is not None:
            location_parts.append(f"function {func_idx}")
        if instr_offset is not None:
            location_parts.append(f"offset 0x{instr_offset:x}")

        if location_parts:
            message = f"at {', '.join(location_parts)}: {message}"
        super().__init__(message)


class TrapError(WasmError):
    """Runtime trap condition detected at compile time."""

    def __init__(self, trap_type: str, message: str = "") -> None:
        self.trap_type = trap_type
        super().__init__(f"{trap_type}: {message}" if message else trap_type)
