"""Utility helpers for netlist_parser."""

import sys

try:
    from termcolor import colored as _colored

    def colored(text: str, color: str) -> str:  # type: ignore[misc]
        return _colored(text, color)

except ImportError:  # pragma: no cover
    def colored(text: str, color: str) -> str:  # type: ignore[misc]  # noqa: F811
        return text


def warning(message: str) -> None:
    """Print a warning message to stderr."""
    print(colored(message, "yellow"), file=sys.stderr)
