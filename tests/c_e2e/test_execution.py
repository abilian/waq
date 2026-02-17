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

/* Declare the generated init function */
extern void __wasm_memory_init(void);

int main(void) {
    __wasm_init(1);
    __wasm_memory_init();
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


def mangle_export_name(name: str) -> str:
    """Mangle an export name to match compiler output."""
    if name == "_start" or name.startswith(("wasm_", "__wasm_")):
        return name
    return f"wasm_{name}"


def compile_and_run_with_imports(
    wat_file: Path, env_c_code: str, entry_func: str, expected_result: int | None = None
) -> int:
    """Compile a WAT file with C-provided imports and run it.

    Args:
        wat_file: Path to WAT file
        env_c_code: C code that provides imported functions
        entry_func: Name of the exported function to call (will be mangled)
        expected_result: Expected return value

    Returns the exit code of the program.
    """
    # Mangle the entry function name to match compiler output
    entry_func = mangle_export_name(entry_func)
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

        # Step 4: Create env.c with imported functions
        env_c = tmpdir / "env.c"
        env_c.write_text(env_c_code)

        # Step 5: Create main.c wrapper
        main_c = tmpdir / "main.c"
        main_c.write_text(f"""
#include <stdio.h>
#include <stdlib.h>
#include "wasm_runtime.h"

extern int {entry_func}(void);
extern void __wasm_memory_init(void);

int main(void) {{
    __wasm_init(1);
    __wasm_memory_init();
    int result = {entry_func}();
    __wasm_fini();
    return result;
}}
""")

        # Step 6: Compile and link
        runtime_obj = build_runtime()
        exe_file = tmpdir / "program"

        result = subprocess.run(
            [
                "clang",
                "-o",
                str(exe_file),
                str(main_c),
                str(env_c),
                str(asm_file),
                str(runtime_obj),
                f"-I{RUNTIME_DIR}",
                "-lm",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"clang linking failed: {result.stderr}")

        # Step 7: Run the program
        result = subprocess.run([str(exe_file)], capture_output=True, text=True)

        if expected_result is not None:
            assert result.returncode == expected_result, (
                f"Expected {expected_result}, got {result.returncode}"
            )

        return result.returncode


class TestImports:
    """Import tests."""

    def test_import_function(self):
        """Test calling an imported function: add_numbers(30, 12) = 42."""
        wat_file = FIXTURES_DIR / "import.wat"

        env_code = """
#include <stdint.h>

int32_t add_numbers(int32_t a, int32_t b) {
    return a + b;
}
"""
        compile_and_run_with_imports(
            wat_file, env_code, "test_import", expected_result=42
        )


class TestStartSection:
    """Start section tests."""

    def test_start_function(self):
        """Test that start function runs before main.

        The start function increments a global counter by 10.
        get_counter returns the counter, which should be 10.
        """
        wat_file = FIXTURES_DIR / "start.wat"
        compile_and_run(wat_file, expected_result=10)


class TestMultiValue:
    """Multi-value return tests."""

    def test_multi_value_function(self):
        """Test function returning multiple values.

        add_and_mul(3, 4) returns (7, 12).
        wasm_main returns 7 + 12 = 19.
        """
        wat_file = FIXTURES_DIR / "multi_value.wat"
        compile_and_run(wat_file, expected_result=19)

    def test_multi_value_block(self):
        """Test block returning multiple values.

        Block returns (5, 7).
        wasm_main returns 5 + 7 = 12.
        """
        wat_file = FIXTURES_DIR / "multi_value_block.wat"
        compile_and_run(wat_file, expected_result=12)
