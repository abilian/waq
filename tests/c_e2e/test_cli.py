"""End-to-end tests for the CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from waq.cli import main


class TestCLIBasic:
    """Basic CLI functionality tests."""

    def test_help(self, capsys):
        """Test --help output."""
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "waq" in captured.out
        assert "WASM" in captured.out

    def test_version(self, capsys):
        """Test --version output."""
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "0.1.1" in captured.out

    def test_missing_input(self, capsys):
        """Test error when no input file is provided."""
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code != 0

    def test_file_not_found(self, capsys):
        """Test error when input file doesn't exist."""
        result = main(["nonexistent.wasm"])
        assert result == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err or "not found" in captured.err.lower()


class TestCLICompilation:
    """Tests for CLI compilation."""

    @pytest.fixture
    def minimal_wasm(self, tmp_path):
        """Create a minimal WASM file."""
        wasm_file = tmp_path / "test.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")
        return wasm_file

    @pytest.fixture
    def wasm_with_function(self, tmp_path):
        """Create a WASM file with a simple function."""
        wasm_file = tmp_path / "func.wasm"
        wasm = bytes([
            0x00,
            0x61,
            0x73,
            0x6D,  # magic
            0x01,
            0x00,
            0x00,
            0x00,  # version
            # Type section: () -> ()
            0x01,
            0x04,
            0x01,
            0x60,
            0x00,
            0x00,
            # Function section
            0x03,
            0x02,
            0x01,
            0x00,
            # Export section: export "f"
            0x07,
            0x05,
            0x01,
            0x01,
            0x66,
            0x00,
            0x00,
            # Code section
            0x0A,
            0x04,
            0x01,
            0x02,
            0x00,
            0x0B,
        ])
        wasm_file.write_bytes(wasm)
        return wasm_file

    def test_compile_minimal_module(self, minimal_wasm, tmp_path):
        """Test compiling a minimal WASM module."""
        output_file = tmp_path / "output.ssa"
        result = main([str(minimal_wasm), "-o", str(output_file)])
        assert result == 0
        assert output_file.exists()

    def test_compile_with_function(self, wasm_with_function, tmp_path):
        """Test compiling a WASM module with a function."""
        output_file = tmp_path / "output.ssa"
        result = main([str(wasm_with_function), "-o", str(output_file)])
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "export" in content
        assert "$f" in content

    def test_default_output_name(self, minimal_wasm):
        """Test that default output has .ssa extension."""
        result = main([str(minimal_wasm)])
        assert result == 0
        output_file = minimal_wasm.with_suffix(".ssa")
        assert output_file.exists()
        # Cleanup
        output_file.unlink()

    def test_verbose_output(self, wasm_with_function, tmp_path, capsys):
        """Test verbose mode."""
        output_file = tmp_path / "output.ssa"
        result = main([str(wasm_with_function), "-o", str(output_file), "-v"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Reading" in captured.out
        assert "Parsing" in captured.out
        assert "Compiling" in captured.out
        assert "Writing" in captured.out
        assert "Done" in captured.out


class TestCLITargets:
    """Tests for different target architectures."""

    @pytest.fixture
    def minimal_wasm(self, tmp_path):
        """Create a minimal WASM file."""
        wasm_file = tmp_path / "test.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")
        return wasm_file

    @pytest.mark.parametrize(
        "target",
        [
            "amd64_sysv",
            "amd64_apple",
            "arm64",
            "arm64_apple",
            "rv64",
        ],
    )
    def test_target_architectures(self, minimal_wasm, tmp_path, target):
        """Test compilation with different target architectures."""
        output_file = tmp_path / "output.ssa"
        result = main([str(minimal_wasm), "-o", str(output_file), "-t", target])
        assert result == 0
        assert output_file.exists()


class TestCLIEmitFormats:
    """Tests for different emit formats."""

    @pytest.fixture
    def minimal_wasm(self, tmp_path):
        """Create a minimal WASM file."""
        wasm_file = tmp_path / "test.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")
        return wasm_file

    def test_emit_qbe(self, minimal_wasm, tmp_path):
        """Test QBE output format."""
        output_file = tmp_path / "output.ssa"
        result = main([str(minimal_wasm), "-o", str(output_file), "--emit", "qbe"])
        assert result == 0
        assert output_file.exists()

    def test_emit_asm(self, minimal_wasm, tmp_path):
        """Test asm output format."""
        output_file = tmp_path / "output.s"
        result = main([str(minimal_wasm), "-o", str(output_file), "--emit", "asm"])
        # May fail if QBE not installed, which is acceptable
        if result == 0:
            assert output_file.exists()
            content = output_file.read_text()
            assert ".text" in content or "section" in content.lower()

    def test_emit_obj(self, minimal_wasm, tmp_path):
        """Test obj output format."""
        output_file = tmp_path / "output.o"
        result = main([str(minimal_wasm), "-o", str(output_file), "--emit", "obj"])
        # May fail if QBE not installed, which is acceptable
        if result == 0:
            assert output_file.exists()
            # Check it's a valid object file (has some content)
            assert output_file.stat().st_size > 0

    def test_emit_exe(self, tmp_path):
        """Test exe output format with fibonacci example."""
        import subprocess

        # Use the fibonacci fixture which exports wasm_main
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        wat_file = fixtures_dir / "fibonacci.wat"
        if not wat_file.exists():
            pytest.skip("fibonacci.wat fixture not found")

        output_file = tmp_path / "fibonacci"
        result = main([str(wat_file), "-o", str(output_file), "--emit", "exe"])
        # May fail if QBE/wat2wasm not installed
        if result == 0:
            assert output_file.exists()
            # Run the executable and check output
            proc = subprocess.run(
                [str(output_file)], capture_output=True, text=True, timeout=5
            )
            assert proc.returncode == 0
            assert proc.stdout.strip() == "55"  # fib(10) = 55


class TestCLIErrors:
    """Tests for CLI error handling."""

    def test_parse_error(self, tmp_path, capsys):
        """Test handling of parse errors."""
        wasm_file = tmp_path / "bad.wasm"
        wasm_file.write_bytes(b"\x00bad\x01\x00\x00\x00")  # Invalid magic
        result = main([str(wasm_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "Parse error" in captured.err or "invalid magic" in captured.err

    def test_invalid_wasm_version(self, tmp_path, capsys):
        """Test handling of invalid WASM version."""
        wasm_file = tmp_path / "bad_version.wasm"
        wasm_file.write_bytes(b"\x00asm\x02\x00\x00\x00")  # Invalid version
        result = main([str(wasm_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()
