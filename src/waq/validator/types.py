"""Validation context and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from waq.parser.module import WasmModule
from waq.parser.types import FuncType, ValueType


class ValidationSeverity(Enum):
    """Severity level for validation issues."""

    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: ValidationSeverity
    message: str
    location: str | None = None
    """Human-readable location (e.g., 'function 3, instruction 42')"""

    func_idx: int | None = None
    """Function index where issue occurred, if applicable"""

    instr_offset: int | None = None
    """Instruction byte offset within function, if applicable"""

    def __str__(self) -> str:
        parts = [self.severity.name.lower()]
        if self.location:
            parts.append(f"at {self.location}")
        parts.append(self.message)
        return ": ".join(parts)


@dataclass
class ValidationResult:
    """Result of module validation."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings/info are OK)."""
        return not any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        """All error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """All warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def add_error(
        self,
        message: str,
        location: str | None = None,
        func_idx: int | None = None,
        instr_offset: int | None = None,
    ) -> None:
        """Add an error-level issue."""
        self.issues.append(
            ValidationIssue(
                ValidationSeverity.ERROR, message, location, func_idx, instr_offset
            )
        )

    def add_warning(
        self,
        message: str,
        location: str | None = None,
        func_idx: int | None = None,
        instr_offset: int | None = None,
    ) -> None:
        """Add a warning-level issue."""
        self.issues.append(
            ValidationIssue(
                ValidationSeverity.WARNING, message, location, func_idx, instr_offset
            )
        )

    def __str__(self) -> str:
        if not self.issues:
            return "validation passed"
        return "\n".join(str(i) for i in self.issues)


@dataclass
class ControlFrame:
    """Control frame for validation stack tracking."""

    kind: str  # "block", "loop", "if"
    start_depth: int
    result_types: tuple[ValueType, ...]
    param_types: tuple[ValueType, ...] = ()
    unreachable: bool = False


@dataclass
class ValidationContext:
    """Context for validating a WASM module."""

    module: WasmModule
    result: ValidationResult = field(default_factory=ValidationResult)

    # Current function being validated
    current_func_idx: int | None = None
    current_func_type: FuncType | None = None

    # Locals for current function (params + locals)
    locals: list[ValueType] = field(default_factory=list)

    # Value stack (types only, not actual values)
    value_stack: list[ValueType] = field(default_factory=list)

    # Control stack
    control_stack: list[ControlFrame] = field(default_factory=list)

    # Current instruction offset (for error reporting)
    current_offset: int = 0

    def error(self, message: str) -> None:
        """Record an error at the current location."""
        location = None
        if self.current_func_idx is not None:
            location = f"function {self.current_func_idx}"
            if self.current_offset > 0:
                location += f", offset {self.current_offset}"
        self.result.add_error(
            message, location, self.current_func_idx, self.current_offset
        )

    def warning(self, message: str) -> None:
        """Record a warning at the current location."""
        location = None
        if self.current_func_idx is not None:
            location = f"function {self.current_func_idx}"
        self.result.add_warning(
            message, location, self.current_func_idx, self.current_offset
        )

    def push_value(self, vtype: ValueType) -> None:
        """Push a value type onto the stack."""
        self.value_stack.append(vtype)

    def pop_value(self) -> ValueType | None:
        """Pop a value type from the stack. Returns None on underflow."""
        if not self.value_stack:
            # Check if we're in unreachable code
            if self.control_stack and self.control_stack[-1].unreachable:
                return ValueType.I32  # Dummy type for unreachable code
            return None
        return self.value_stack.pop()

    def pop_expect(self, expected: ValueType) -> bool:
        """Pop and check that the type matches. Returns True if OK."""
        actual = self.pop_value()
        if actual is None:
            self.error(f"stack underflow: expected {expected}")
            return False
        if actual != expected:
            self.error(f"type mismatch: expected {expected}, got {actual}")
            return False
        return True

    def peek_value(self) -> ValueType | None:
        """Peek at the top value without popping."""
        if not self.value_stack:
            return None
        return self.value_stack[-1]

    def push_control(self, kind: str, result_types: tuple[ValueType, ...]) -> None:
        """Push a control frame."""
        frame = ControlFrame(
            kind=kind,
            start_depth=len(self.value_stack),
            result_types=result_types,
        )
        self.control_stack.append(frame)

    def pop_control(self) -> ControlFrame | None:
        """Pop a control frame, checking stack depth."""
        if not self.control_stack:
            self.error("control stack underflow")
            return None

        frame = self.control_stack.pop()

        # Check that stack has exactly the result types
        expected_depth = frame.start_depth + len(frame.result_types)
        actual_depth = len(self.value_stack)

        if not frame.unreachable:
            if actual_depth < expected_depth:
                self.error(
                    f"stack underflow at block end: expected {len(frame.result_types)} values"
                )
            elif actual_depth > expected_depth:
                self.error(
                    f"stack has extra values at block end: expected {len(frame.result_types)}, got {actual_depth - frame.start_depth}"
                )

        return frame

    def get_local_type(self, idx: int) -> ValueType | None:
        """Get the type of a local variable."""
        if idx >= len(self.locals):
            self.error(f"local index {idx} out of bounds (have {len(self.locals)})")
            return None
        return self.locals[idx]

    def get_func_type(self, func_idx: int) -> FuncType | None:
        """Get the type of a function by index."""
        try:
            return self.module.get_func_type(func_idx)
        except (ValueError, IndexError):
            self.error(f"function index {func_idx} out of bounds")
            return None

    def reset_for_function(self, func_idx: int, func_type: FuncType, local_types: list[ValueType]) -> None:
        """Reset context for validating a new function."""
        self.current_func_idx = func_idx
        self.current_func_type = func_type
        self.locals = list(func_type.params) + local_types
        self.value_stack.clear()
        self.control_stack.clear()
        self.current_offset = 0

        # Push implicit function block
        self.push_control("function", func_type.results)
