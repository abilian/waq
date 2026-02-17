"""Command-line interface for the WASM-to-QBE compiler."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

from waq.compiler import compile_module
from waq.errors import CompileError, ParseError, ValidationError
from waq.parser.module import parse_module
from waq.runtime import RUNTIME_C_SOURCE


def detect_target() -> str:
    """Auto-detect the QBE target for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        # macOS
        if machine in ("arm64", "aarch64"):
            return "arm64_apple"
        return "amd64_apple"
    if system == "linux":
        if machine in ("arm64", "aarch64"):
            return "arm64"
        if machine in ("riscv64",):
            return "rv64"
        return "amd64_sysv"
    # Default to System V ABI for unknown systems
    return "amd64_sysv"


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

    default_target = detect_target()
    parser.add_argument(
        "-t",
        "--target",
        choices=["amd64_sysv", "amd64_apple", "arm64", "arm64_apple", "rv64"],
        default=default_target,
        help=f"Target architecture (default: {default_target})",
    )

    parser.add_argument(
        "--emit",
        choices=["qbe", "asm", "obj", "exe"],
        default="qbe",
        help="Output format (default: qbe)",
    )

    parser.add_argument(
        "--entry",
        default="main",
        help="Entry function name for exe output (default: main)",
    )

    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Don't print result in exe output (for void functions)",
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
        version="waq 0.1.1",
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
                obj_bytes,
                args.output,
                args.entry,
                args.target,
                args.verbose,
                print_result=not args.no_print,
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
    """Run QBE to convert QBE IL to assembly.

    Uses TemporaryDirectory for reliable cleanup even on process termination.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="waq_") as tmpdir:
            temp_ssa_path = Path(tmpdir) / "input.ssa"
            temp_ssa_path.write_text(qbe_il, encoding="utf-8")

            if verbose:
                print(f"Running QBE with target {target}")

            result = subprocess.run(
                ["qbe", "-t", target, str(temp_ssa_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"QBE compilation failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "QBE not found. Please ensure QBE is installed and in your PATH."
        ) from e


def run_assembler(asm_code: str, target: str, verbose: bool = False) -> bytes:
    """Run the assembler to convert assembly to object file.

    Uses TemporaryDirectory for reliable cleanup even on process termination.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="waq_") as tmpdir:
            temp_asm_path = Path(tmpdir) / "input.s"
            temp_obj_path = Path(tmpdir) / "output.o"

            temp_asm_path.write_text(asm_code, encoding="utf-8")

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
                    str(temp_asm_path),
                    "-o",
                    str(temp_obj_path),
                ]
            else:
                # Use as on Linux/other
                cmd = ["as", str(temp_asm_path), "-o", str(temp_obj_path)]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return temp_obj_path.read_bytes()

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Assembly failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "Assembler not found. Please ensure 'as' or 'clang' is installed."
        ) from e


def mangle_export_name(name: str) -> str:
    """Get the native symbol name for a WASM export.

    WASM exports are prefixed with wasm_ to avoid conflicts with C symbols,
    except for _start which is the WASI entry point, and names already
    prefixed with wasm_ or __wasm_ to avoid double-prefixing.
    """
    if name == "_start" or name.startswith(("wasm_", "__wasm_")):
        return name
    return f"wasm_{name}"


def generate_main_stub(entry_function: str, *, print_result: bool = True) -> str:
    """Generate a C main() stub that calls the WASM entry function.

    The entry_function should be the WASM export name; it will be mangled
    to match the compiled symbol name.
    """
    # Apply name mangling to match compiled output
    native_name = mangle_export_name(entry_function)
    if print_result:
        return f"""\
/* Generated main stub for WAQ */
#include <stdio.h>

extern void __wasm_memory_init(void);
extern int {native_name}(void);

int main(void) {{
    __wasm_memory_init();
    int result = {native_name}();
    printf("%d\\n", result);
    return 0;
}}
"""
    return f"""\
/* Generated main stub for WAQ */

extern void __wasm_memory_init(void);
extern int {native_name}(void);

int main(void) {{
    __wasm_memory_init();
    return {native_name}();
}}
"""


def link_executable(
    obj_bytes: bytes,
    output_path: Path,
    entry_function: str,
    target: str,
    verbose: bool = False,
    *,
    print_result: bool = True,
) -> None:
    """Link object file with runtime to create executable.

    Uses TemporaryDirectory for reliable cleanup even on process termination.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="waq_") as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write the object file
            temp_obj_path = tmpdir_path / "module.o"
            temp_obj_path.write_bytes(obj_bytes)

            # Generate and write the main stub
            main_stub = generate_main_stub(entry_function, print_result=print_result)
            temp_main_path = tmpdir_path / "main.c"
            temp_main_path.write_text(main_stub, encoding="utf-8")

            if verbose:
                print(f"Linking executable with entry function: {entry_function}")

            # Compile and link everything together
            if "apple" in target:
                cmd = [
                    "clang",
                    "-o",
                    str(output_path),
                    str(temp_obj_path),
                    str(temp_main_path),
                    str(RUNTIME_C_SOURCE),
                    "-lm",  # Link math library
                ]
            else:
                cmd = [
                    "gcc",
                    "-o",
                    str(output_path),
                    str(temp_obj_path),
                    str(temp_main_path),
                    str(RUNTIME_C_SOURCE),
                    "-lm",
                ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Linking failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "Compiler not found. Please ensure 'clang' or 'gcc' is installed."
        ) from e


def convert_wat_to_wasm(wat_content: str) -> bytes:
    """Convert WAT text format to WASM binary format using wat2wasm.

    Uses TemporaryDirectory for reliable cleanup even on process termination.
    """
    try:
        with tempfile.TemporaryDirectory(prefix="waq_") as tmpdir:
            tmpdir_path = Path(tmpdir)

            temp_wat_path = tmpdir_path / "input.wat"
            temp_wasm_path = tmpdir_path / "output.wasm"

            temp_wat_path.write_text(wat_content, encoding="utf-8")

            # Convert WAT to WASM
            subprocess.run(
                ["wat2wasm", str(temp_wat_path), "-o", str(temp_wasm_path)],
                capture_output=True,
                text=True,
                check=True,
            )

            # Read the resulting WASM binary
            return temp_wasm_path.read_bytes()

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(
            "Failed to convert WAT to WASM. "
            "Ensure wat2wasm is installed (part of WebAssembly binary toolkit). "
            f"Error: {e}"
        ) from e


if __name__ == "__main__":
    sys.exit(main())
