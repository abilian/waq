#!/usr/bin/env python3
"""Create a fuzzing corpus from test fixtures.

This script collects all .wasm files from the test suite and
copies them to a corpus directory for use with fuzzers.

Usage:
    python tests/fuzz/create_corpus.py [output_dir]
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Create the fuzzing corpus."""
    project_root = Path(__file__).parent.parent.parent
    tests_dir = project_root / "tests"
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else tests_dir / "fuzz" / "corpus"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    corpus_files = []

    # Find all .wasm files
    for wasm_file in tests_dir.rglob("*.wasm"):
        corpus_files.append(wasm_file)

    # Convert .wat files to .wasm
    for wat_file in tests_dir.rglob("*.wat"):
        wasm_out = output_dir / f"{wat_file.stem}_from_wat.wasm"
        try:
            result = subprocess.run(
                ["wat2wasm", str(wat_file), "-o", str(wasm_out)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                corpus_files.append(wasm_out)
            else:
                print(f"Warning: Failed to convert {wat_file}: {result.stderr}")
        except FileNotFoundError:
            print("Warning: wat2wasm not found, skipping .wat files")
            break

    # Copy files with content-based names (dedup)
    seen_hashes = set()
    copied_count = 0

    for src_file in corpus_files:
        if not src_file.exists():
            continue

        data = src_file.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()[:16]

        if file_hash in seen_hashes:
            continue
        seen_hashes.add(file_hash)

        # Use content hash as filename
        dest_file = output_dir / f"{file_hash}.wasm"
        if src_file != dest_file:
            shutil.copy2(src_file, dest_file)
        copied_count += 1

    # Add some minimal edge case inputs
    edge_cases = [
        # Empty file
        b"",
        # Just magic
        b"\x00asm",
        # Magic + version
        b"\x00asm\x01\x00\x00\x00",
        # Minimal valid module (empty)
        b"\x00asm\x01\x00\x00\x00",
        # Module with empty type section
        b"\x00asm\x01\x00\x00\x00\x01\x01\x00",
        # Module with empty function section
        b"\x00asm\x01\x00\x00\x00\x03\x01\x00",
        # Truncated header
        b"\x00as",
        # Wrong magic
        b"\x00bsm\x01\x00\x00\x00",
        # Wrong version
        b"\x00asm\x02\x00\x00\x00",
    ]

    for i, data in enumerate(edge_cases):
        dest_file = output_dir / f"edge_case_{i:03d}.wasm"
        dest_file.write_bytes(data)
        copied_count += 1

    print(f"Created corpus with {copied_count} files in {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
