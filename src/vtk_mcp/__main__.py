"""vtk-mcp entry point: ``python -m vtk_mcp``."""

import click


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    show_default=True,
    help="Transport protocol.",
)
@click.option("--host", default="0.0.0.0", show_default=True, help="HTTP host.")
@click.option("--port", default=8000, show_default=True, help="HTTP port.")
@click.option(
    "--knowledge-artifact",
    envvar="VTK_MCP_KNOWLEDGE_ARTIFACT_PATH",
    type=click.Path(exists=True),
    help="Path to a local vtk-knowledge JSONL artifact (skips auto-download).",
)
@click.option(
    "--vtk-version",
    envvar="VTK_MCP_VTK_VERSION",
    default="9.3.0",
    show_default=True,
    help="VTK version to fetch from ghcr.io when no local artifact is given.",
)
def main(
    transport: str,
    host: str,
    port: int,
    knowledge_artifact: str | None,
    vtk_version: str,
) -> None:
    """Run the VTK MCP gateway server."""
    import os

    from .composition import init_context
    from .config import Settings

    if knowledge_artifact:
        os.environ["VTK_MCP_KNOWLEDGE_ARTIFACT_PATH"] = knowledge_artifact
    os.environ.setdefault("VTK_MCP_VTK_VERSION", vtk_version)

    settings = Settings()
    init_context(settings)

    if transport == "http":
        click.echo(f"Starting vtk-mcp on http://{host}:{port}")
        from .transport.http import run

        run(host=host, port=port)
    else:
        from .transport.stdio import run

        run()


if __name__ == "__main__":
    main()
