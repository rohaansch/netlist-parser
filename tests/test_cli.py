"""CLI invocation tests for netlist-parser."""

import subprocess
import sys
import os
import pytest

TESTS_DIR = os.path.dirname(__file__)
SPI_FILE = os.path.join(TESTS_DIR, "sample.spi")
CIR_FILE = os.path.join(TESTS_DIR, "sample.cir")


def run(*args):
    """Run netlist_parser as a module and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "netlist_parser"] + list(args),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestCLIBasic:
    def test_summary_runs_without_error(self):
        code, out, err = run(SPI_FILE)
        assert code == 0

    def test_summary_contains_cell_count(self):
        code, out, _ = run(SPI_FILE)
        assert "2" in out  # 2 cells

    def test_summary_contains_cell_names(self):
        code, out, _ = run(SPI_FILE)
        assert "inv_x1" in out
        assert "and2_x1" in out

    def test_version_flag(self):
        code, out, _ = run("--version")
        assert code == 0
        assert out.strip() != ""

    def test_missing_file_nonzero_exit(self):
        code, _, err = run("/nonexistent/path/file.spi")
        assert code != 0
        assert err.strip() != ""

    def test_missing_file_error_message(self):
        code, _, err = run("/nonexistent/path/file.spi")
        assert "Error" in err or "error" in err


class TestCLICells:
    def test_cells_flag_lists_names(self):
        code, out, _ = run(SPI_FILE, "--cells")
        assert code == 0
        assert "inv_x1" in out
        assert "and2_x1" in out

    def test_cells_flag_line_per_cell(self):
        code, out, _ = run(SPI_FILE, "--cells")
        lines = [l for l in out.strip().splitlines() if l]
        assert len(lines) == 2


class TestCLIPorts:
    def test_ports_flag_shows_ports(self):
        code, out, _ = run(SPI_FILE, "--ports")
        assert code == 0
        assert "inv_x1" in out
        assert "A" in out
        assert "ZN" in out


class TestCLIDevices:
    def test_devices_flag_shows_device_names(self):
        code, out, _ = run(SPI_FILE, "--devices")
        assert code == 0
        assert "pmos" in out
        assert "nmos" in out


class TestCLICell:
    def test_cell_flag_shows_cell_detail(self):
        code, out, _ = run(SPI_FILE, "--cell", "inv_x1")
        assert code == 0
        assert "inv_x1" in out
        assert "Mp1" in out or "pmos" in out

    def test_cell_flag_missing_cell_nonzero_exit(self):
        code, _, err = run(SPI_FILE, "--cell", "nonexistent_cell")
        assert code != 0
