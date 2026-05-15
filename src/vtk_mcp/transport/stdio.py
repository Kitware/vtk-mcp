"""stdio transport entry point."""

from __future__ import annotations


def run() -> None:
    from ..server import mcp

    mcp.run()
