# Parsing SPICE Netlists in Pure Python

*No EDA license. No simulator. Just Python.*

---

If you work in analog or mixed-signal IC design, you have almost certainly written a script that opens a netlist file and tries to extract something from it — cell names, port lists, device counts, parameter values. The script probably lives in a corner of a repo somewhere, held together with regex and hope.

I wrote **netlist-parser** to replace that script permanently.

---

## What is a SPICE netlist?

A netlist is the text-based circuit description that flows between every stage of the analog design flow — from schematic capture to LVS to simulation to characterization. It lists every subcircuit, every port, every device instance, and every parameter value.

SPICE is the original simulation engine (Simulation Program with Integrated Circuit Emphasis, Bell Labs 1973), and its netlist format has spawned a family of dialects:

| Extension | Dialect | Tool |
|---|---|---|
| `.spi` | SPICE | Cadence, Synopsys HSPICE |
| `.cir` | SPICE | SiliconSmart decks, general |
| `.scs` | Spectre | Cadence Virtuoso |
| `.cdl` | CDL | Cadence LVS |
| `.sp` | SPICE | General |
| `.spf` | DSPF | Post-layout parasitics |
| `.hsp` | HSPICE | Synopsys HSPICE |

All dialects share the same underlying concept: a hierarchical list of subcircuits (`subckt`), each containing device instances, and a flat parameter syntax. But the formatting rules differ enough that a naïve parser written for one dialect will silently misparse another.

---

## The format in detail

Here is a minimal SPICE inverter (`inv_x1`) and AND gate (`and2_x1`):

```spice
* Sample SPICE netlist
.subckt inv_x1 A ZN VDD VSS
Mp1 ZN A VDD VDD pmos W=500n L=180n
Mn1 ZN A VSS VSS nmos W=250n L=180n
c_a A VSS 10f
.ends inv_x1

.subckt and2_x1 A1 A2 ZN VDD VSS
Xinv1 net1 A1 VDD VSS inv_x1
Xinv2 net2 A2 VDD VSS inv_x1
R1 ZN out 100
.ends and2_x1
```

The same cells in Cadence Spectre (`.scs`) look different:

```spectre
// Spectre netlist — port lists use parentheses
subckt inv_x1 (A ZN VDD VSS)
Mp1 (ZN A VDD VDD) pmos w=500n l=180n
Mn1 (ZN A VSS VSS) nmos w=250n l=180n
c_a (A VSS) capacitor c=10f
r_out (ZN ZN_int) resistor r=50
ends inv_x1

subckt and2_x1 (A1 A2 ZN VDD VSS)
Xinv1 (net1 A1 VDD VSS) inv_x1
Xinv2 (net2 A2 VDD VSS) inv_x1
c_load (ZN VSS) capacitor c=20f
ends and2_x1
```

Differences to handle:
- SPICE uses `*` for comments; Spectre uses `//`
- SPICE uses `.subckt`/`.ends`; Spectre uses `subckt`/`ends` (no leading dot)
- Spectre wraps port lists in parentheses
- Spectre passives use `capacitor c=value` / `resistor r=value` keyword syntax
- Long SPICE lines continue with a trailing `\`, or the next line starting with `+`

And real-world post-layout netlists (`.spf` / DSPF format) add another layer: special comment annotations like `*|NET`, `*|P`, `*|S`, `*|I` that encode layer-level parasitic extraction data alongside the device instances.

A production parser has to handle all of this without the caller needing to care.

---

## Installation

```bash
pip install eda-netlist-parser
```

Zero mandatory dependencies. Pure Python 3.7+. `termcolor` is supported as an optional extra for colored terminal output:

```bash
pip install "eda-netlist-parser[color]"
```

---

## Parsing a file

```python
from netlist_parser import NetlistParser

parser = NetlistParser()
netlist = parser.parse("design.spi")
```

The returned `Netlist` object holds everything:

```python
print(netlist.version)        # 'spi' — derived from file extension
print(len(netlist.cells))     # number of subcircuits
```

The format is detected automatically from the file extension. You do not configure it.

---

## Navigating cells and ports

```python
for cell in netlist.cells:
    print(cell.name)          # 'inv_x1', 'and2_x1', ...
    print(cell.ports)         # ['A', 'ZN', 'VDD', 'VSS']
```

Each `NetlistCell` is a subcircuit. Its `ports` list reflects the exact port order from the `.subckt` line — critical for LVS and connectivity checks.

---

## Inspecting device instances

Each line inside a subcircuit becomes a `DeviceInstance`:

```python
cell = netlist.cells[0]   # inv_x1

for inst in cell.instances:
    print(inst.name)        # 'Mp1', 'Mn1', 'c_a'
    print(inst.code)        # 'm', 'm', 'c'  (first char of instance name, lowercased)
    print(inst.nodes)       # connection nodes
    print(inst.device_name) # 'pmos', 'nmos', None
    print(inst.number)      # None, None, '10f'
    print(inst.parameters)  # {'W': '500n', 'L': '180n'}, ...
```

The `code` field encodes the device type by SPICE convention:

| Code | Device type |
|---|---|
| `x` | Subcircuit instance |
| `m` | MOSFET |
| `c` | Capacitor |
| `r` | Resistor |
| `d` | Diode |
| `l` | Inductor |
| `v` | Voltage source |

For passives (`c`, `r`), the value is stored in `number` as a string preserving the original SI suffix (`10f`, `0.425554f`, `100`). For device instances (`x`, `m`, `d`), `device_name` holds the subcircuit or model name in lowercase.

---

## Subcircuit instances (X devices)

```python
# and2_x1 contains two inverter instances
cell = netlist.cells[1]   # and2_x1

for inst in cell.instances:
    if inst.code == 'x':
        print(inst.name)         # 'Xinv1', 'Xinv2'
        print(inst.device_name)  # 'inv_x1', 'inv_x1'
        print(inst.nodes)        # ['net1', 'A1', 'VDD', 'VSS']
        print(inst.parameters)   # {}
```

---

## The `read()` API — high-level data extraction

`parse()` gives you the full object tree. `read()` gives you pre-shaped data dicts for common queries:

```python
parser = NetlistParser()

# Set of all cell names defined in the file
cells = parser.read("design.spi", data="cells")
# → {'inv_x1', 'and2_x1'}

# Dict: cell name → list of port names
ports = parser.read("design.spi", data="ports")
# → {'inv_x1': ['A', 'ZN', 'VDD', 'VSS'], 'and2_x1': ['A1', 'A2', 'ZN', 'VDD', 'VSS']}

# Dict: cell name → set of device names used inside it
devices = parser.read("design.spi", data="devices")
# → {'inv_x1': {'pmos', 'nmos'}, 'and2_x1': {'inv_x1'}}

# Dict: cell name → list of [inst_name, nodes, value, params] for every resistor
resistors = parser.read("design.spi", data="resistors")

# Dict: cell name → list of [inst_name, value] for every capacitor
capacitors = parser.read("design.spi", data="capacitors")

# Dict: cell name → dict of {device_name: {inst_name: {param: value}}}
device_params = parser.read("design.spi", data="device-params")
```

`read()` also accepts a directory path — it walks the directory, parses every file with a recognized extension, and merges results:

```python
all_cells = parser.read("/path/to/netlist/dir", data="cells")
```

---

## The `internal` flag

Large netlists often define helper subcircuits that are only used as primitive devices inside other cells — they appear both as a `subckt` definition and as an `X` instance. By default, `NetlistParser(internal=False)` excludes these internal cells from `read()` output (they are tracked as device names, not as top-level cells). Set `internal=True` to include them:

```python
# Default: internal helper cells excluded from results
parser = NetlistParser()

# Include internal cells
parser_all = NetlistParser(internal=True)
```

---

## Line continuation

Real production netlists commonly break long device lines across multiple lines. The parser handles both SPICE continuation styles transparently:

```spice
* Trailing backslash continuation
XM0 out A VDD VDD pmos W=1u L=0.18u \
+ AD=0.18e-12 AS=0.18e-12

* Leading-plus continuation
XM1 out \
+ B \
+ VSS VSS nmos W=0.5u L=0.18u
```

Both forms produce a single `DeviceInstance` with all parameters merged, exactly as if written on one line.

---

## Spectre format

Spectre (`.scs`) is the native format for Cadence Virtuoso simulations. The parser detects it from the file extension and applies Spectre-specific rules automatically:

```spectre
subckt inv_x1 (A ZN VDD VSS)
Mp1 (ZN A VDD VDD) pmos w=500n l=180n
c_a (A VSS) capacitor c=10f
ends inv_x1
```

Internally, the parser:
1. Strips `(` and `)` from every line before tokenizing
2. Detects `capacitor c=value` / `resistor r=value` syntax and extracts the numeric value

From Python, you access it identically to any other format:

```python
netlist = parser.parse("design.scs")
print(netlist.version)         # 'scs'

cell = netlist.cells[0]
print(cell.ports)              # ['A', 'ZN', 'VDD', 'VSS']

cap = next(i for i in cell.instances if i.code == 'c')
print(cap.number)              # '10f'
```

---

## CDL format

CDL (Circuit Description Language) is the format Cadence Virtuoso writes for LVS netlists. Its passives use a fixed column structure rather than scanning backwards from the end:

```
.SUBCKT bus_cut CPWR OGND OPWRA OPWRB SUB
XRR0pc SUB SUB SUB opppcres M=1 w=4e-07 l=1.4e-06
XDnoxref1 SUB noxref_4 diodenwx AREA=4.4154e-12 perim=8.42e-06
c_1 noxref_4 0 0.425554f
c_4 CPWR 0 2.14755f
cc_1 CPWR OGND 0.129039f
.ENDS
```

CDL capacitors and resistors always have their value at token position 3 (or 4 if a `$SUB=` token appears). The parser handles this automatically based on the `.cdl` extension.

---

## Post-layout parasitics (DSPF / .spf)

Post-layout netlists in DSPF format embed parasitic extraction data as structured comments alongside the device netlist:

```
*|NET SIGNAL_A 1.23e-15
*|P (SIGNAL_A $lvl=7)
*|S (SIGNAL_A:1 $lvl=5)
R1_258 SIGNAL_A SIGNAL_A:1 12.5
C1_412 SIGNAL_A:1 0 0.8e-15
```

The `*|NET`, `*|P`, `*|S`, `*|I` annotations are parsed into `netlist.resistance` and `netlist.capacitance` dictionaries keyed by net name and layer, enabling layer-aware parasitic analysis.

---

## Error handling

All errors raise `NetlistError` — a plain Python exception — instead of calling `sys.exit()`. The library is safe to use inside any pipeline:

```python
from netlist_parser import NetlistParser, NetlistError

try:
    netlist = parser.parse("missing.spi")
except NetlistError as e:
    print(e)   # NetlistError: Could not find file: missing.spi
```

```python
# Works safely inside larger automation
for path in glob.glob("**/*.spi", recursive=True):
    try:
        netlist = parser.parse(path)
        process(netlist)
    except NetlistError:
        continue
```

---

## CLI

The package ships a command-line tool for quick inspection without writing any Python:

```bash
# Summary
netlist-parser design.spi
# File:  design.spi
# Format: spi
# Cells (2):
#   inv_x1    ports=4  instances=3
#   and2_x1   ports=5  instances=3

# List cell names only
netlist-parser design.spi --cells
# inv_x1
# and2_x1

# Port lists
netlist-parser design.spi --ports
# inv_x1: A ZN VDD VSS
# and2_x1: A1 A2 ZN VDD VSS

# Devices used per cell
netlist-parser design.spi --devices
# inv_x1: nmos, pmos
# and2_x1: inv_x1

# Detailed view of one cell
netlist-parser design.spi --cell inv_x1
# Cell: inv_x1
#   Ports: A ZN VDD VSS
#   Instances (3):
#     Mp1  code=m  device=pmos  nodes=['ZN', 'A', 'VDD', 'VDD']  params={'W': '500n', 'L': '180n'}
#     Mn1  code=m  device=nmos  nodes=['ZN', 'A', 'VSS', 'VSS']  params={'W': '250n', 'L': '180n'}
#     c_a  code=c  number=10f   nodes=['A', 'VSS']

netlist-parser --version
```

---

## Real-world use cases

**Get all cell names from a directory of characterization decks:**

```python
parser = NetlistParser()
cells = parser.read("/sim/decks/", data="cells")
print(sorted(cells))
```

**Build a device-usage matrix across all cells:**

```python
devices = parser.read("design.spi", data="devices")
for cell_name, device_set in devices.items():
    print(f"{cell_name:<20} {sorted(device_set)}")
```

**Extract every MOSFET W/L for a cell:**

```python
netlist = parser.parse("design.spi")
cell = next(c for c in netlist.cells if c.name == "inv_x1")

for inst in cell.instances:
    if inst.code == 'm' and 'W' in inst.parameters:
        print(f"  {inst.name}: W={inst.parameters['W']}  L={inst.parameters['L']}")
```

**Count capacitor instances per cell:**

```python
caps = parser.read("layout.spi", data="capacitors")
for cell_name, cap_list in caps.items():
    print(f"{cell_name}: {len(cap_list)} capacitors")
```

**Check which cells in a library use a specific device:**

```python
devices = parser.read("/lib/", data="devices")
target = "diodenwx"
users = [cell for cell, devs in devices.items() if target in devs]
print(f"Cells using {target}: {users}")
```

**Cross-check LVS ports against a known port list:**

```python
expected = {'A', 'ZN', 'VDD', 'VSS'}
ports = parser.read("extracted.cdl", data="ports")
actual = set(ports.get("inv_x1", []))
if actual != expected:
    print(f"Port mismatch: expected {expected}, got {actual}")
```

**Walk a directory and build a flat JSON manifest:**

```python
import json, glob
from netlist_parser import NetlistParser

parser = NetlistParser()
manifest = {}
for path in glob.glob("decks/**/*.spi", recursive=True):
    try:
        p = parser.read(path, data="ports")
        manifest.update(p)
    except Exception:
        pass

with open("manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
```

---

## Testing

The test suite covers 67 cases across 4 test files, using hand-crafted sample netlists in each supported format as fixtures:

```
test_parser.py       — 37 tests: cells, ports, instances, device names,
                       numbers, parameters, codes — across SPICE / CDL / CIR
test_exceptions.py   —  6 tests: missing file, bad path, NetlistError type
test_integration.py  — 12 tests: line continuation, all data= modes,
                       internal= flag, multi-cell files, directory scan
test_cli.py          — 12 tests: every CLI flag via subprocess
```

Test sample files:

| File | Format | Tests |
|---|---|---|
| `sample.spi` | SPICE | Core MOSFET, capacitor, resistor, X-instance parsing |
| `sample_cdl.spi` | CDL | Fixed-position passive parsing, `$SUB=` handling |
| `sample.cir` | CIR | `.title` lines, multi-cell files |
| `sample.scs` | Spectre | Parenthesized ports, `capacitor c=` syntax |
| `sample_continuation.spi` | SPICE | `\` and `+` line joining |

Run them:

```bash
pip install -e ".[dev]"
pytest -v
```

---

## Design notes

**Format detection from extension.** Rather than asking the caller to specify a format flag, the parser sets `netlist.version` from the file extension and uses it to gate format-specific rules. This means one API call works for all dialects.

**Instance code from first character.** SPICE mandates that an instance name's first letter encodes its device type (M for MOSFET, X for subcircuit, C for capacitor, etc.). The parser lowercases this and stores it as `code`, giving you O(1) type dispatch without string comparisons.

**Backward scan for device token.** For non-CDL formats, identifying which token is the device name (vs. a node or a parameter) requires scanning backwards from the end of the line — parameters are `key=value`, nodes are bare tokens, and the device name is the last bare token before the parameters begin. The CDL exception (fixed position) is handled by the version check.

**Exceptions, not sys.exit().** A library that calls `sys.exit()` is unusable in any pipeline that needs to continue after a parse failure. Every error in `netlist-parser` raises `NetlistError`, so callers decide what to do.

**Zero mandatory dependencies.** Netlist parsing scripts frequently run inside EDA tool environments — Cadence SKILL Python bridges, Synopsys custom flows, Make-based batch jobs — where installing compiled dependencies is painful. Zero deps means `pip install eda-netlist-parser` works anywhere Python does.

---

## Get it

```bash
pip install eda-netlist-parser
```

Source: [github.com/rohaansch/netlist-parser](https://github.com/rohaansch/netlist-parser)

If you are parsing netlists in your EDA automation flow, I would love to hear what you are building.
