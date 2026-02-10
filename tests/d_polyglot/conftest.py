"""Polyglot WASM test harness configuration.

This module provides fixtures for compiling source programs to WASM
and executing them with both Node.js (reference) and waq (our compiler).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

# Directories
POLYGLOT_DIR = Path(__file__).parent
PROGRAMS_DIR = POLYGLOT_DIR / "programs"
COMPILED_DIR = POLYGLOT_DIR / "compiled"
NODE_RUNNER = POLYGLOT_DIR / "run_wasm.mjs"


@dataclass
class ExecutionResult:
    """Result of executing a WASM program."""

    exit_code: int
    stdout: str
    stderr: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExecutionResult):
            return NotImplemented
        return (
            self.exit_code == other.exit_code
            and self.stdout == other.stdout
            # Don't compare stderr for equality (may have debug info)
        )


@dataclass
class CompilerInfo:
    """Information about a language compiler."""

    name: str
    available: bool
    version: str | None
    pure_available: bool  # Can compile to pure WASM (no WASI)
    wasi_available: bool  # Can compile to WASI WASM
    skip_reason: str | None = None


# Compiler detection cache
_compiler_cache: dict[str, CompilerInfo] = {}


def run_command(
    cmd: list[str], *, check: bool = True, timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def get_rustc_targets() -> set[str]:
    """Get available rustc targets."""
    try:
        result = run_command(["rustc", "--print", "target-list"], check=False)
        if result.returncode == 0:
            return set(result.stdout.strip().split("\n"))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return set()


def get_rustc_installed_targets() -> set[str]:
    """Get installed rustc targets (not just available ones)."""
    try:
        result = run_command(["rustup", "target", "list", "--installed"], check=False)
        if result.returncode == 0:
            return set(result.stdout.strip().split("\n"))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # Fall back to checking if the target is in available list
    return get_rustc_targets()


def check_clang_wasm32() -> bool:
    """Check if clang can compile to wasm32 (pure WASM)."""
    try:
        result = run_command(
            ["clang", "--target=wasm32", "--print-supported-cpus"],
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False


def check_clang_wasi() -> bool:
    """Check if clang can compile to wasm32-wasi."""
    if shutil.which("wasm32-wasi-clang"):
        return True

    try:
        result = run_command(
            ["clang", "--target=wasm32-wasi", "--print-sysroot"],
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            sysroot = Path(result.stdout.strip())
            if sysroot.exists():
                return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False


def detect_c_compiler() -> CompilerInfo:
    """Detect C compiler availability."""
    if "c" in _compiler_cache:
        return _compiler_cache["c"]

    try:
        result = run_command(["clang", "--version"], check=False)
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            pure_ok = check_clang_wasm32()
            wasi_ok = check_clang_wasi()
            skip_reasons = []
            if not pure_ok:
                skip_reasons.append("wasm32 target not available")
            if not wasi_ok:
                skip_reasons.append("wasi-sdk not installed")
            info = CompilerInfo(
                name="c",
                available=True,
                version=version,
                pure_available=pure_ok,
                wasi_available=wasi_ok,
                skip_reason="; ".join(skip_reasons) if skip_reasons else None,
            )
        else:
            info = CompilerInfo(
                name="c",
                available=False,
                version=None,
                pure_available=False,
                wasi_available=False,
                skip_reason="clang not found",
            )
    except FileNotFoundError:
        info = CompilerInfo(
            name="c",
            available=False,
            version=None,
            pure_available=False,
            wasi_available=False,
            skip_reason="clang not found",
        )

    _compiler_cache["c"] = info
    return info


def detect_rust_compiler() -> CompilerInfo:
    """Detect Rust compiler availability."""
    if "rust" in _compiler_cache:
        return _compiler_cache["rust"]

    try:
        result = run_command(["rustc", "--version"], check=False)
        if result.returncode == 0:
            version = result.stdout.strip()
            installed = get_rustc_installed_targets()
            pure_ok = "wasm32-unknown-unknown" in installed
            wasi_ok = "wasm32-wasip1" in installed or "wasm32-wasi" in installed
            skip_reasons = []
            if not pure_ok:
                skip_reasons.append("wasm32-unknown-unknown target not installed")
            if not wasi_ok:
                skip_reasons.append("wasm32-wasi target not installed")
            info = CompilerInfo(
                name="rust",
                available=True,
                version=version,
                pure_available=pure_ok,
                wasi_available=wasi_ok,
                skip_reason="; ".join(skip_reasons) if skip_reasons else None,
            )
        else:
            info = CompilerInfo(
                name="rust",
                available=False,
                version=None,
                pure_available=False,
                wasi_available=False,
                skip_reason="rustc not found",
            )
    except FileNotFoundError:
        info = CompilerInfo(
            name="rust",
            available=False,
            version=None,
            pure_available=False,
            wasi_available=False,
            skip_reason="rustc not found",
        )

    _compiler_cache["rust"] = info
    return info


def detect_zig_compiler() -> CompilerInfo:
    """Detect Zig compiler availability."""
    if "zig" in _compiler_cache:
        return _compiler_cache["zig"]

    try:
        result = run_command(["zig", "version"], check=False)
        if result.returncode == 0:
            version = result.stdout.strip()
            info = CompilerInfo(
                name="zig",
                available=True,
                version=version,
                pure_available=True,
                wasi_available=True,
                skip_reason=None,
            )
        else:
            info = CompilerInfo(
                name="zig",
                available=False,
                version=None,
                pure_available=False,
                wasi_available=False,
                skip_reason="zig not found",
            )
    except FileNotFoundError:
        info = CompilerInfo(
            name="zig",
            available=False,
            version=None,
            pure_available=False,
            wasi_available=False,
            skip_reason="zig not found",
        )

    _compiler_cache["zig"] = info
    return info


COMPILER_DETECTORS: dict[str, Callable[[], CompilerInfo]] = {
    "c": detect_c_compiler,
    "rust": detect_rust_compiler,
    "zig": detect_zig_compiler,
}


def detect_compiler(language: str) -> CompilerInfo:
    """Detect if a language compiler is available."""
    detector = COMPILER_DETECTORS.get(language)
    if detector is None:
        return CompilerInfo(
            name=language,
            available=False,
            version=None,
            pure_available=False,
            wasi_available=False,
            skip_reason=f"unknown language: {language}",
        )
    return detector()


def detect_nodejs() -> tuple[bool, str | None]:
    """Check if Node.js is available."""
    try:
        result = run_command(["node", "--version"], check=False)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    return False, None


def detect_waq() -> tuple[bool, str | None]:
    """Check if waq is available."""
    try:
        result = run_command(["waq", "--version"], check=False)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    return False, None


def get_wasm_cache_path(source_path: Path, mode: str) -> Path:
    """Get the cached WASM output path for a source file."""
    content_hash = hashlib.md5(source_path.read_bytes()).hexdigest()[:8]
    lang = source_path.parent.name
    name = source_path.stem
    return COMPILED_DIR / mode / lang / f"{name}_{content_hash}.wasm"


def get_rust_wasi_target() -> str:
    """Get the appropriate Rust WASI target."""
    installed = get_rustc_installed_targets()
    if "wasm32-wasip1" in installed:
        return "wasm32-wasip1"
    return "wasm32-wasi"


def compile_c_pure(source: Path, output: Path) -> None:
    """Compile C to pure WASM (no WASI)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "clang",
        "--target=wasm32",
        "-O2",
        "-nostdlib",
        "-Wl,--no-entry",
        "-Wl,--export-all",
        "-o",
        str(output),
        str(source),
    ]
    run_command(cmd)


def compile_c_wasi(source: Path, output: Path) -> None:
    """Compile C to WASI WASM."""
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("wasm32-wasi-clang"):
        cmd = ["wasm32-wasi-clang", "-O2", "-o", str(output), str(source)]
    else:
        cmd = ["clang", "--target=wasm32-wasi", "-O2", "-o", str(output), str(source)]
    run_command(cmd)


def compile_rust_pure(source: Path, output: Path) -> None:
    """Compile Rust to pure WASM (no WASI)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "rustc",
        "--target",
        "wasm32-unknown-unknown",
        "--crate-type",
        "cdylib",
        "-O",
        "-o",
        str(output),
        str(source),
    ]
    run_command(cmd)


def compile_rust_wasi(source: Path, output: Path) -> None:
    """Compile Rust to WASI WASM."""
    output.parent.mkdir(parents=True, exist_ok=True)
    target = get_rust_wasi_target()
    cmd = [
        "rustc",
        "--target",
        target,
        "-O",
        "-o",
        str(output),
        str(source),
    ]
    run_command(cmd)


def compile_zig_pure(source: Path, output: Path) -> None:
    """Compile Zig to pure WASM (no WASI)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "zig",
        "build-exe",
        "-target",
        "wasm32-freestanding",
        "-O",
        "ReleaseSmall",
        "-fno-entry",
        "--export=main",
        f"-femit-bin={output}",
        str(source),
    ]
    run_command(cmd)


def compile_zig_wasi(source: Path, output: Path) -> None:
    """Compile Zig to WASI WASM."""
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "zig",
        "build-exe",
        "-target",
        "wasm32-wasi",
        "-O",
        "ReleaseSmall",
        f"-femit-bin={output}",
        str(source),
    ]
    run_command(cmd)


COMPILERS: dict[str, dict[str, Callable[[Path, Path], None]]] = {
    "c": {"pure": compile_c_pure, "wasi": compile_c_wasi},
    "rust": {"pure": compile_rust_pure, "wasi": compile_rust_wasi},
    "zig": {"pure": compile_zig_pure, "wasi": compile_zig_wasi},
}


def compile_to_wasm(source: Path, mode: str) -> Path:
    """Compile a source file to WASM.

    Args:
        source: Path to source file
        mode: "pure" or "wasi"

    Returns:
        Path to compiled WASM file
    """
    output = get_wasm_cache_path(source, mode)

    if output.exists():
        return output

    lang = source.parent.name
    compiler = COMPILERS.get(lang, {}).get(mode)
    if compiler is None:
        msg = f"No compiler for {lang}/{mode}"
        raise ValueError(msg)

    compiler(source, output)
    return output


def run_with_nodejs_pure(wasm_path: Path, func_name: str = "main") -> ExecutionResult:
    """Run pure WASM with Node.js by calling an exported function."""
    result = subprocess.run(
        ["node", str(NODE_RUNNER), str(wasm_path), "--mode", "pure", "--func", func_name],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return ExecutionResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def run_with_nodejs_wasi(wasm_path: Path) -> ExecutionResult:
    """Run WASI WASM with Node.js."""
    result = subprocess.run(
        ["node", str(NODE_RUNNER), str(wasm_path), "--mode", "wasi"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return ExecutionResult(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def run_with_waq_pure(
    wasm_path: Path, func_name: str = "main", tmp_path: Path | None = None
) -> ExecutionResult:
    """Compile with waq and run (pure WASM mode)."""
    if tmp_path is None:
        tmp_path = Path("/tmp")

    exe_path = tmp_path / "waq_output"

    compile_result = subprocess.run(
        ["waq", str(wasm_path), "--emit", "exe", "--entry", func_name, "--no-print", "-o", str(exe_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    if compile_result.returncode != 0:
        return ExecutionResult(
            exit_code=compile_result.returncode,
            stdout=compile_result.stdout,
            stderr=f"waq compilation failed: {compile_result.stderr}",
        )

    run_result = subprocess.run(
        [str(exe_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    return ExecutionResult(
        exit_code=run_result.returncode,
        stdout=run_result.stdout,
        stderr=run_result.stderr,
    )


def run_with_waq_wasi(wasm_path: Path, tmp_path: Path | None = None) -> ExecutionResult:
    """Compile with waq and run (WASI mode)."""
    if tmp_path is None:
        tmp_path = Path("/tmp")

    exe_path = tmp_path / "waq_output"

    # WASI programs use _start as entry point, not main
    compile_result = subprocess.run(
        ["waq", str(wasm_path), "--emit", "exe", "--entry", "_start", "--no-print", "-o", str(exe_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    if compile_result.returncode != 0:
        return ExecutionResult(
            exit_code=compile_result.returncode,
            stdout=compile_result.stdout,
            stderr=f"waq compilation failed: {compile_result.stderr}",
        )

    run_result = subprocess.run(
        [str(exe_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    return ExecutionResult(
        exit_code=run_result.returncode,
        stdout=run_result.stdout,
        stderr=run_result.stderr,
    )


@pytest.fixture(scope="session")
def nodejs_available() -> tuple[bool, str | None]:
    """Check if Node.js is available."""
    return detect_nodejs()


@pytest.fixture(scope="session")
def waq_available() -> tuple[bool, str | None]:
    """Check if waq is available."""
    return detect_waq()


@pytest.fixture(scope="session")
def compiler_info() -> dict[str, CompilerInfo]:
    """Get compiler availability information for all languages."""
    return {lang: detect_compiler(lang) for lang in COMPILER_DETECTORS}


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "polyglot: mark test as a polyglot WASM test")
    config.addinivalue_line("markers", "pure_wasm: mark test as pure WASM (no WASI)")
    config.addinivalue_line("markers", "wasi: mark test as WASI WASM")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Add polyglot marker to all tests in this directory."""
    for item in items:
        if "d_polyglot" in str(item.fspath):
            item.add_marker(pytest.mark.polyglot)
