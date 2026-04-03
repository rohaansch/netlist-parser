# Changelog

## [0.1.0] — 2025-04-02

### Added
- Initial release extracted from pet-automation NetlistParser.py
- `NetlistParser`, `Netlist`, `NetlistCell`, `DeviceInstance` classes
- `NetlistError` exception replacing `sys.exit()` calls
- `termcolor` made optional (graceful fallback)
- CLI `netlist-parser` with `--cells`, `--ports`, `--devices`, `--cell`, `--version`
- Support for `.spi`, `.cir`, `.cdl`, `.scs`, `.spf`, `.sp`, `.hsp` formats
- Line continuation via `\` and `+` prefix
- SPF parasitics data parsing (resistance, capacitance, layer_map)
- Zero mandatory runtime dependencies
