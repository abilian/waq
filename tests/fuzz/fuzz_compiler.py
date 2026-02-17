#!/usr/bin/env python3
"""Fuzzing target for WASM compiler.

This script fuzzes the WASM compiler by:
1. Parsing random bytes as WASM
2. If parsing succeeds, compiling the module

It should not crash or hang on any valid parsed input.

Usage:
    # Run with Atheris
    pip install atheris
    python tests/fuzz/fuzz_compiler.py

    # Or with a corpus
    python tests/fuzz/fuzz_compiler.py corpus/

    # Or with a specific input
    python tests/fuzz/fuzz_compiler.py -atheris_runs=0 path/to/input.wasm
"""

from __future__ import annotations

import sys


def fuzz_compiler(data: bytes) -> None:
    """Fuzz target: parse and compile arbitrary bytes.

    Should never crash - all invalid inputs should raise clean errors.
    """
    from waq.compiler import compile_module
    from waq.errors import CompileError, ParseError, ValidationError, WasmError
    from waq.parser.module import parse_module

    try:
        # First parse
        module = parse_module(data)

        # Then compile
        compile_module(module)

    except (ParseError, ValidationError, CompileError, WasmError):
        # Expected - invalid input should raise clean errors
        pass
    except ValueError:
        # Also acceptable for invalid data
        pass
    except MemoryError:
        # Acceptable if limits are hit
        pass


def main() -> None:
    """Run the fuzzer."""
    try:
        import atheris
    except ImportError:
        print("Atheris not installed. Install with: pip install atheris")
        print(
            "Or run with: uv add --dev atheris && uv run python tests/fuzz/fuzz_compiler.py"
        )
        sys.exit(1)

    atheris.Setup(sys.argv, fuzz_compiler)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
