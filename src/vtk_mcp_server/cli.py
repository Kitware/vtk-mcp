#!/usr/bin/env python3

import argparse
import json
import sys

from .vtk_scraper import VTKClassScraper


class VTKDocumentationClient:
    """VTK documentation retrieval client"""

    def __init__(self, output_format="text"):
        self.scraper_engine = VTKClassScraper()
        self.output_format = output_format

    def get_class_info(self, class_identifier):
        """Retrieve VTK class documentation"""
        try:
            class_data = self.scraper_engine.get_class_info(class_identifier)
            if class_data:
                if self.output_format == "json":
                    self._display_json_output(
                        {
                            "tool": "get_vtk_class_info",
                            "arguments": {"class_name": class_identifier},
                            "result": class_data,
                        }
                    )
                else:
                    self._display_class_info(class_data)
            else:
                error_msg = f"Class '{class_identifier}' not found in VTK documentation"
                if self.output_format == "json":
                    self._display_json_output(
                        {
                            "tool": "get_vtk_class_info",
                            "arguments": {"class_name": class_identifier},
                            "error": error_msg,
                        }
                    )
                else:
                    print(error_msg)
        except Exception as retrieval_error:
            error_msg = f"Error retrieving class information: {retrieval_error}"
            if self.output_format == "json":
                self._display_json_output(
                    {
                        "tool": "get_vtk_class_info",
                        "arguments": {"class_name": class_identifier},
                        "error": error_msg,
                    }
                )
            else:
                print(error_msg)

    def search_classes(self, search_pattern):
        """Search VTK classes matching pattern"""
        try:
            matching_classes = self.scraper_engine.search_classes(search_pattern)
            if self.output_format == "json":
                self._display_json_output(
                    {
                        "tool": "search_vtk_classes",
                        "arguments": {"search_term": search_pattern},
                        "result": matching_classes,
                    }
                )
            elif matching_classes:
                print(
                    f"Found {len(matching_classes)} VTK classes "
                    f"matching '{search_pattern}':"
                )
                print()
                for class_idx, vtk_class in enumerate(matching_classes, 1):
                    print(f"{class_idx}. {vtk_class}")
                print()
                print(
                    "Use get_class_info with any class name for detailed information."
                )
            else:
                print(f"No VTK classes found matching '{search_pattern}'")
        except Exception as search_error:
            error_msg = f"Search error: {search_error}"
            if self.output_format == "json":
                self._display_json_output(
                    {
                        "tool": "search_vtk_classes",
                        "arguments": {"search_term": search_pattern},
                        "error": error_msg,
                    }
                )
            else:
                print(error_msg)

    def list_available_commands(self):
        """List available client commands"""
        if self.output_format == "json":
            self._display_json_output(
                {
                    "available_tools": [
                        {
                            "name": "get_vtk_class_info",
                            "description": "Retrieve detailed VTK class documentation",
                            "parameters": {
                                "class_name": {
                                    "type": "string",
                                    "description": "VTK class name to retrieve",
                                }
                            },
                        },
                        {
                            "name": "search_vtk_classes",
                            "description": "Search for VTK classes matching pattern",
                            "parameters": {
                                "search_term": {
                                    "type": "string",
                                    "description": (
                                        "Pattern to search for in class names"
                                    ),
                                }
                            },
                        },
                    ]
                }
            )
        else:
            print("Available commands:")
            print("=" * 50)
            print("• get_class_info")
            print("  Purpose: Retrieve detailed VTK class documentation")
            print("  Parameters:")
            print("    - class_identifier (str): VTK class name to retrieve")
            print()
            print("• search_classes")
            print("  Purpose: Search for VTK classes matching pattern")
            print("  Parameters:")
            print("    - search_pattern (str): Pattern to search for in class names")

    def _display_json_output(self, data):
        """Display data as formatted JSON"""
        print(json.dumps(data, indent=2))

    def _display_class_info(self, class_metadata):
        """Display VTK class information"""
        class_name = class_metadata["class_name"]
        print(f"VTK Class: {class_name}")
        print("=" * 60)
        print()

        if class_metadata.get("brief"):
            print(f"Brief: {class_metadata['brief']}")
            print()

        if class_metadata.get("detailed_description"):
            description = class_metadata["detailed_description"]
            if len(description) > 400:
                description = description[:400] + "..."
            print(f"Description: {description}")
            print()

        if class_metadata.get("inheritance"):
            print(
                f"Inheritance hierarchy "
                f"({len(class_metadata['inheritance'])} parent classes):"
            )
            for parent_class in class_metadata["inheritance"][:8]:
                print(f"  └─ {parent_class}")
            if len(class_metadata["inheritance"]) > 8:
                remaining_count = len(class_metadata["inheritance"]) - 8
                print(f"  └─ ... and {remaining_count} more parent classes")
            print()

        if class_metadata.get("methods"):
            print(f"Methods ({len(class_metadata['methods'])} available):")
            for method_idx, method_info in enumerate(class_metadata["methods"][:12], 1):
                method_name = method_info["name"]
                print(f"  {method_idx:2d}. {method_name}")
            if len(class_metadata["methods"]) > 12:
                remaining_methods = len(class_metadata["methods"]) - 12
                print(f"      ... and {remaining_methods} more methods")
            print()

        print(f"Documentation URL: {class_metadata['url']}")


def main():
    argument_parser = argparse.ArgumentParser(
        description="VTK MCP Client - VTK documentation retrieval tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  vtk-mcp-client vtkActor                    # Get vtkActor documentation
  vtk-mcp-client --search Actor             # Search for classes containing 'Actor'
  vtk-mcp-client --search Camera            # Search for classes containing 'Camera'
  vtk-mcp-client --list                     # List available commands
  vtk-mcp-client PolyData                   # Get vtkPolyData (auto-prefix vtk)
  vtk-mcp-client vtkActor --json             # Get vtkActor in JSON format
  vtk-mcp-client --search Actor --json      # Search in JSON format
        """,
    )

    command_group = argument_parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument(
        "class_name",
        nargs="?",
        help="VTK class name to retrieve documentation for",
    )
    command_group.add_argument(
        "--search",
        "-s",
        metavar="PATTERN",
        help="Search for VTK classes matching pattern",
    )
    command_group.add_argument(
        "--list", "-l", action="store_true", help="List available commands"
    )

    argument_parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results in JSON format (MCP server format)",
    )

    parsed_args = argument_parser.parse_args()

    # Initialize documentation client
    output_format = "json" if parsed_args.json else "text"
    vtk_client = VTKDocumentationClient(output_format)

    try:
        if parsed_args.list:
            vtk_client.list_available_commands()
        elif parsed_args.search:
            if not parsed_args.json:
                print(f"Searching for pattern '{parsed_args.search}'...")
                print()
            vtk_client.search_classes(parsed_args.search)
        elif parsed_args.class_name:
            if not parsed_args.json:
                print(f"Retrieving documentation for '{parsed_args.class_name}'...")
                print()
            vtk_client.get_class_info(parsed_args.class_name)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as client_error:
        print(f"Client error: {client_error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
