"""Command-line interface for the WASM-to-QBE compiler."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from waq.compiler import compile_module
from waq.errors import CompileError, ParseError, ValidationError
from waq.parser.module import parse_module
from waq.runtime import RUNTIME_C_SOURCE


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
        help="Output file (default: input with appropriate extension)",
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
        choices=["qbe", "asm", "obj", "exe"],
        default="qbe",
        help="Output format (default: qbe)",
    )

    parser.add_argument(
        "--entry",
        default="wasm_main",
        help="Entry function name for exe output (default: wasm_main)",
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

    # Determine output file with appropriate extension
    if args.output is None:
        ext_map = {"qbe": ".ssa", "asm": ".s", "obj": ".o", "exe": ""}
        args.output = args.input.with_suffix(ext_map[args.emit])

    try:
        # Read input
        if args.verbose:
            print(f"Reading {args.input}")

        if args.input.suffix == ".wat":
            if args.verbose:
                print("Detected .wat file, converting to WASM format")
            wasm_bytes = convert_wat_to_wasm(args.input.read_text())
        else:
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
        elif args.emit == "asm":
            qbe_il = qbe_module.emit()
            asm_code = run_qbe(qbe_il, args.target, args.verbose)
            args.output.write_text(asm_code)
        elif args.emit == "obj":
            qbe_il = qbe_module.emit()
            asm_code = run_qbe(qbe_il, args.target, args.verbose)
            obj_bytes = run_assembler(asm_code, args.target, args.verbose)
            args.output.write_bytes(obj_bytes)
        elif args.emit == "exe":
            qbe_il = qbe_module.emit()
            asm_code = run_qbe(qbe_il, args.target, args.verbose)
            obj_bytes = run_assembler(asm_code, args.target, args.verbose)
            link_executable(
                obj_bytes, args.output, args.entry, args.target, args.verbose
            )

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


def run_qbe(qbe_il: str, target: str, verbose: bool = False) -> str:
    """Run QBE to convert QBE IL to assembly."""
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".ssa", mode="w", delete=False
        ) as temp_ssa:
            temp_ssa.write(qbe_il)
            temp_ssa_path = temp_ssa.name

        try:
            if verbose:
                print(f"Running QBE with target {target}")

            result = subprocess.run(
                ["qbe", "-t", target, temp_ssa_path],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout

        finally:
            Path(temp_ssa_path).unlink(missing_ok=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"QBE compilation failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "QBE not found. Please ensure QBE is installed and in your PATH."
        ) from e


def run_assembler(asm_code: str, target: str, verbose: bool = False) -> bytes:
    """Run the assembler to convert assembly to object file."""
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".s", mode="w", delete=False
        ) as temp_asm:
            temp_asm.write(asm_code)
            temp_asm_path = temp_asm.name

        with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as temp_obj:
            temp_obj_path = temp_obj.name

        try:
            if verbose:
                print("Running assembler")

            # Determine assembler based on target
            if "apple" in target:
                # Use clang on macOS for better compatibility
                cmd = [
                    "clang",
                    "-c",
                    "-x",
                    "assembler",
                    temp_asm_path,
                    "-o",
                    temp_obj_path,
                ]
            else:
                # Use as on Linux/other
                cmd = ["as", temp_asm_path, "-o", temp_obj_path]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return Path(temp_obj_path).read_bytes()

        finally:
            Path(temp_asm_path).unlink(missing_ok=True)
            Path(temp_obj_path).unlink(missing_ok=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Assembly failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "Assembler not found. Please ensure 'as' or 'clang' is installed."
        ) from e


def generate_main_stub(entry_function: str) -> str:
    """Generate a C main() stub that calls the WASM entry function."""
    # Use the plain function name - C compiler handles mangling
    return f"""\
/* Generated main stub for WAQ */
#include <stdio.h>

extern int {entry_function}(void);

int main(void) {{
    int result = {entry_function}();
    printf("%d\\n", result);
    return 0;
}}
"""


def link_executable(
    obj_bytes: bytes,
    output_path: Path,
    entry_function: str,
    target: str,
    verbose: bool = False,
) -> None:
    """Link object file with runtime to create executable."""
    try:
        # Write the object file to a temp location
        with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as temp_obj:
            temp_obj.write(obj_bytes)
            temp_obj_path = temp_obj.name

        # Generate and write the main stub
        main_stub = generate_main_stub(entry_function)
        with tempfile.NamedTemporaryFile(
            suffix=".c", mode="w", delete=False
        ) as temp_main:
            temp_main.write(main_stub)
            temp_main_path = temp_main.name

        try:
            if verbose:
                print(f"Linking executable with entry function: {entry_function}")

            # Compile and link everything together
            if "apple" in target:
                cmd = [
                    "clang",
                    "-o",
                    str(output_path),
                    temp_obj_path,
                    temp_main_path,
                    str(RUNTIME_C_SOURCE),
                    "-lm",  # Link math library
                ]
            else:
                cmd = [
                    "gcc",
                    "-o",
                    str(output_path),
                    temp_obj_path,
                    temp_main_path,
                    str(RUNTIME_C_SOURCE),
                    "-lm",
                ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

        finally:
            Path(temp_obj_path).unlink(missing_ok=True)
            Path(temp_main_path).unlink(missing_ok=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Linking failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "Compiler not found. Please ensure 'clang' or 'gcc' is installed."
        ) from e


def convert_wat_to_wasm(wat_content: str) -> bytes:
    """Convert WAT text format to WASM binary format using wat2wasm."""
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wat", mode="w", delete=False
        ) as temp_wat:
            temp_wat.write(wat_content)
            temp_wat_path = temp_wat.name

        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as temp_wasm:
            temp_wasm_path = temp_wasm.name

        try:
            # Convert WAT to WASM
            result = subprocess.run(
                ["wat2wasm", temp_wat_path, "-o", temp_wasm_path],
                capture_output=True,
                text=True,
                check=True,
            )

            # Read the resulting WASM binary
            wasm_bytes = Path(temp_wasm_path).read_bytes()
            return wasm_bytes

        finally:
            # Clean up temporary files
            Path(temp_wat_path).unlink(missing_ok=True)
            Path(temp_wasm_path).unlink(missing_ok=True)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(
            "Failed to convert WAT to WASM. "
            "Ensure wat2wasm is installed (part of WebAssembly binary toolkit). "
            f"Error: {e}"
        )


if __name__ == "__main__":
    sys.exit(main())
