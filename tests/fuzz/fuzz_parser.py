#!/usr/bin/env python3
"""Fuzzing target for WASM parser.

This script fuzzes the WASM binary parser with random bytes.
It should not crash or hang on any input.

Usage:
    # Run with Atheris
    pip install atheris
    python tests/fuzz/fuzz_parser.py

    # Or with a corpus
    python tests/fuzz/fuzz_parser.py corpus/

    # Or with a specific input
    python tests/fuzz/fuzz_parser.py -atheris_runs=0 path/to/input.wasm
"""

from __future__ import annotations

import sys


def fuzz_parser(data: bytes) -> None:
    """Fuzz target: parse arbitrary bytes as WASM.

    Should never crash - all invalid inputs should raise ParseError or similar.
    """
    from waq.errors import ParseError, ValidationError, WasmError
    from waq.parser.module import parse_module

    try:
        parse_module(data)
    except (ParseError, ValidationError, WasmError):
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
        print("Or run with: uv add --dev atheris && uv run python tests/fuzz/fuzz_parser.py")
        sys.exit(1)

    atheris.Setup(sys.argv, fuzz_parser)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
