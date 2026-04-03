"""Tests for NetlistError exception behaviour."""

import os
import pytest
from netlist_parser import NetlistParser, NetlistError


class TestNetlistError:
    def test_missing_file_raises_netlist_error(self, tmp_path):
        parser = NetlistParser()
        with pytest.raises(NetlistError):
            parser.parse(str(tmp_path / "nonexistent.spi"))

    def test_netlist_error_is_exception(self):
        assert issubclass(NetlistError, Exception)

    def test_netlist_error_message_readable(self, tmp_path):
        parser = NetlistParser()
        missing = str(tmp_path / "missing.spi")
        with pytest.raises(NetlistError) as exc_info:
            parser.parse(missing)
        assert str(exc_info.value) != ""
        assert "missing.spi" in str(exc_info.value)

    def test_netlist_error_can_be_caught_as_exception(self, tmp_path):
        parser = NetlistParser()
        caught = False
        try:
            parser.parse(str(tmp_path / "nope.spi"))
        except Exception:
            caught = True
        assert caught

    def test_empty_directory_returns_empty(self, tmp_path):
        """A directory with no valid netlist files returns an empty set/dict."""
        parser = NetlistParser()
        result = parser.read(str(tmp_path), data="cells")
        assert result == set()

    def test_read_missing_file_raises_netlist_error(self, tmp_path):
        parser = NetlistParser()
        with pytest.raises(NetlistError):
            parser.read(str(tmp_path / "nope.spi"), data="cells")
