"""vtk-mcp HTTP client CLI.

Talks to a running vtk-mcp HTTP server and exposes all MCP tools as
subcommands.  Designed for quick inspection from the terminal; not a
general-purpose MCP client.
"""

from __future__ import annotations

import json
import sys

import click
import requests

# ── Transport ──────────────────────────────────────────────────────────────


class _Client:
    def __init__(self, host: str, port: int) -> None:
        self._base = f"http://{host}:{port}"
        self._session_id: str | None = None
        self._req_id = 0
        self._init()

    def _init(self) -> None:
        resp = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "vtk-mcp-client", "version": "1.0.0"},
                },
            }
        )
        if resp:
            self._session_id = resp.headers.get("Mcp-Session-Id")
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _post(self, payload: dict) -> requests.Response | None:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        try:
            r = requests.post(f"{self._base}/mcp", json=payload, headers=headers, timeout=30)
            if r.status_code not in (200, 202):
                click.echo(f"HTTP {r.status_code}: {r.text}", err=True)
                return None
            return r
        except requests.exceptions.ConnectionError:
            click.echo(f"Cannot connect to {self._base}. Is the server running?", err=True)
            sys.exit(1)

    def _sse_result(self, resp: requests.Response | None):
        if resp is None:
            return None
        for line in resp.text.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        return None

    def call(self, tool: str, **args) -> object:
        resp = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {"name": tool, "arguments": {k: v for k, v in args.items() if v is not None}},
            }
        )
        msg = self._sse_result(resp)
        if msg is None:
            return None
        if "error" in msg:
            click.echo(f"Error: {msg['error']['message']}", err=True)
            return None
        content = msg.get("result", {}).get("content", [])
        if content:
            return json.loads(content[0]["text"])
        return None

    def list_tools(self) -> list:
        resp = self._post({"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list"})
        msg = self._sse_result(resp)
        if msg and "result" in msg:
            return msg["result"].get("tools", [])
        return []


# ── Formatting helpers ─────────────────────────────────────────────────────


def _print_json(obj: object) -> None:
    click.echo(json.dumps(obj, indent=2))


def _print_methods(methods: list, limit: int = 20) -> None:
    for i, m in enumerate(methods[:limit], 1):
        sigs = m.get("signatures") or []
        sig = sigs[0] if sigs else m.get("name", "")
        click.echo(f"  {i:3d}. {sig}")
    if len(methods) > limit:
        click.echo(f"       … {len(methods) - limit} more")


# ── CLI skeleton ───────────────────────────────────────────────────────────


@click.group()
@click.option("--host", default="localhost", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--json", "as_json", is_flag=True, help="Raw JSON output")
@click.pass_context
def cli(ctx: click.Context, host: str, port: int, as_json: bool) -> None:
    """VTK MCP client — talks to a running vtk-mcp HTTP server."""
    ctx.ensure_object(dict)
    ctx.obj["client"] = _Client(host, port)
    ctx.obj["json"] = as_json


# ── Knowledge lookup ───────────────────────────────────────────────────────


@cli.command()
@click.argument("class_name")
@click.pass_context
def info(ctx: click.Context, class_name: str) -> None:
    """Full class record (all fields)."""
    r = ctx.obj["client"].call("vtk_get_class_info", class_name=class_name)
    if r is None:
        return
    if ctx.obj["json"]:
        _print_json(r)
        return
    click.echo(f"Class:      {r.get('class_name')}")
    click.echo(f"Module:     {r.get('module_name')}")
    click.echo(f"Role:       {r.get('role')}")
    click.echo(f"Synopsis:   {r.get('synopsis') or '—'}")
    click.echo(f"Action:     {r.get('action_phrase') or '—'}")
    click.echo(f"Visibility: {r.get('visibility_score')}")
    click.echo(f"Input:      {r.get('input_datatype') or '—'}")
    click.echo(f"Output:     {r.get('output_datatype') or '—'}")
    inh = r.get("inheritance") or []
    if inh:
        click.echo(f"MRO:        {' → '.join(inh[:6])}{'…' if len(inh) > 6 else ''}")
    methods = r.get("methods") or []
    click.echo(f"\nMethods ({len(methods)}):")
    _print_methods(methods)


@cli.command()
@click.argument("query")
@click.option("--limit", "-n", default=10, show_default=True)
@click.pass_context
def search(ctx: click.Context, query: str, limit: int) -> None:
    """Search classes by name or keyword."""
    results = ctx.obj["client"].call("vtk_search_classes", query=query, limit=limit)
    if results is None:
        return
    if ctx.obj["json"]:
        _print_json(results)
        return
    for r in results:
        click.echo(f"  {r['class_name']:<40} {r.get('synopsis') or ''}")


@cli.command()
@click.argument("class_name")
@click.pass_context
def doc(ctx: click.Context, class_name: str) -> None:
    """Class docstring."""
    r = ctx.obj["client"].call("vtk_get_class_doc", class_name=class_name)
    click.echo(r or "")


@cli.command()
@click.argument("class_name")
@click.pass_context
def synopsis(ctx: click.Context, class_name: str) -> None:
    """One-sentence synopsis (LLM-generated)."""
    click.echo(ctx.obj["client"].call("vtk_get_class_synopsis", class_name=class_name) or "")


@cli.command()
@click.argument("class_name")
@click.pass_context
def role(ctx: click.Context, class_name: str) -> None:
    """Pipeline role (source / filter / mapper / …)."""
    click.echo(ctx.obj["client"].call("vtk_get_class_role", class_name=class_name) or "")


@cli.command()
@click.argument("class_name")
@click.pass_context
def inheritance(ctx: click.Context, class_name: str) -> None:
    """Full MRO chain."""
    r = ctx.obj["client"].call("vtk_get_class_inheritance", class_name=class_name) or []
    if ctx.obj["json"]:
        _print_json(r)
        return
    for i, cls in enumerate(r):
        click.echo(f"  {'└─' if i else '  '} {cls}")


@cli.command()
@click.argument("class_name")
@click.pass_context
def methods(ctx: click.Context, class_name: str) -> None:
    """All methods with signatures."""
    r = ctx.obj["client"].call("vtk_get_class_methods", class_name=class_name) or []
    if ctx.obj["json"]:
        _print_json(r)
        return
    click.echo(f"{len(r)} methods:")
    _print_methods(r, limit=len(r))


@cli.command("semantic-methods")
@click.argument("class_name")
@click.pass_context
def semantic_methods(ctx: click.Context, class_name: str) -> None:
    """Non-inherited (semantic) methods only."""
    r = ctx.obj["client"].call("vtk_get_class_semantic_methods", class_name=class_name) or []
    if ctx.obj["json"]:
        _print_json(r)
        return
    for m in r:
        click.echo(f"  {m}")


@cli.command()
@click.argument("class_name")
@click.argument("method_name")
@click.pass_context
def method(ctx: click.Context, class_name: str, method_name: str) -> None:
    """Info for a specific method."""
    r = ctx.obj["client"].call("vtk_get_method_info", class_name=class_name, method_name=method_name)
    if r is None:
        return
    if ctx.obj["json"]:
        _print_json(r)
        return
    for sig in r.get("signatures") or []:
        click.echo(sig)
    if r.get("doc"):
        click.echo(f"\n{r['doc']}")


@cli.command()
@click.argument("class_name")
@click.pass_context
def module(ctx: click.Context, class_name: str) -> None:
    """vtkmodules.* import path."""
    click.echo(ctx.obj["client"].call("vtk_get_class_module", class_name=class_name) or "")


@cli.command("module-classes")
@click.argument("module_name")
@click.pass_context
def module_classes(ctx: click.Context, module_name: str) -> None:
    """All classes in a module."""
    r = ctx.obj["client"].call("vtk_get_module_classes", module=module_name) or []
    if ctx.obj["json"]:
        _print_json(r)
        return
    for cls in r:
        click.echo(f"  {cls}")


@cli.command()
@click.argument("class_name")
@click.pass_context
def metadata(ctx: click.Context, class_name: str) -> None:
    """Record metadata: vtk_version, schema_version, content_hash."""
    r = ctx.obj["client"].call("vtk_get_class_record_metadata", class_name=class_name)
    if r is None:
        return
    if ctx.obj["json"]:
        _print_json(r)
        return
    for k, v in r.items():
        click.echo(f"  {k}: {v}")


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """VTK version and enabled features."""
    r = ctx.obj["client"].call("vtk_version_info")
    if r is None:
        return
    if ctx.obj["json"]:
        _print_json(r)
        return
    for k, v in r.items():
        click.echo(f"  {k}: {v}")


# ── Semantic search ────────────────────────────────────────────────────────


@cli.command("search-docs")
@click.argument("query")
@click.option("-n", "--top", default=5, show_default=True, type=int)
@click.option("--role", "role_filter", default=None)
@click.option("--class", "class_filter", default=None)
@click.option("--min-visibility", default=None, type=float)
@click.pass_context
def search_docs(
    ctx: click.Context,
    query: str,
    top: int,
    role_filter: str | None,
    class_filter: str | None,
    min_visibility: float | None,
) -> None:
    """Hybrid semantic search over VTK documentation chunks."""
    r = ctx.obj["client"].call(
        "vector_search_docs",
        query=query,
        k=top,
        role=role_filter,
        class_name=class_filter,
        min_visibility=min_visibility,
    )
    _print_search_results(r, ctx.obj["json"])


@cli.command("search-examples")
@click.argument("query")
@click.option("-n", "--top", default=5, show_default=True, type=int)
@click.option("--role", "role_filter", default=None)
@click.option("--class", "class_filter", default=None)
@click.option("--min-visibility", default=None, type=float)
@click.pass_context
def search_examples(
    ctx: click.Context,
    query: str,
    top: int,
    role_filter: str | None,
    class_filter: str | None,
    min_visibility: float | None,
) -> None:
    """Hybrid semantic search over VTK code example chunks."""
    r = ctx.obj["client"].call(
        "vector_search_examples",
        query=query,
        k=top,
        role=role_filter,
        class_name=class_filter,
        min_visibility=min_visibility,
    )
    _print_search_results(r, ctx.obj["json"])


def _print_search_results(results: object, as_json: bool) -> None:
    if results is None:
        return
    if as_json:
        _print_json(results)
        return
    if isinstance(results, list) and results and "error" in results[0]:
        click.echo(results[0]["error"], err=True)
        return
    for i, chunk in enumerate(results or [], 1):
        classes = ", ".join(chunk.get("class_names") or [])
        click.echo(f"\n[{i}] {classes or '—'} | role={chunk.get('role')} | score={chunk.get('visibility_score')}")
        content = chunk.get("content", "")
        click.echo(f"    {content[:200]}{'…' if len(content) > 200 else ''}")


# ── Validation ─────────────────────────────────────────────────────────────


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.pass_context
def validate(ctx: click.Context, source: str) -> None:
    """Validate a Python source file against the VTK API."""
    code = open(source).read()
    r = ctx.obj["client"].call("validate_vtk_code", source=code)
    if r is None:
        return
    if ctx.obj["json"]:
        _print_json(r)
        return
    status = r.get("status", "?")
    click.echo(f"Status: {status}  ({r.get('elapsed_ms', 0):.1f} ms)")
    for d in r.get("diagnostics") or []:
        click.echo(f"  [{d.get('error_type')}] line {d.get('line')}: {d.get('message')}")


@cli.command("validate-import")
@click.argument("import_statement")
@click.pass_context
def validate_import(ctx: click.Context, import_statement: str) -> None:
    """Validate a single VTK import statement."""
    r = ctx.obj["client"].call("vtk_validate_import", import_statement=import_statement)
    if r is None:
        return
    if ctx.obj["json"]:
        _print_json(r)
        return
    click.echo("valid" if r.get("valid") else "invalid")
    for d in r.get("diagnostics") or []:
        click.echo(f"  {d.get('message')}")


# ── Meta ───────────────────────────────────────────────────────────────────


@cli.command("list-tools")
@click.pass_context
def list_tools(ctx: click.Context) -> None:
    """List all tools exposed by the server."""
    tools = ctx.obj["client"].list_tools()
    if ctx.obj["json"]:
        _print_json(tools)
        return
    for t in tools:
        click.echo(f"  {t['name']:<45} {t.get('description', '')}")


def main() -> None:
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nCancelled.", err=True)
        sys.exit(1)
