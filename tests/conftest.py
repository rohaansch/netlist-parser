"""Shared pytest fixtures for netlist-parser tests."""

import os
import pytest
from netlist_parser import NetlistParser, Netlist


TESTS_DIR = os.path.dirname(__file__)


def _path(name: str) -> str:
    return os.path.join(TESTS_DIR, name)


# ---- File path fixtures ------------------------------------------------

@pytest.fixture(scope="module")
def spi_file() -> str:
    return _path("sample.spi")


@pytest.fixture(scope="module")
def cdl_file() -> str:
    return _path("sample_cdl.spi")


@pytest.fixture(scope="module")
def cir_file() -> str:
    return _path("sample.cir")


@pytest.fixture(scope="module")
def continuation_file() -> str:
    return _path("sample_continuation.spi")


# ---- Parsed netlist fixtures -------------------------------------------

@pytest.fixture(scope="module")
def spi_netlist(spi_file) -> Netlist:
    return NetlistParser().parse(spi_file)


@pytest.fixture(scope="module")
def cdl_netlist(cdl_file) -> Netlist:
    return NetlistParser().parse(cdl_file)


@pytest.fixture(scope="module")
def cir_netlist(cir_file) -> Netlist:
    return NetlistParser().parse(cir_file)


# ---- Cell-level fixtures -----------------------------------------------

@pytest.fixture(scope="module")
def spi_cell(spi_netlist):
    """First cell of the sample .spi file (inv_x1)."""
    return spi_netlist.cells[0]


@pytest.fixture(scope="module")
def cir_cell(cir_netlist):
    """clamp_cell from the sample .cir file."""
    return next(c for c in cir_netlist.cells if c.name == "clamp_cell")
