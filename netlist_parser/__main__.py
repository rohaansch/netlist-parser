"""CLI entry point: python -m netlist_parser  or  netlist-parser (installed script)."""

import argparse
import sys

from .parser import NetlistParser, NetlistError
from . import __version__


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="netlist-parser",
        description="Parse a SPICE-family netlist file and print its content.",
        epilog=(
            "Examples:\n"
            "  netlist-parser sample.spi\n"
            "  netlist-parser sample.spi --cells\n"
            "  netlist-parser sample.spi --ports\n"
            "  netlist-parser sample.spi --devices\n"
            "  netlist-parser sample.spi --cell inv_x1\n"
            "  netlist-parser --version\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("path", nargs="?", help="Path to a netlist file")
    ap.add_argument(
        "--cells",
        action="store_true",
        help="Print cell names defined in the file",
    )
    ap.add_argument(
        "--ports",
        action="store_true",
        help="Print each cell and its port list",
    )
    ap.add_argument(
        "--devices",
        action="store_true",
        help="Print each cell and the device names it uses",
    )
    ap.add_argument(
        "--cell",
        metavar="NAME",
        help="Print detailed info for a specific cell",
    )
    ap.add_argument(
        "--version",
        action="store_true",
        help="Print package version and exit",
    )
    args = ap.parse_args()

    if args.version:
        print(__version__)
        return

    if not args.path:
        ap.error("the following arguments are required: path")

    parser = NetlistParser()
    try:
        netlist = parser.parse(args.path)
    except NetlistError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.cells:
        for cell in netlist.cells:
            print(cell.name)
        return

    if args.ports:
        for cell in netlist.cells:
            ports = " ".join(cell.ports)
            print(f"{cell.name}: {ports}")
        return

    if args.devices:
        for cell in netlist.cells:
            device_names = sorted(
                {inst.device_name for inst in cell.instances if inst.device_name}
            )
            print(f"{cell.name}: {', '.join(device_names)}")
        return

    if args.cell:
        target = args.cell
        for cell in netlist.cells:
            if cell.name == target:
                print(f"Cell: {cell.name}")
                print(f"  Ports: {' '.join(cell.ports)}")
                print(f"  Instances ({len(cell.instances)}):")
                for inst in cell.instances:
                    line = f"    {inst.name}  code={inst.code}"
                    if inst.device_name:
                        line += f"  device={inst.device_name}"
                    if inst.number:
                        line += f"  number={inst.number}"
                    if inst.nodes:
                        line += f"  nodes={inst.nodes}"
                    if inst.parameters:
                        line += f"  params={inst.parameters}"
                    print(line)
                return
        print(f"Error: cell '{target}' not found in {args.path}", file=sys.stderr)
        sys.exit(1)

    # Default: summary
    print(f"File:  {args.path}")
    print(f"Format: {netlist.version}")
    print(f"Cells ({len(netlist.cells)}):")
    for cell in netlist.cells:
        print(f"  {cell.name}  ports={len(cell.ports)}  instances={len(cell.instances)}")


if __name__ == "__main__":
    main()
