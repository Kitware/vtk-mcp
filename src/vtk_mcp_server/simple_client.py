#!/usr/bin/env python3

import json
import sys
import click
import requests


class SimpleVTKClient:
    """HTTP client for VTK MCP server"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self._initialize_session()

    def _initialize_session(self):
        """Initialize MCP session with handshake"""
        try:
            # Initialize
            payload = {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": "vtk-mcp-client",
                        "version": "1.0.0"
                    },
                },
            }
            response = self._make_request(payload)
            if not response:
                return

            self.session_id = response.headers.get("Mcp-Session-Id")

            # Send initialized notification
            self._make_request(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                }
            )
        except Exception as e:
            print(f"Session initialization failed: {e}")

    def _make_request(self, payload):
        """Make HTTP request with proper headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        try:
            response = requests.post(
                f"{self.base_url}/mcp/", json=payload, headers=headers
            )
            if response.status_code != 200:
                print(f"HTTP {response.status_code}: {response.text}")
                return None
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def _parse_response(self, response):
        """Parse SSE response and extract result"""
        try:
            for line in response.text.strip().split("\n"):
                if line.startswith("data: "):
                    return json.loads(line[6:])  # Remove 'data: ' prefix
        except Exception as e:
            print(f"Parse error: {e}")
        return None

    def _handle_tool_response(self, result):
        """Handle tool response and print result"""
        if result and "result" in result and "content" in result["result"]:
            print(result["result"]["content"][0]["text"])
        elif result and "error" in result:
            print(f"Error: {result['error']['message']}")
        else:
            print("Unexpected response format")

    def get_class_info(self, class_name):
        """Get VTK class information"""
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": "get_vtk_class_info",
                "arguments": {"class_name": class_name},
            },
        }
        response = self._make_request(payload)
        if response:
            result = self._parse_response(response)
            self._handle_tool_response(result)

    def search_classes(self, search_term):
        """Search VTK classes"""
        payload = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/call",
            "params": {
                "name": "search_vtk_classes",
                "arguments": {"search_term": search_term},
            },
        }
        response = self._make_request(payload)
        if response:
            result = self._parse_response(response)
            self._handle_tool_response(result)

    def get_python_help(self, class_name):
        """Get VTK Python API help"""
        payload = {
            "jsonrpc": "2.0",
            "id": "3",
            "method": "tools/call",
            "params": {
                "name": "get_vtk_python_help",
                "arguments": {"class_name": class_name},
            },
        }
        response = self._make_request(payload)
        if response:
            result = self._parse_response(response)
            self._handle_tool_response(result)

    def list_tools(self):
        """List available MCP tools"""
        payload = {"jsonrpc": "2.0", "id": "3", "method": "tools/list"}
        response = self._make_request(payload)
        if not response:
            return

        result = self._parse_response(response)
        if result and "result" in result and "tools" in result["result"]:
            print("Available commands:")
            print("=" * 50)
            for tool in result["result"]["tools"]:
                print(f"• {tool['name']}")
                print(f"  Description: {tool['description']}")
                schema = tool.get("inputSchema", {})
                if "properties" in schema:
                    print("  Parameters:")
                    for name, info in schema["properties"].items():
                        desc = info["description"]
                        print(f"    - {name} ({info['type']}): {desc}")
                print()
        elif result and "error" in result:
            print(f"Error: {result['error']['message']}")
        else:
            print("Unexpected response format")


@click.group(invoke_without_command=True)
@click.option("--host", default="localhost", help="Server host")
@click.option("--port", default=8000, help="Server port")
@click.pass_context
def cli(ctx, host, port):
    """VTK MCP Client - Get VTK class information from documentation"""
    ctx.ensure_object(dict)
    base_url = f"http://{host}:{port}"
    ctx.obj["client"] = SimpleVTKClient(base_url=base_url)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("class_name")
@click.pass_context
def info(ctx, class_name):
    """Get detailed information about a VTK class"""
    client = ctx.obj["client"]
    click.echo(f"Getting information for VTK class '{class_name}'...")
    click.echo()
    client.get_class_info(class_name)


@cli.command()
@click.argument("search_term")
@click.pass_context
def search(ctx, search_term):
    """Search for VTK classes containing a specific term"""
    client = ctx.obj["client"]
    click.echo(f"Searching for VTK classes containing '{search_term}'...")
    click.echo()
    client.search_classes(search_term)


@cli.command()
@click.argument("class_name")
@click.pass_context
def python_help(ctx, class_name):
    """Get Python API documentation for a VTK class"""
    client = ctx.obj["client"]
    click.echo(f"Getting Python API help for VTK class '{class_name}'...")
    click.echo()
    client.get_python_help(class_name)


@cli.command()
@click.pass_context
def list_tools(ctx):
    """List available tools"""
    client = ctx.obj["client"]
    client.list_tools()


def main():
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
