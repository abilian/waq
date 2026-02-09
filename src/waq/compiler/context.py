"""Compilation context for WASM to QBE translation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from waq.parser.module import ExportKind, ImportKind, WasmModule
from waq.parser.types import FuncType, ValueType

from .stack import ValueStack

if TYPE_CHECKING:
    from qbepy import Block, Function, Module


@dataclass
class ControlFrame:
    """Represents a control flow structure (block, loop, if, try)."""

    kind: str  # "block", "loop", "if", "try", "catch"
    start_depth: int  # Stack depth at entry
    result_types: tuple[ValueType, ...]  # Expected result types
    label_name: str  # QBE block label for branch target
    else_label: str | None = None  # For if: the else block label
    end_label: str | None = None  # For if/try: the merge block label
    # For if/else with results: store values from then branch for phi
    then_values: list[str] | None = None  # Temp names from then branch
    then_label: str | None = None  # Label where then branch ends
    # Exception handling fields
    catch_label: str | None = None  # For try: the catch block label
    catch_all_label: str | None = None  # For try: the catch_all block label
    delegate_depth: int | None = None  # For delegate: outer try depth
    exception_tag: int | None = None  # For catch: the tag being caught


@dataclass
class FunctionContext:
    """Context for compiling a single function."""

    # The WASM module
    module: WasmModule

    # Function index in the module
    func_idx: int

    # Function type
    func_type: FuncType

    # Local variables (params + locals)
    locals: list[ValueType] = field(default_factory=list)

    # QBE function being built
    qbe_func: Function | None = None

    # Current QBE block
    current_block: Block | None = None

    # Value stack for SSA conversion
    stack: ValueStack = field(default_factory=ValueStack)

    # Control flow stack
    control_stack: list[ControlFrame] = field(default_factory=list)

    # Local variable stack addresses (index -> QBE temp holding address)
    local_addrs: dict[int, str] = field(default_factory=dict)

    # Block label counter
    _label_counter: int = 0

    def new_label(self, prefix: str = "L") -> str:
        """Generate a new unique block label.

        Note: Don't include @ prefix - qbepy adds it.
        """
        name = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return name

    def get_local_type(self, idx: int) -> ValueType:
        """Get the type of a local variable."""
        if idx >= len(self.locals):
            raise ValueError(f"local index {idx} out of range")
        return self.locals[idx]

    def get_local_addr(self, idx: int) -> str:
        """Get the stack address temp for a local.

        Note: Names don't include % prefix - qbepy adds it.
        """
        if idx not in self.local_addrs:
            raise ValueError(f"local {idx} not allocated")
        return self.local_addrs[idx]

    def set_local_addr(self, idx: int, addr_temp: str) -> None:
        """Set the stack address temp for a local."""
        self.local_addrs[idx] = addr_temp

    def push_control(self, frame: ControlFrame) -> None:
        """Push a control frame."""
        self.control_stack.append(frame)

    def pop_control(self) -> ControlFrame:
        """Pop a control frame."""
        if not self.control_stack:
            raise ValueError("control stack underflow")
        return self.control_stack.pop()

    def get_branch_target(self, depth: int) -> ControlFrame:
        """Get the control frame at the given branch depth."""
        if depth >= len(self.control_stack):
            raise ValueError(f"branch depth {depth} exceeds control stack")
        # depth 0 is the innermost frame
        return self.control_stack[-(depth + 1)]


@dataclass
class ModuleContext:
    """Context for compiling a complete module."""

    # The WASM module
    module: WasmModule

    # QBE module being built
    qbe_module: Module | None = None

    # Mapping of function indices to QBE function names
    func_names: dict[int, str] = field(default_factory=dict)

    # Mapping of global indices to QBE data names
    global_names: dict[int, str] = field(default_factory=dict)

    # Memory base pointer name (no $ prefix - qbepy adds it)
    memory_base: str = "__wasm_memory"

    # Memory size name (no $ prefix - qbepy adds it)
    memory_size: str = "__wasm_memory_size"

    def get_func_name(self, func_idx: int) -> str:
        """Get the QBE function name for a WASM function index.

        Note: Do not include $ prefix - qbepy adds it automatically.
        """
        if func_idx in self.func_names:
            return self.func_names[func_idx]

        # Check if it's an imported function
        num_imports = self.module.num_imported_funcs()
        if func_idx < num_imports:
            # Find the import
            import_idx = 0
            for imp in self.module.imports:
                if imp.kind == ImportKind.FUNC:
                    if import_idx == func_idx:
                        # Use module$name format for imported functions
                        # This allows linking with external C functions
                        name = imp.name
                        self.func_names[func_idx] = name
                        return name
                    import_idx += 1
            raise ValueError(f"imported function {func_idx} not found")

        # Check if exported
        for exp in self.module.exports:
            if exp.kind == ExportKind.FUNC and exp.index == func_idx:
                # Exported functions keep their name
                name = exp.name
                self.func_names[func_idx] = name
                return name

        # Internal function
        wasm_name = self.module.get_func_name(func_idx)
        name = f"__wasm_{wasm_name}"
        self.func_names[func_idx] = name
        return name

    def get_global_name(self, global_idx: int) -> str:
        """Get the QBE data name for a WASM global index.

        Note: Do not include $ prefix - qbepy adds it automatically.
        """
        if global_idx in self.global_names:
            return self.global_names[global_idx]

        # Check if exported
        for exp in self.module.exports:
            if exp.kind == ExportKind.GLOBAL and exp.index == global_idx:
                name = exp.name
                self.global_names[global_idx] = name
                return name

        # Internal global
        name = f"__wasm_global_{global_idx}"
        self.global_names[global_idx] = name
        return name
