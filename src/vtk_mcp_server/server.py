#!/usr/bin/env python3

import asyncio
import click
import io
from contextlib import redirect_stdout
from fastmcp import FastMCP
from .vtk_scraper import VTKClassScraper

# Initialize
mcp = FastMCP("VTK MCP Server")
scraper = VTKClassScraper()


@mcp.tool()
def get_vtk_class_info_cpp(class_name: str) -> str:
    """Get detailed information about a VTK class from online C++ docs."""
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


@mcp.tool()
def get_vtk_class_info_python(class_name: str) -> str:
    """Get Python API documentation for a VTK class using help()."""
    if not class_name:
        return "Error: class_name is required"

    try:
        # Import vtk module
        import vtk

        # Ensure class name starts with 'vtk'
        if not class_name.startswith("vtk"):
            class_name = f"vtk{class_name}"

        # Get the class from vtk module
        if not hasattr(vtk, class_name):
            return f"Class '{class_name}' not found in VTK Python API."

        vtk_class = getattr(vtk, class_name)

        # Capture help() output
        help_output = io.StringIO()
        with redirect_stdout(help_output):
            help(vtk_class)

        help_text = help_output.getvalue()

        if not help_text:
            return f"No help documentation available for '{class_name}'"

        # Format the output nicely
        return (
            f"# Python API Documentation for {class_name}\n\n" f"```\n{help_text}\n```"
        )

    except ImportError:
        return (
            "Error: VTK Python package is not installed. "
            "Install with 'pip install vtk'"
        )
    except Exception as e:
        return f"Error getting Python help for '{class_name}': {str(e)}"


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
