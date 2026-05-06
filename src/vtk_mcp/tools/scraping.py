"""C++ VTK documentation scraping tools.

These are the only tools in the gateway that own domain logic directly.
They will eventually be replaced by a vtk-knowledge-cpp artifact.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def get_vtk_class_info_cpp(class_name: str, ctx: "VTKMCPContext") -> str:
    """Get detailed VTK class information from the online C++ docs."""
    if not ctx.settings.enable_cpp_scraping:
        return "C++ scraping disabled (VTK_MCP_ENABLE_CPP_SCRAPING=false)."
    from .vtk_scraper import VTKClassScraper
    scraper = VTKClassScraper()
    info = scraper.get_class_info(class_name)
    if info is None:
        return f"Class '{class_name}' not found in VTK C++ documentation."
    return _format_cpp_info(info)


def search_vtk_classes_cpp(search_term: str, ctx: "VTKMCPContext") -> str:
    """Search VTK class names in the C++ docs."""
    if not ctx.settings.enable_cpp_scraping:
        return "C++ scraping disabled (VTK_MCP_ENABLE_CPP_SCRAPING=false)."
    from .vtk_scraper import VTKClassScraper
    scraper = VTKClassScraper()
    matches = scraper.search_classes(search_term)
    if not matches:
        return f"No VTK classes found containing '{search_term}'."
    return "\n".join(f"{i}. {cls}" for i, cls in enumerate(matches, 1))


def _format_cpp_info(info: dict[str, Any]) -> str:
    lines = [f"# {info.get('class_name', '')}"]
    for section, title in [
        ("brief", "## Brief"),
        ("detailed_description", "## Description"),
    ]:
        if info.get(section):
            lines += [title, info[section], ""]
    if info.get("methods"):
        lines.append("## Methods")
        for m in info["methods"][:10]:
            lines.append(f"- **{m['name']}**: {m.get('description', '')}")
    if info.get("url"):
        lines += ["", f"## Docs\n{info['url']}"]
    return "\n".join(lines)
