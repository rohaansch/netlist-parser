"""Basic usage examples for netlist_parser."""

from netlist_parser import NetlistParser, NetlistError

# ---- Parse a single file and inspect cells ----
parser = NetlistParser()

try:
    netlist = parser.parse("tests/sample.spi")
except NetlistError as e:
    print(f"Error: {e}")
    raise SystemExit(1)

print(f"Version/format: {netlist.version}")
print(f"Number of cells: {len(netlist.cells)}")
print()

for cell in netlist.cells:
    print(f"Cell: {cell.name}")
    print(f"  Ports: {cell.ports}")
    print(f"  Instances:")
    for inst in cell.instances:
        print(f"    {inst.name}  code={inst.code}  device={inst.device_name}  number={inst.number}")
        if inst.parameters:
            print(f"      parameters: {inst.parameters}")
    print()

# ---- Use read() with data modes ----
cells = parser.read("tests/sample.spi", data="cells")
print(f"Cell names (set): {cells}")

ports = parser.read("tests/sample.spi", data="ports")
print(f"Ports dict: {ports}")

devices = parser.read("tests/sample.spi", data="devices")
print(f"Devices dict: {devices}")

caps = parser.read("tests/sample.spi", data="capacitors")
print(f"Capacitors: {caps}")
