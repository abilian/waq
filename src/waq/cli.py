"""Command-line interface for the WASM-to-QBE compiler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from waq.compiler import compile_module
from waq.errors import CompileError, ParseError, ValidationError
from waq.parser.module import parse_module


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="waq",
        description="Compile WebAssembly to native code via QBE",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input WASM file",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file (default: input with .ssa extension)",
    )

    parser.add_argument(
        "-t",
        "--target",
        choices=["amd64_sysv", "amd64_apple", "arm64", "arm64_apple", "rv64"],
        default="amd64_sysv",
        help="Target architecture (default: amd64_sysv)",
    )

    parser.add_argument(
        "--emit",
        choices=["qbe", "asm", "obj"],
        default="qbe",
        help="Output format (default: qbe)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="waq 0.1.0",
    )

    args = parser.parse_args(argv)

    # Determine output file
    if args.output is None:
        args.output = args.input.with_suffix(".ssa")

    try:
        # Read input
        if args.verbose:
            print(f"Reading {args.input}")
        wasm_bytes = args.input.read_bytes()

        # Parse
        if args.verbose:
            print("Parsing WASM module")
        wasm_module = parse_module(wasm_bytes)

        if args.verbose:
            print(f"  Types: {len(wasm_module.types)}")
            print(f"  Functions: {len(wasm_module.func_types)}")
            print(f"  Exports: {len(wasm_module.exports)}")

        # Compile
        if args.verbose:
            print("Compiling to QBE IL")
        qbe_module = compile_module(wasm_module, target=args.target)

        # Write output
        if args.verbose:
            print(f"Writing {args.output}")

        if args.emit == "qbe":
            output_text = qbe_module.emit()
            args.output.write_text(output_text)
        else:
            # TODO: Invoke QBE for asm/obj output
            print(f"Output format '{args.emit}' not yet implemented", file=sys.stderr)
            return 1

        if args.verbose:
            print("Done")

        return 0

    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 1
    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    except CompileError as e:
        print(f"Compile error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback  # noqa: PLC0415

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
