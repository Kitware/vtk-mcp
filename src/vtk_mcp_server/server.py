#!/usr/bin/env python3

import asyncio
import click
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from fastmcp import FastMCP
from .vtk_scraper import VTKClassScraper

# Initialize
mcp = FastMCP("VTK MCP Server")
scraper = VTKClassScraper()

# Global database path (set via CLI)
_database_path = None


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


@mcp.tool()
def vector_search_vtk_examples(
    query: str,
    collection_name: str = "vtk-examples",
    top_k: int = 5,
) -> str:
    """Search VTK examples using vector similarity search with RAG.

    This function performs semantic search over VTK code examples using embeddings
    and returns the most relevant code snippets and documentation.

    Args:
        query: The search query describing what you're looking for
        collection_name: Name of the collection in the database
            (default: vtk-examples)
        top_k: Number of top results to return (default: 5)

    Returns:
        Formatted string with code snippets, documentation, and relevance scores
    """
    if not query:
        return "Error: query is required"

    if not _database_path:
        return (
            "Error: Database path not configured. "
            "Start the server with --database-path option."
        )

    try:
        # Check dependencies
        import importlib.util

        required_modules = ["chromadb", "sentence_transformers"]
        missing_modules = [
            module
            for module in required_modules
            if importlib.util.find_spec(module) is None
        ]

        if missing_modules:
            return (
                f"Error: Missing required dependencies: {', '.join(missing_modules)}\n"
                "Install with: pip install chromadb sentence-transformers\n\n"
                "Or ensure the rag-components submodule is initialized:\n"
                "git submodule update --init --recursive"
            )

        # Setup path and import
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent
        rag_path = str(project_root / "rag-components")

        if rag_path not in sys.path:
            sys.path.insert(0, rag_path)

        from query_db import query_db, initialize_db

        # Initialize database client with configured path
        client = initialize_db(_database_path)

        # Perform vector search with reranking
        results = query_db(
            query=query, collection_name=collection_name, top_k=top_k, client=client
        )

        # Format results
        return _format_vector_search_results(query, results, top_k)

    except Exception as e:
        return f"Error performing vector search: {str(e)}"


def _format_vector_search_results(query, results, top_k):
    """Format vector search results into readable markdown."""
    lines = [
        f"# Vector Search Results for: {query}",
        "",
        f"Found {top_k} most relevant code examples and documentation snippets.",
        "",
    ]

    # Format code results
    if results["code_documents"]:
        lines.append("## Code Examples")
        lines.append("")

        for i, (document, metadata, score) in enumerate(
            zip(
                results["code_documents"],
                results["code_metadata"],
                results["code_scores"],
            ),
            1,
        ):
            lines.append(f"### Result {i} (Relevance: {score:.4f})")
            lines.append("")

            # Add metadata if available
            if metadata:
                source = metadata.get("source", "Unknown")
                lines.append(f"**Source:** {source}")
                lines.append("")

            # Add code snippet
            lines.append("```python")
            lines.append(document.strip())
            lines.append("```")
            lines.append("")

    # Format text/documentation results
    if results["text_documents"]:
        lines.append("## Documentation Snippets")
        lines.append("")

        for i, (document, metadata, score) in enumerate(
            zip(
                results["text_documents"],
                results["text_metadata"],
                results["text_scores"],
            ),
            1,
        ):
            lines.append(f"### Snippet {i} (Relevance: {score:.4f})")
            lines.append("")

            # Add metadata if available
            if metadata:
                source = metadata.get("source", "Unknown")
                lines.append(f"**Source:** {source}")
                lines.append("")

            # Add text content
            lines.append(document.strip())
            lines.append("")

    return "\n".join(lines)


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
@click.option(
    "--database-path",
    type=click.Path(exists=True),
    help="Path to the RAG database (required for vector search)",
)
def main(transport, host, port, database_path):
    """Run the VTK MCP Server"""
    global _database_path

    # Set global database path if provided
    if database_path:
        _database_path = database_path
        click.echo(f"Database path configured: {database_path}")

    if transport == "http":
        click.echo(f"Starting VTK MCP Server on http://{host}:{port}")
        asyncio.run(mcp.run_http_async(host=host, port=port))
    else:
        click.echo("Starting VTK MCP Server on stdio transport")
        mcp.run()


if __name__ == "__main__":
    main()
