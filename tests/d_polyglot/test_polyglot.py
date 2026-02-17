"""Polyglot WASM tests.

Tests that programs compiled from various languages produce the same
results when executed via Node.js (reference) and waq (our compiler).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    PROGRAMS_DIR,
    compile_to_wasm,
    detect_compiler,
    detect_nodejs,
    detect_waq,
    run_with_nodejs_pure,
    run_with_nodejs_wasi,
    run_with_waq_pure,
    run_with_waq_wasi,
)

# QBE has a 63-character identifier length limit. Rust generates longer mangled names.
_QBE_ID_LIMIT = pytest.mark.xfail(
    reason="QBE identifier length limit exceeded by Rust mangled names",
    strict=False,
)

# Test program definitions: (language, program_name, expected_exit_code)
PURE_WASM_TESTS = [
    # Basic tests
    ("c", "return_42", 42),
    ("c", "factorial", 208),  # factorial(6) % 256 = 720 % 256 = 208
    ("rust", "return_42", 42),
    ("rust", "factorial", 208),
    ("zig", "return_42", 42),
    ("zig", "factorial", 208),
    # Fibonacci: tests loops, local variables
    ("c", "fibonacci", 109),  # fibonacci(20) % 256 = 6765 % 256 = 109
    ("rust", "fibonacci", 109),
    ("zig", "fibonacci", 109),
    # GCD: tests loops, conditionals, modulo
    ("c", "gcd", 27),  # gcd(48,18) + gcd(252,105) = 6 + 21 = 27
    ("rust", "gcd", 27),
    ("zig", "gcd", 27),
    # Primes: tests nested loops, conditionals
    ("c", "primes", 25),  # count of primes up to 100
    pytest.param("rust", "primes", 25, marks=_QBE_ID_LIMIT),
    ("zig", "primes", 25),
    # Collatz: tests loops, conditionals, 64-bit math
    ("c", "collatz", 111),  # collatz(27) has 111 steps
    ("rust", "collatz", 111),
    ("zig", "collatz", 111),
    # Bitops: tests and, or, xor, shifts
    ("c", "bitops", 249),  # checksum of various bit operations
    ("rust", "bitops", 249),
    ("zig", "bitops", 249),
]

WASI_TESTS = [
    ("c", "hello", 42),
    pytest.param("rust", "hello", 42, marks=_QBE_ID_LIMIT),
    ("zig", "hello", 42),
]


def get_source_path(mode: str, language: str, program: str) -> Path:
    """Get the source file path for a test program."""
    ext_map = {"c": ".c", "rust": ".rs", "zig": ".zig"}
    ext = ext_map.get(language)
    if ext is None:
        msg = f"Unknown language: {language}"
        raise ValueError(msg)
    return PROGRAMS_DIR / mode / language / f"{program}{ext}"


def skip_if_compiler_unavailable(language: str, mode: str) -> None:
    """Skip test if compiler is not available."""
    info = detect_compiler(language)
    if not info.available:
        pytest.skip(f"{language} compiler not available: {info.skip_reason}")
    if mode == "pure" and not info.pure_available:
        pytest.skip(f"{language} pure WASM support not available: {info.skip_reason}")
    if mode == "wasi" and not info.wasi_available:
        pytest.skip(f"{language} WASI support not available: {info.skip_reason}")


def skip_if_nodejs_unavailable() -> None:
    """Skip test if Node.js is not available."""
    available, _ = detect_nodejs()
    if not available:
        pytest.skip("Node.js not available")


def skip_if_waq_unavailable() -> None:
    """Skip test if waq is not available."""
    available, _ = detect_waq()
    if not available:
        pytest.skip("waq not available")


class TestPureWasm:
    """Tests for pure WASM programs (no WASI dependencies)."""

    @pytest.mark.parametrize(
        ("language", "program", "expected"),
        PURE_WASM_TESTS,
        ids=[f"{lang}-{prog}" for lang, prog, _ in PURE_WASM_TESTS],
    )
    @pytest.mark.pure_wasm
    def test_nodejs_execution(
        self, language: str, program: str, expected: int
    ) -> None:
        """Test that pure WASM runs correctly in Node.js."""
        skip_if_compiler_unavailable(language, "pure")
        skip_if_nodejs_unavailable()

        source = get_source_path("pure", language, program)
        wasm = compile_to_wasm(source, "pure")

        result = run_with_nodejs_pure(wasm, "main")
        assert result.exit_code == expected, (
            f"Expected exit code {expected}, got {result.exit_code}\n"
            f"stderr: {result.stderr}"
        )

    @pytest.mark.parametrize(
        ("language", "program", "expected"),
        PURE_WASM_TESTS,
        ids=[f"{lang}-{prog}" for lang, prog, _ in PURE_WASM_TESTS],
    )
    @pytest.mark.pure_wasm
    def test_waq_execution(
        self, language: str, program: str, expected: int, tmp_path: Path
    ) -> None:
        """Test that pure WASM runs correctly with waq."""
        skip_if_compiler_unavailable(language, "pure")
        skip_if_waq_unavailable()

        source = get_source_path("pure", language, program)
        wasm = compile_to_wasm(source, "pure")

        result = run_with_waq_pure(wasm, "main", tmp_path)
        assert result.exit_code == expected, (
            f"Expected exit code {expected}, got {result.exit_code}\n"
            f"stderr: {result.stderr}"
        )

    @pytest.mark.parametrize(
        ("language", "program", "expected"),
        PURE_WASM_TESTS,
        ids=[f"{lang}-{prog}" for lang, prog, _ in PURE_WASM_TESTS],
    )
    @pytest.mark.pure_wasm
    def test_nodejs_vs_waq(
        self, language: str, program: str, expected: int, tmp_path: Path
    ) -> None:
        """Test that Node.js and waq produce the same result."""
        skip_if_compiler_unavailable(language, "pure")
        skip_if_nodejs_unavailable()
        skip_if_waq_unavailable()

        source = get_source_path("pure", language, program)
        wasm = compile_to_wasm(source, "pure")

        node_result = run_with_nodejs_pure(wasm, "main")
        waq_result = run_with_waq_pure(wasm, "main", tmp_path)

        assert node_result.exit_code == waq_result.exit_code, (
            f"Exit codes differ: Node.js={node_result.exit_code}, "
            f"waq={waq_result.exit_code}\n"
            f"Node stderr: {node_result.stderr}\n"
            f"waq stderr: {waq_result.stderr}"
        )
        assert node_result.stdout == waq_result.stdout, (
            f"Stdout differs:\n"
            f"Node.js: {node_result.stdout!r}\n"
            f"waq: {waq_result.stdout!r}"
        )


class TestWasi:
    """Tests for WASI programs."""

    @pytest.mark.parametrize(
        ("language", "program", "expected"),
        WASI_TESTS,
        ids=[f"{lang}-{prog}" for lang, prog, _ in WASI_TESTS],
    )
    @pytest.mark.wasi
    def test_nodejs_execution(
        self, language: str, program: str, expected: int
    ) -> None:
        """Test that WASI WASM runs correctly in Node.js."""
        skip_if_compiler_unavailable(language, "wasi")
        skip_if_nodejs_unavailable()

        source = get_source_path("wasi", language, program)
        wasm = compile_to_wasm(source, "wasi")

        result = run_with_nodejs_wasi(wasm)
        assert result.exit_code == expected, (
            f"Expected exit code {expected}, got {result.exit_code}\n"
            f"stderr: {result.stderr}"
        )

    @pytest.mark.parametrize(
        ("language", "program", "expected"),
        WASI_TESTS,
        ids=[f"{lang}-{prog}" for lang, prog, _ in WASI_TESTS],
    )
    @pytest.mark.wasi
    def test_waq_execution(
        self, language: str, program: str, expected: int, tmp_path: Path
    ) -> None:
        """Test that WASI WASM runs correctly with waq."""
        skip_if_compiler_unavailable(language, "wasi")
        skip_if_waq_unavailable()

        source = get_source_path("wasi", language, program)
        wasm = compile_to_wasm(source, "wasi")

        result = run_with_waq_wasi(wasm, tmp_path)
        assert result.exit_code == expected, (
            f"Expected exit code {expected}, got {result.exit_code}\n"
            f"stderr: {result.stderr}"
        )

    @pytest.mark.parametrize(
        ("language", "program", "expected"),
        WASI_TESTS,
        ids=[f"{lang}-{prog}" for lang, prog, _ in WASI_TESTS],
    )
    @pytest.mark.wasi
    def test_nodejs_vs_waq(
        self, language: str, program: str, expected: int, tmp_path: Path
    ) -> None:
        """Test that Node.js and waq produce the same result for WASI."""
        skip_if_compiler_unavailable(language, "wasi")
        skip_if_nodejs_unavailable()
        skip_if_waq_unavailable()

        source = get_source_path("wasi", language, program)
        wasm = compile_to_wasm(source, "wasi")

        node_result = run_with_nodejs_wasi(wasm)
        waq_result = run_with_waq_wasi(wasm, tmp_path)

        assert node_result.exit_code == waq_result.exit_code, (
            f"Exit codes differ: Node.js={node_result.exit_code}, "
            f"waq={waq_result.exit_code}\n"
            f"Node stderr: {node_result.stderr}\n"
            f"waq stderr: {waq_result.stderr}"
        )
        assert node_result.stdout == waq_result.stdout, (
            f"Stdout differs:\n"
            f"Node.js: {node_result.stdout!r}\n"
            f"waq: {waq_result.stdout!r}"
        )


class TestCompilerDetection:
    """Tests for compiler detection functionality."""

    def test_detect_all_compilers(self) -> None:
        """Verify compiler detection runs without error."""
        for lang in ["c", "rust", "zig"]:
            info = detect_compiler(lang)
            assert info.name == lang

    def test_detect_nodejs(self) -> None:
        """Verify Node.js detection runs without error."""
        available, version = detect_nodejs()
        assert isinstance(available, bool)
        if available:
            assert version is not None

    def test_detect_waq(self) -> None:
        """Verify waq detection runs without error."""
        available, version = detect_waq()
        assert isinstance(available, bool)
        if available:
            assert version is not None
