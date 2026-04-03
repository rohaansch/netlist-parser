# eda-netlist-parser

A pure-Python parser for SPICE-family netlist files: `.spi`, `.cir`, `.cdl`, `.scs`, `.spf`, `.sp`, `.hsp`.

## Installation

```bash
pip install eda-netlist-parser
# optional colored terminal output:
pip install eda-netlist-parser[color]
```

## Quick start

```python
from netlist_parser import NetlistParser, NetlistError

parser = NetlistParser()

try:
    netlist = parser.parse("design.spi")
except NetlistError as e:
    print(f"Error: {e}")

for cell in netlist.cells:
    print(cell.name, cell.ports)
    for inst in cell.instances:
        print("  ", inst.name, inst.code, inst.device_name)
```

### Importing

```python
from netlist_parser import NetlistParser
from netlist_parser import NetlistParser, Netlist, NetlistCell, DeviceInstance
```

## API

### `NetlistParser(internal=False)`

| Method | Returns | Description |
|--------|---------|-------------|
| `parse(filename)` | `Netlist` | Parse a single file |
| `read(path, data=None)` | varies | Parse file or directory |

`read()` data modes:

| `data=` | Returns |
|---------|---------|
| `None` | `Netlist` |
| `'cells'` | `Set[str]` |
| `'ports'` | `Dict[str, List[str]]` |
| `'devices'` | `Dict[str, Set[str]]` |
| `'device-params'` | `Dict[str, Dict]` |
| `'resistors'` | `Dict[str, List]` |
| `'capacitors'` | `Dict[str, List]` |

### Classes

- `Netlist` — full file data: `.cells`, `.version`, `.resistance`, `.capacitance`, `.layer_map`
- `NetlistCell` — one subckt: `.name`, `.ports`, `.instances`, `.substitute`
- `DeviceInstance` — one line: `.name`, `.code`, `.nodes`, `.device_name`, `.number`, `.parameters`
- `NetlistError` — raised on file errors

## CLI

```
netlist-parser sample.spi                   # summary
netlist-parser sample.spi --cells           # list cell names
netlist-parser sample.spi --ports           # cell → ports
netlist-parser sample.spi --devices         # cell → device names
netlist-parser sample.spi --cell inv_x1     # one cell detail
netlist-parser --version
```

## License

MIT — 2025 Rohaan Scherpbier
