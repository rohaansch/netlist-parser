"""Core parsing tests for netlist_parser."""

import pytest
from netlist_parser import NetlistParser, Netlist, NetlistCell, DeviceInstance


class TestBasicParsing:
    def test_spi_returns_netlist(self, spi_netlist):
        assert isinstance(spi_netlist, Netlist)

    def test_spi_version_set(self, spi_netlist):
        assert spi_netlist.version == "spi"

    def test_spi_cells_non_empty(self, spi_netlist):
        assert len(spi_netlist.cells) > 0

    def test_cir_returns_netlist(self, cir_netlist):
        assert isinstance(cir_netlist, Netlist)

    def test_cir_version_set(self, cir_netlist):
        assert cir_netlist.version == "cir"


class TestSpiParsing:
    def test_two_cells(self, spi_netlist):
        assert len(spi_netlist.cells) == 2

    def test_cell_names(self, spi_netlist):
        names = [c.name for c in spi_netlist.cells]
        assert "inv_x1" in names
        assert "and2_x1" in names

    def test_inv_x1_ports(self, spi_cell):
        assert spi_cell.name == "inv_x1"
        assert spi_cell.ports == ["A", "ZN", "VDD", "VSS"]

    def test_inv_x1_instance_count(self, spi_cell):
        assert len(spi_cell.instances) == 3

    def test_mp1_code(self, spi_cell):
        mp1 = next(i for i in spi_cell.instances if i.name == "Mp1")
        assert mp1.code == "m"

    def test_mn1_code(self, spi_cell):
        mn1 = next(i for i in spi_cell.instances if i.name == "Mn1")
        assert mn1.code == "m"

    def test_c_a_code(self, spi_cell):
        c_a = next(i for i in spi_cell.instances if i.name == "c_a")
        assert c_a.code == "c"

    def test_mp1_device_name(self, spi_cell):
        mp1 = next(i for i in spi_cell.instances if i.name == "Mp1")
        assert mp1.device_name == "pmos"

    def test_mn1_device_name(self, spi_cell):
        mn1 = next(i for i in spi_cell.instances if i.name == "Mn1")
        assert mn1.device_name == "nmos"

    def test_c_a_number(self, spi_cell):
        c_a = next(i for i in spi_cell.instances if i.name == "c_a")
        assert c_a.number == "10f"

    def test_c_a_device_name_is_none(self, spi_cell):
        c_a = next(i for i in spi_cell.instances if i.name == "c_a")
        assert c_a.device_name is None

    def test_mp1_parameters(self, spi_cell):
        mp1 = next(i for i in spi_cell.instances if i.name == "Mp1")
        assert mp1.parameters.get("W") == "500n"
        assert mp1.parameters.get("L") == "180n"

    def test_mn1_parameters(self, spi_cell):
        mn1 = next(i for i in spi_cell.instances if i.name == "Mn1")
        assert mn1.parameters.get("W") == "250n"
        assert mn1.parameters.get("L") == "180n"

    def test_and2_x1_subckt_instances(self, spi_netlist):
        and2 = next(c for c in spi_netlist.cells if c.name == "and2_x1")
        x_instances = [i for i in and2.instances if i.code == "x"]
        assert len(x_instances) == 2

    def test_and2_xinv_device_names(self, spi_netlist):
        and2 = next(c for c in spi_netlist.cells if c.name == "and2_x1")
        x_instances = [i for i in and2.instances if i.code == "x"]
        device_names = {i.device_name for i in x_instances}
        assert "inv_x1" in device_names

    def test_and2_r1_code(self, spi_netlist):
        and2 = next(c for c in spi_netlist.cells if c.name == "and2_x1")
        r1 = next(i for i in and2.instances if i.name == "R1")
        assert r1.code == "r"

    def test_and2_r1_number(self, spi_netlist):
        and2 = next(c for c in spi_netlist.cells if c.name == "and2_x1")
        r1 = next(i for i in and2.instances if i.name == "R1")
        assert r1.number == "100"

    def test_cell_str(self, spi_cell):
        assert str(spi_cell) == "inv_x1"

    def test_instance_str(self, spi_cell):
        mp1 = next(i for i in spi_cell.instances if i.name == "Mp1")
        assert str(mp1) == "Mp1"


class TestCdlParsing:
    def test_one_cell(self, cdl_netlist):
        assert len(cdl_netlist.cells) == 1

    def test_cell_name(self, cdl_netlist):
        assert cdl_netlist.cells[0].name == "bus_cut"

    def test_ports(self, cdl_netlist):
        cell = cdl_netlist.cells[0]
        assert cell.ports == ["CPWR", "OGND", "OPWRA", "OPWRB", "SUB"]

    def test_x_instances_have_device_name(self, cdl_netlist):
        cell = cdl_netlist.cells[0]
        x_instances = [i for i in cell.instances if i.code == "x"]
        assert len(x_instances) > 0
        for inst in x_instances:
            assert inst.device_name is not None

    def test_c_instances_have_number(self, cdl_netlist):
        cell = cdl_netlist.cells[0]
        c_instances = [i for i in cell.instances if i.code == "c"]
        assert len(c_instances) > 0
        for inst in c_instances:
            assert inst.number is not None

    def test_cdl_diode_device_name(self, cdl_netlist):
        cell = cdl_netlist.cells[0]
        xd1 = next(i for i in cell.instances if i.name == "XDnoxref1")
        assert xd1.device_name == "diodenwx"


class TestCirParsing:
    def test_two_cells(self, cir_netlist):
        assert len(cir_netlist.cells) == 2

    def test_version(self, cir_netlist):
        assert cir_netlist.version == "cir"

    def test_clamp_cell_ports(self, cir_cell):
        assert cir_cell.ports == ["CPWR", "OGND", "OPWR", "SUB"]

    def test_clamp_cell_instances(self, cir_cell):
        assert len(cir_cell.instances) > 0

    def test_fillcap_exists(self, cir_netlist):
        names = [c.name for c in cir_netlist.cells]
        assert "fillcap" in names
