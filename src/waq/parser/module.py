"""WASM module parsing and representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from waq.errors import ParseError

from .binary import WASM_MAGIC, WASM_VERSION, BinaryReader
from .types import (
    ArrayType,
    CompositeType,
    FuncType,
    GlobalType,
    MemoryType,
    StructType,
    TableType,
    ValueType,
)


class SectionId(IntEnum):
    """WASM section identifiers."""

    CUSTOM = 0
    TYPE = 1
    IMPORT = 2
    FUNCTION = 3
    TABLE = 4
    MEMORY = 5
    GLOBAL = 6
    EXPORT = 7
    START = 8
    ELEMENT = 9
    CODE = 10
    DATA = 11
    DATA_COUNT = 12


class ExportKind(IntEnum):
    """Export descriptor kinds."""

    FUNC = 0
    TABLE = 1
    MEMORY = 2
    GLOBAL = 3


class ImportKind(IntEnum):
    """Import descriptor kinds."""

    FUNC = 0
    TABLE = 1
    MEMORY = 2
    GLOBAL = 3


@dataclass
class Import:
    """Import entry."""

    module: str
    name: str
    kind: ImportKind
    # For FUNC: type index
    # For TABLE: TableType
    # For MEMORY: MemoryType
    # For GLOBAL: GlobalType
    desc: int | TableType | MemoryType | GlobalType


@dataclass
class Export:
    """Export entry."""

    name: str
    kind: ExportKind
    index: int


@dataclass
class Global:
    """Global variable definition."""

    type: GlobalType
    init_expr: bytes  # Raw init expression bytecode


@dataclass
class FunctionBody:
    """Function body from code section."""

    locals: list[tuple[int, ValueType]]  # (count, type) pairs
    code: bytes  # Raw instruction bytecode

    def all_locals(self) -> list[ValueType]:
        """Expand local declarations to full list."""
        result = []
        for count, vtype in self.locals:
            result.extend([vtype] * count)
        return result


@dataclass
class DataSegment:
    """Data segment (memory initializer)."""

    memory_idx: int
    offset_expr: bytes  # Raw offset expression
    data: bytes


@dataclass
class ElementSegment:
    """Element segment (table initializer)."""

    table_idx: int
    offset_expr: bytes  # Raw offset expression
    func_indices: list[int]


@dataclass
class WasmModule:
    """Complete WASM module representation."""

    # Type section (composite types: functions, structs, arrays)
    types: list[CompositeType] = field(default_factory=list)

    # Import section
    imports: list[Import] = field(default_factory=list)

    # Function section (type indices for defined functions)
    func_types: list[int] = field(default_factory=list)

    # Table section
    tables: list[TableType] = field(default_factory=list)

    # Memory section
    memories: list[MemoryType] = field(default_factory=list)

    # Global section
    globals: list[Global] = field(default_factory=list)

    # Export section
    exports: list[Export] = field(default_factory=list)

    # Start function index
    start: int | None = None

    # Element section
    elements: list[ElementSegment] = field(default_factory=list)

    # Code section
    code: list[FunctionBody] = field(default_factory=list)

    # Data section
    data: list[DataSegment] = field(default_factory=list)

    # Custom sections
    custom: dict[str, bytes] = field(default_factory=dict)

    # Derived: function names from name section
    function_names: dict[int, str] = field(default_factory=dict)

    def num_imported_funcs(self) -> int:
        """Count of imported functions."""
        return sum(1 for imp in self.imports if imp.kind == ImportKind.FUNC)

    def num_imported_tables(self) -> int:
        """Count of imported tables."""
        return sum(1 for imp in self.imports if imp.kind == ImportKind.TABLE)

    def num_imported_memories(self) -> int:
        """Count of imported memories."""
        return sum(1 for imp in self.imports if imp.kind == ImportKind.MEMORY)

    def num_imported_globals(self) -> int:
        """Count of imported globals."""
        return sum(1 for imp in self.imports if imp.kind == ImportKind.GLOBAL)

    def get_func_type(self, func_idx: int) -> FuncType:
        """Get function type by function index."""
        num_imports = self.num_imported_funcs()
        if func_idx < num_imports:
            # Imported function
            import_idx = 0
            for imp in self.imports:
                if imp.kind == ImportKind.FUNC:
                    if import_idx == func_idx:
                        assert isinstance(imp.desc, int)
                        type_def = self.types[imp.desc]
                        if not isinstance(type_def, FuncType):
                            raise ValueError(f"type {imp.desc} is not a function type")
                        return type_def
                    import_idx += 1
            raise ValueError(f"import function {func_idx} not found")
        # Defined function
        local_idx = func_idx - num_imports
        if local_idx >= len(self.func_types):
            raise ValueError(f"function {func_idx} not found")
        type_def = self.types[self.func_types[local_idx]]
        if not isinstance(type_def, FuncType):
            raise ValueError(
                f"type {self.func_types[local_idx]} is not a function type"
            )
        return type_def

    def get_struct_type(self, type_idx: int) -> StructType:
        """Get struct type by type index."""
        if type_idx >= len(self.types):
            raise ValueError(f"type index {type_idx} out of range")
        type_def = self.types[type_idx]
        if not isinstance(type_def, StructType):
            raise ValueError(f"type {type_idx} is not a struct type")
        return type_def

    def get_array_type(self, type_idx: int) -> ArrayType:
        """Get array type by type index."""
        if type_idx >= len(self.types):
            raise ValueError(f"type index {type_idx} out of range")
        type_def = self.types[type_idx]
        if not isinstance(type_def, ArrayType):
            raise ValueError(f"type {type_idx} is not an array type")
        return type_def

    def get_func_name(self, func_idx: int) -> str:
        """Get function name, or generate one."""
        if func_idx in self.function_names:
            return self.function_names[func_idx]
        # Check exports
        for exp in self.exports:
            if exp.kind == ExportKind.FUNC and exp.index == func_idx:
                return exp.name
        return f"func_{func_idx}"


def parse_module(data: bytes) -> WasmModule:
    """Parse a WASM binary module."""
    reader = BinaryReader(data)

    # Check magic number
    magic = reader.read_bytes(4)
    if magic != WASM_MAGIC:
        raise ParseError(f"invalid magic number: {magic!r}", 0)

    # Check version
    version = int.from_bytes(reader.read_bytes(4), "little")
    if version != WASM_VERSION:
        raise ParseError(f"unsupported version: {version}", 4)

    module = WasmModule()

    # Parse sections
    while not reader.at_end:
        section_id = reader.read_byte()
        section_size = reader.read_u32_leb128()
        section_reader = reader.slice(section_size)

        try:
            section_type = SectionId(section_id)
        except ValueError:
            # Unknown section, skip it
            continue

        _parse_section(module, section_type, section_reader)

    return module


def _parse_section(
    module: WasmModule, section_id: SectionId, reader: BinaryReader
) -> None:
    """Parse a single section."""
    match section_id:
        case SectionId.CUSTOM:
            _parse_custom_section(module, reader)
        case SectionId.TYPE:
            _parse_type_section(module, reader)
        case SectionId.IMPORT:
            _parse_import_section(module, reader)
        case SectionId.FUNCTION:
            _parse_function_section(module, reader)
        case SectionId.TABLE:
            _parse_table_section(module, reader)
        case SectionId.MEMORY:
            _parse_memory_section(module, reader)
        case SectionId.GLOBAL:
            _parse_global_section(module, reader)
        case SectionId.EXPORT:
            _parse_export_section(module, reader)
        case SectionId.START:
            _parse_start_section(module, reader)
        case SectionId.ELEMENT:
            _parse_element_section(module, reader)
        case SectionId.CODE:
            _parse_code_section(module, reader)
        case SectionId.DATA:
            _parse_data_section(module, reader)
        case SectionId.DATA_COUNT:
            # Just validation, we don't need to store this
            _count = reader.read_u32_leb128()


def _parse_custom_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse custom section."""
    name = reader.read_name()
    data = reader.read_bytes(reader.remaining)
    module.custom[name] = data

    # Parse name section for debugging
    if name == "name":
        _parse_name_section(module, BinaryReader(data))


def _parse_name_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse the name custom section."""
    while not reader.at_end:
        subsection_id = reader.read_byte()
        subsection_size = reader.read_u32_leb128()
        subsection_data = reader.read_bytes(subsection_size)

        if subsection_id == 1:  # Function names
            sub_reader = BinaryReader(subsection_data)
            count = sub_reader.read_u32_leb128()
            for _ in range(count):
                func_idx = sub_reader.read_u32_leb128()
                func_name = sub_reader.read_name()
                module.function_names[func_idx] = func_name


def _parse_type_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse type section.

    Supports both WASM 1.0 function types and WASM GC composite types.
    """
    module.types = reader.read_vector(reader.read_composite_type)


def _parse_import_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse import section."""
    count = reader.read_u32_leb128()
    for _ in range(count):
        mod_name = reader.read_name()
        field_name = reader.read_name()
        kind = ImportKind(reader.read_byte())

        match kind:
            case ImportKind.FUNC:
                desc = reader.read_u32_leb128()  # type index
            case ImportKind.TABLE:
                desc = reader.read_table_type()
            case ImportKind.MEMORY:
                desc = reader.read_memory_type()
            case ImportKind.GLOBAL:
                desc = reader.read_global_type()

        module.imports.append(Import(mod_name, field_name, kind, desc))


def _parse_function_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse function section (type indices only)."""
    module.func_types = reader.read_vector(reader.read_u32_leb128)


def _parse_table_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse table section."""
    module.tables = reader.read_vector(reader.read_table_type)


def _parse_memory_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse memory section."""
    module.memories = reader.read_vector(reader.read_memory_type)


def _parse_global_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse global section."""
    count = reader.read_u32_leb128()
    for _ in range(count):
        global_type = reader.read_global_type()
        init_expr = _read_init_expr(reader)
        module.globals.append(Global(global_type, init_expr))


def _parse_export_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse export section."""
    count = reader.read_u32_leb128()
    for _ in range(count):
        name = reader.read_name()
        kind = ExportKind(reader.read_byte())
        index = reader.read_u32_leb128()
        module.exports.append(Export(name, kind, index))


def _parse_start_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse start section."""
    module.start = reader.read_u32_leb128()


def _parse_element_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse element section."""
    count = reader.read_u32_leb128()
    for _ in range(count):
        # Simplified: only handle basic active segments (flags=0)
        flags = reader.read_u32_leb128()
        if flags == 0:
            # Active segment, table 0
            offset_expr = _read_init_expr(reader)
            func_indices = reader.read_vector(reader.read_u32_leb128)
            module.elements.append(ElementSegment(0, offset_expr, func_indices))
        else:
            # Skip complex segment types for now
            raise ParseError(f"unsupported element segment flags: {flags}", reader.pos)


def _parse_code_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse code section."""
    count = reader.read_u32_leb128()
    for _ in range(count):
        body_size = reader.read_u32_leb128()
        body_reader = reader.slice(body_size)

        # Parse locals
        num_local_decls = body_reader.read_u32_leb128()
        locals_list = []
        for _ in range(num_local_decls):
            local_count = body_reader.read_u32_leb128()
            local_type = body_reader.read_value_type()
            locals_list.append((local_count, local_type))

        # Rest is code
        code = body_reader.read_bytes(body_reader.remaining)
        module.code.append(FunctionBody(locals_list, code))


def _parse_data_section(module: WasmModule, reader: BinaryReader) -> None:
    """Parse data section."""
    count = reader.read_u32_leb128()
    for _ in range(count):
        flags = reader.read_u32_leb128()
        if flags == 0:
            # Active segment, memory 0
            offset_expr = _read_init_expr(reader)
            data_len = reader.read_u32_leb128()
            data = reader.read_bytes(data_len)
            module.data.append(DataSegment(0, offset_expr, data))
        elif flags == 1:
            # Passive segment
            data_len = reader.read_u32_leb128()
            data = reader.read_bytes(data_len)
            module.data.append(DataSegment(-1, b"", data))  # -1 = passive
        elif flags == 2:
            # Active segment with memory index
            memory_idx = reader.read_u32_leb128()
            offset_expr = _read_init_expr(reader)
            data_len = reader.read_u32_leb128()
            data = reader.read_bytes(data_len)
            module.data.append(DataSegment(memory_idx, offset_expr, data))
        else:
            raise ParseError(f"unsupported data segment flags: {flags}", reader.pos)


def _read_init_expr(reader: BinaryReader) -> bytes:
    """Read an initialization expression (ends with 0x0B)."""
    start = reader.pos
    depth = 1
    while depth > 0:
        opcode = reader.read_byte()
        if opcode == 0x0B:  # end
            depth -= 1
        elif opcode in (0x02, 0x03, 0x04):  # block, loop, if
            reader.read_block_type()
            depth += 1
        elif opcode in (0x41, 0x42):  # i32.const, i64.const
            reader.read_s64_leb128()
        elif opcode == 0x43:  # f32.const
            reader.read_f32()
        elif opcode == 0x44:  # f64.const
            reader.read_f64()
        elif opcode == 0x23:  # global.get
            reader.read_u32_leb128()
        elif opcode == 0xD0:  # ref.null
            reader.read_byte()  # reftype
        elif opcode == 0xD2:  # ref.func
            reader.read_u32_leb128()
        # Other opcodes in init expressions are not common
    end = reader.pos
    # Return the expression bytes
    return reader.data[start:end]
