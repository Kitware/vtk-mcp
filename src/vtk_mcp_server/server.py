#!/usr/bin/env python3

import asyncio
import click
from fastmcp import FastMCP
from .vtk_scraper import VTKClassScraper

# Initialize
mcp = FastMCP("VTK MCP Server")
scraper = VTKClassScraper()


@mcp.tool()
def get_vtk_class_info(class_name: str) -> str:
    """Get detailed information about a VTK class from the online documentation."""
    if not class_name:
        return "Error: class_name is required"

    try:
        info = scraper.get_class_info(class_name)
        if info is None:
            return f"Class '{class_name}' not found in VTK documentation."
        return _format_class_info(info)
    except Exception as e:
        return f"Error retrieving class '{class_name}': {str(e)}"


@mcp.tool()
def search_vtk_classes(search_term: str) -> str:
    """Search for VTK classes containing a specific term."""
    if not search_term:
        return "Error: search_term is required"

    try:
        matches = scraper.search_classes(search_term)
        if not matches:
            return f"No VTK classes found containing '{search_term}'"

        response = f"VTK classes containing '{search_term}':\n\n"
        response += "\n".join(f"{i}. {cls}" for i, cls in enumerate(matches, 1))
        response += f"\n\nFound {len(matches)} classes."
        return response
    except Exception as e:
        return f"Error searching for '{search_term}': {str(e)}"


def _format_class_info(info):
    """Format class info into readable markdown."""
    lines = [f"# {info['class_name']}", ""]

    for section, title in [
        ("brief", "## Brief Description"),
        ("detailed_description", "## Detailed Description"),
    ]:
        if info.get(section):
            lines.extend([title, info[section], ""])

    if info.get("inheritance"):
        lines.append("## Inheritance Hierarchy")
        lines.extend(f"- {cls}" for cls in info["inheritance"])
        lines.append("")

    if info.get("methods"):
        lines.append("## Public Methods")
        methods = info["methods"][:10]  # Show first 10
        lines.extend(
            f"- **{m['name']}**: {m.get('description', 'No description')}"
            for m in methods
        )
        if len(info["methods"]) > 10:
            lines.append(f"- ... and {len(info['methods']) - 10} more methods")
        lines.append("")

    lines.extend(["## Documentation URL", info["url"]])
    return "\n".join(lines)


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport protocol",
)
@click.option("--host", default="127.0.0.1", help="Host (HTTP only)")
@click.option("--port", default=8000, type=int, help="Port (HTTP only)")
def main(transport, host, port):
    """Run the VTK MCP Server"""
    if transport == "http":
        click.echo(f"Starting VTK MCP Server on http://{host}:{port}")
        asyncio.run(mcp.run_http_async(host=host, port=port))
    else:
        click.echo("Starting VTK MCP Server on stdio transport")
        mcp.run()


if __name__ == "__main__":
    main()
