# WAQ - WebAssembly to QBE Compiler

WAQ is an ahead-of-time (AOT) compiler that translates WebAssembly binary modules into native machine code using QBE as the backend.

## Features

- **WASM Binary Parsing**: Parse WebAssembly binary modules
- **Stack-to-SSA Translation**: Convert WebAssembly's stack-based model to QBE's SSA form
- **Control Flow Conversion**: Transform structured control flow (blocks, loops, ifs) to basic blocks and jumps
- **Type Mapping**: Map WASM types (i32, i64, f32, f64) to QBE types (w, l, s, d)
- **QBE Backend**: Generate QBE intermediate language code

## Installation

```bash
# Clone the repository
# (not yet) git clone https://github.com/abilian/waq.git
git clone https://git.sr.ht/~sfermigier/waq
cd waq

# Install dependencies using uv
uv sync
```

### External Dependencies

WAQ requires the following external tools depending on output format:

| Output | Required Tools |
|--------|----------------|
| `--emit qbe` | None |
| `--emit asm` | [QBE](https://c9x.me/compile/) |
| `--emit obj` | QBE + assembler (clang/as) |
| `--emit exe` | QBE + C compiler (clang/gcc) |
| `.wat` input | [wabt](https://github.com/WebAssembly/wabt) (wat2wasm) |

## Usage

### Basic Compilation

```bash
# Compile a WASM file to QBE IL
waq input.wasm -o output.ssa

# Compile a WAT file (automatically converted via wat2wasm)
waq input.wat -o output.ssa

# Compile to assembly
waq input.wasm --emit asm -o output.s

# Compile to object file
waq input.wasm --emit obj -o output.o

# Compile to executable (requires exported wasm_main function)
waq input.wasm --emit exe -o program

# Specify a different entry function
waq input.wasm --emit exe --entry my_main -o program

# For void functions, use --no-print
waq input.wasm --emit exe --entry void_func --no-print -o program

# Target a specific architecture
waq input.wasm --emit exe -t arm64_apple -o program
```

### Supported Targets

- `amd64_sysv` - x86-64 Linux/BSD (default)
- `amd64_apple` - x86-64 macOS
- `arm64` - ARM64 Linux
- `arm64_apple` - ARM64 macOS (Apple Silicon)
- `rv64` - RISC-V 64-bit

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
uv run pytest -m unit              # Unit tests only
uv run pytest -m integration       # Integration tests only
uv run pytest -m e2e               # End-to-end tests only
```

### Development Commands

```bash
# Format code
make format

# Lint and type check
make lint

# Run with coverage
make test-cov

# Multi-version testing via nox
nox -s tests              # Run tests on all Python versions
nox -s check              # Run linting/type checking
```

## Project Structure

```
waq/
├── src/
│   └── waq/              # Main source code
│       ├── compiler/     # Compilation logic
│       ├── parser/       # WASM binary parsing
│       ├── runtime/      # Runtime support
│       └── cli.py        # Command-line interface
├── tests/                # Test suite
│   ├── a_unit/           # Unit tests
│   ├── b_integration/    # Integration tests
│   └── c_e2e/            # End-to-end tests
├── notes/                # Technical notes (no documentation yet)
└── runtime/              # Runtime components
```

## Testing

The project follows a pyramid testing structure:

- **Unit Tests**: Fast, isolated tests in `tests/a_unit/`
- **Integration Tests**: Component interaction tests in `tests/b_integration/`
- **End-to-end Tests**: Full workflow tests in `tests/c_e2e/`

## Code Style

- Targets Python 3.12+
- Uses Ruff with ALL rules enabled
- Multiple type checkers: ty, pyrefly, mypy
- All files must have `from __future__ import annotations`

## License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

## Contributing

See CONTRIBUTING.md for contribution guidelines.
