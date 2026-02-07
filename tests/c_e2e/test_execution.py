"""End-to-end execution tests.

These tests compile WAT programs to native executables and run them,
verifying the output is correct.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from waq.cli import main as waq_main

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
RUNTIME_DIR = PROJECT_ROOT / "runtime"


def check_tools_available():
    """Check if required tools are available."""
    tools = ["wat2wasm", "qbe", "clang"]
    missing = []
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=False)
        except FileNotFoundError:
            missing.append(tool)
    return missing


# Skip all tests if tools are missing
missing_tools = check_tools_available()
pytestmark = pytest.mark.skipif(
    len(missing_tools) > 0, reason=f"Missing required tools: {', '.join(missing_tools)}"
)


def build_runtime():
    """Build the runtime library if needed."""
    runtime_obj = RUNTIME_DIR / "wasm_runtime.o"
    runtime_c = RUNTIME_DIR / "wasm_runtime.c"
    runtime_h = RUNTIME_DIR / "wasm_runtime.h"

    # Check if rebuild needed
    if runtime_obj.exists():
        obj_mtime = runtime_obj.stat().st_mtime
        if (
            runtime_c.stat().st_mtime < obj_mtime
            and runtime_h.stat().st_mtime < obj_mtime
        ):
            return runtime_obj

    # Build runtime
    result = subprocess.run(
        ["make", "-C", str(RUNTIME_DIR)], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to build runtime: {result.stderr}")

    return runtime_obj


def compile_and_run(wat_file: Path, expected_result: int | None = None) -> int:
    """Compile a WAT file to an executable and run it.

    Returns the exit code of the program.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: WAT -> WASM (using wat2wasm)
        wasm_file = tmpdir / "program.wasm"
        result = subprocess.run(
            ["wat2wasm", str(wat_file), "-o", str(wasm_file)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"wat2wasm failed: {result.stderr}")

        # Step 2: WASM -> QBE IL (using waq)
        ssa_file = tmpdir / "program.ssa"
        exit_code = waq_main([str(wasm_file), "-o", str(ssa_file)])
        if exit_code != 0:
            raise RuntimeError("waq compilation failed")

        # Step 3: QBE IL -> Assembly (using qbe)
        asm_file = tmpdir / "program.s"
        result = subprocess.run(
            ["qbe", "-o", str(asm_file), str(ssa_file)], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"qbe failed: {result.stderr}")

        # Step 4: Create main.c wrapper
        # Note: The WASM exports a function called 'main' which becomes
        # the C symbol 'main'. We need to rename our C main to call it.
        main_c = tmpdir / "main.c"
        main_c.write_text("""
#include <stdio.h>
#include <stdlib.h>
#include "wasm_runtime.h"

/* Declare the exported WASM function (exported as "main" in WAT) */
extern int wasm_main(void);

int main(void) {
    __wasm_init(1);
    int result = wasm_main();
    __wasm_fini();
    return result;
}
""")

        # Step 5: Compile and link
        runtime_obj = build_runtime()
        exe_file = tmpdir / "program"

        result = subprocess.run(
            [
                "clang",
                "-o",
                str(exe_file),
                str(main_c),
                str(asm_file),
                str(runtime_obj),
                f"-I{RUNTIME_DIR}",
                "-lm",  # Math library
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"clang linking failed: {result.stderr}")

        # Step 6: Run the program
        result = subprocess.run([str(exe_file)], capture_output=True, text=True)

        if expected_result is not None:
            assert result.returncode == expected_result, (
                f"Expected {expected_result}, got {result.returncode}"
            )

        return result.returncode


class TestBasicExecution:
    """Basic execution tests."""

    def test_return_42(self):
        """Test returning a constant."""
        wat_file = FIXTURES_DIR / "return_42.wat"
        compile_and_run(wat_file, expected_result=42)

    def test_add(self):
        """Test addition."""
        wat_file = FIXTURES_DIR / "add.wat"
        compile_and_run(wat_file, expected_result=42)

    def test_locals(self):
        """Test local variables."""
        wat_file = FIXTURES_DIR / "locals.wat"
        compile_and_run(wat_file, expected_result=30)


class TestControlFlow:
    """Control flow tests."""

    def test_loop(self):
        """Test loop: sum 1 to 10 = 55."""
        wat_file = FIXTURES_DIR / "loop.wat"
        compile_and_run(wat_file, expected_result=55)


class TestRecursion:
    """Recursive function tests."""

    def test_factorial(self):
        """Test factorial(6) = 720. Returns 720 mod 256 = 208."""
        wat_file = FIXTURES_DIR / "factorial.wat"
        # Exit codes are 8-bit, so 720 % 256 = 208
        compile_and_run(wat_file, expected_result=720 % 256)

    def test_fibonacci(self):
        """Test fib(10) = 55."""
        wat_file = FIXTURES_DIR / "fibonacci.wat"
        compile_and_run(wat_file, expected_result=55)


class TestMemory:
    """Memory operation tests."""

    def test_memory_store_load(self):
        """Test memory store and load: 42 + 58 = 100."""
        wat_file = FIXTURES_DIR / "memory.wat"
        compile_and_run(wat_file, expected_result=100)


class TestGlobals:
    """Global variable tests."""

    def test_global_counter(self):
        """Test global counter increment."""
        wat_file = FIXTURES_DIR / "global.wat"
        compile_and_run(wat_file, expected_result=4)
