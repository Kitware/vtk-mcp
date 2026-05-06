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
    help="Path to the vtk-knowledge JSONL artifact.",
)
def main(transport: str, host: str, port: int, knowledge_artifact: str | None) -> None:
    """Run the VTK MCP gateway server."""
    import os
    from .config import Settings
    from .composition import init_context

    if knowledge_artifact:
        os.environ["VTK_MCP_KNOWLEDGE_ARTIFACT_PATH"] = knowledge_artifact

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
