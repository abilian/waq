# Polyglot Test Programs

This directory contains test programs in various languages that compile to WebAssembly.
These programs are used to verify that waq produces the same results as a reference
WASM runtime (Node.js).

## Directory Structure

```
programs/
├── pure/               # Pure WASM (no WASI dependencies)
│   ├── c/
│   ├── rust/
│   └── zig/
└── wasi/               # WASI programs
    ├── c/
    ├── rust/
    └── zig/
```

## Test Categories

### Pure WASM

Programs that export a `main` function returning an i32. No system calls needed.
The return value (mod 256) is used as the exit code.

### WASI Programs

Programs that use WASI for process exit and standard I/O.

## Adding New Test Programs

1. Create the source file in the appropriate directory
2. Add an entry to `PURE_WASM_TESTS` or `WASI_TESTS` in `test_polyglot.py`

## Running Tests

```bash
# Run all polyglot tests
uv run pytest tests/d_polyglot/ -v

# Run only Zig tests
uv run pytest tests/d_polyglot/ -v -k zig
```
