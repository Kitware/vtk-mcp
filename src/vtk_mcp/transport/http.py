"""HTTP transport entry point."""

from __future__ import annotations

import asyncio


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    from ..server import mcp
    asyncio.run(mcp.run_http_async(host=host, port=port))
