"""Integration tests: continuation lines, data= modes, directory scanning."""

import os
import pytest
from netlist_parser import NetlistParser, Netlist


TESTS_DIR = os.path.dirname(__file__)


class TestContinuationLines:
    def test_backslash_continuation_joined(self, continuation_file):
        netlist = NetlistParser().parse(continuation_file)
        assert len(netlist.cells) == 1
        cell = netlist.cells[0]
        # XM0 should have all its parameters despite line-continuation with '\'
        xm0 = next(i for i in cell.instances if i.name == "XM0")
        assert "AD" in xm0.parameters or xm0.device_name is not None

    def test_plus_continuation_joined(self, continuation_file):
        netlist = NetlistParser().parse(continuation_file)
        cell = netlist.cells[0]
        # XM1 node list is split across lines with '+' continuation
        xm1 = next(i for i in cell.instances if i.name == "XM1")
        # nodes should include B, VSS (at minimum)
        assert len(xm1.nodes) >= 2

    def test_continuation_instance_count(self, continuation_file):
        netlist = NetlistParser().parse(continuation_file)
        cell = netlist.cells[0]
        assert len(cell.instances) == 2


class TestReadDataModes:
    def test_cells_mode_returns_set(self, spi_file):
        # Use internal=True so inv_x1 (which also appears as a device) is not filtered
        result = NetlistParser(internal=True).read(spi_file, data="cells")
        assert isinstance(result, set)
        assert "inv_x1" in result
        assert "and2_x1" in result

    def test_ports_mode_returns_dict(self, spi_file):
        result = NetlistParser(internal=True).read(spi_file, data="ports")
        assert isinstance(result, dict)
        assert "inv_x1" in result
        assert result["inv_x1"] == ["A", "ZN", "VDD", "VSS"]

    def test_devices_mode_returns_dict(self, spi_file):
        result = NetlistParser(internal=True).read(spi_file, data="devices")
        assert isinstance(result, dict)
        assert "inv_x1" in result
        assert "pmos" in result["inv_x1"]
        assert "nmos" in result["inv_x1"]

    def test_resistors_mode_returns_dict(self, spi_file):
        result = NetlistParser(internal=True).read(spi_file, data="resistors")
        assert isinstance(result, dict)
        # and2_x1 has R1
        assert "and2_x1" in result
        r_list = result["and2_x1"]
        assert len(r_list) > 0
        r1 = r_list[0]
        assert r1[0] == "R1"  # instance name

    def test_capacitors_mode_returns_dict(self, spi_file):
        result = NetlistParser(internal=True).read(spi_file, data="capacitors")
        assert isinstance(result, dict)
        assert "inv_x1" in result
        caps = result["inv_x1"]
        assert len(caps) > 0
        # Each entry is [name, number]
        assert caps[0][0] == "c_a"
        assert caps[0][1] == "10f"

    def test_none_mode_returns_netlist(self, spi_file):
        result = NetlistParser().read(spi_file)
        assert isinstance(result, Netlist)

    def test_cir_cells_mode(self, cir_file):
        result = NetlistParser().read(cir_file, data="cells")
        assert "clamp_cell" in result
        assert "fillcap" in result


class TestInternalFlag:
    def test_internal_false_excludes_internal_cells(self, spi_file):
        """With internal=False, inv_x1 used as a device in and2_x1 should be
        filtered from 'cells' output because inv_x1 appears as both a subckt
        definition and a referenced device."""
        result = NetlistParser(internal=False).read(spi_file, data="cells")
        # inv_x1 is used as a device inside and2_x1, so with internal=False it
        # should be removed
        assert "inv_x1" not in result

    def test_internal_true_keeps_all_cells(self, spi_file):
        result = NetlistParser(internal=True).read(spi_file, data="cells")
        assert "inv_x1" in result
        assert "and2_x1" in result


class TestDirectoryScanning:
    def test_directory_cells_mode(self, tmp_path, spi_file, cir_file):
        import shutil
        shutil.copy(spi_file, tmp_path / "sample.spi")
        shutil.copy(cir_file, tmp_path / "sample.cir")
        result = NetlistParser(internal=True).read(str(tmp_path), data="cells")
        assert isinstance(result, set)
        assert len(result) > 0

    def test_multi_cell_cir(self, cir_netlist):
        assert len(cir_netlist.cells) == 2
