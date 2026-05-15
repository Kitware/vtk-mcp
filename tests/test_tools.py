"""Unit tests for all vtk_mcp tool functions.

Each tool is tested via its function in vtk_mcp.tools.*, using a VTKMCPContext
built from a minimal in-memory VTKAPIIndex so no network or external process
is needed.
"""

import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit


# ── Fixtures ───────────────────────────────────────────────────────────────


def _make_record(**kwargs):
    """Build a VTKDocRecord with sensible defaults."""
    from vtk_knowledge.schema.records import VTKDocRecord, VTKMethod, VTKRole

    defaults = dict(
        class_name="vtkSphereSource",
        module_name="vtkmodules.vtkFiltersSources",
        class_doc="Produces a polygonal sphere.",
        role=VTKRole.SOURCE,
        input_datatype=None,
        output_datatype="vtkPolyData",
        methods=[
            VTKMethod(name="SetRadius", signatures=["SetRadius(radius: float) -> None"], doc="Set sphere radius."),
            VTKMethod(name="GetRadius", signatures=["GetRadius() -> float"], doc="Get sphere radius."),
            VTKMethod(name="SetCenter", signatures=["SetCenter(x, y, z) -> None"], doc="Set center point."),
        ],
        semantic_methods=["SetRadius", "GetRadius", "SetCenter", "SetThetaResolution"],
        inheritance=["vtkSphereSource", "vtkPolyDataAlgorithm", "vtkAlgorithm", "vtkObject"],
        synopsis="Generates a polygonal sphere with configurable resolution.",
        action_phrase="sphere generation",
        visibility_score=0.92,
        vtk_version="9.6.1",
        content_hash="abc123",
    )
    defaults.update(kwargs)
    return VTKDocRecord(**defaults)


@pytest.fixture()
def ctx():
    """A VTKMCPContext with one class loaded, no retriever, validation enabled."""
    from vtk_knowledge import VTKAPIIndex
    from vtk_mcp.composition import VTKMCPContext
    from vtk_mcp.config import Settings

    record = _make_record()
    api_index = VTKAPIIndex([record])

    settings = Settings(
        knowledge_artifact_path=None,
        enable_validation=True,
    )

    context = object.__new__(VTKMCPContext)
    context.settings = settings
    context.api_index = api_index
    context.retriever = None

    from vtk_validate import validate as _validate

    context.validate = lambda source: _validate(source, api_index)
    return context


@pytest.fixture()
def ctx_with_retriever(ctx):
    """Same context but with a mock Retriever attached.

    Uses a plain MagicMock for chunks so vtk_index is not required.
    """
    chunk = MagicMock()
    chunk.model_dump.return_value = {
        "chunk_id": "c1",
        "chunk_type": "class_overview",
        "content": "vtkSphereSource produces a polygonal sphere.",
        "class_names": ["vtkSphereSource"],
        "module_names": ["vtkmodules.vtkFiltersSources"],
        "role": "source",
        "visibility_score": 0.92,
        "source": "docs",
        "source_path": "",
        "vtk_version": "9.6.1",
    }
    retriever = MagicMock()
    retriever.search_docs.return_value = [chunk]
    retriever.search_code.return_value = [chunk]
    ctx.retriever = retriever
    return ctx


# ── docs tools ────────────────────────────────────────────────────────────


class TestDocTools:
    def test_get_class_info_found(self, ctx):
        from vtk_mcp.tools.docs import get_vtk_class_info_python as f

        r = f("vtkSphereSource", ctx)
        assert r["class_name"] == "vtkSphereSource"
        assert r["module_name"] == "vtkmodules.vtkFiltersSources"

    def test_get_class_info_not_found(self, ctx):
        from vtk_mcp.tools.docs import get_vtk_class_info_python as f

        r = f("vtkDoesNotExist", ctx)
        assert "error" in r

    def test_search_classes(self, ctx):
        from vtk_mcp.tools.docs import vtk_search_classes as f

        r = f("Sphere", ctx, limit=5)
        assert any(item["class_name"] == "vtkSphereSource" for item in r)

    def test_search_classes_no_match(self, ctx):
        from vtk_mcp.tools.docs import vtk_search_classes as f

        assert f("ZZZNotAClass", ctx) == []

    def test_get_class_doc(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_doc as f

        assert "polygonal sphere" in f("vtkSphereSource", ctx)

    def test_get_class_doc_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_doc as f

        assert f("vtkMissing", ctx) == ""

    def test_get_class_synopsis(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_synopsis as f

        assert "sphere" in f("vtkSphereSource", ctx).lower()

    def test_get_class_role(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_role as f

        assert f("vtkSphereSource", ctx) == "source"

    def test_get_class_role_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_role as f

        assert f("vtkMissing", ctx) == "unknown"

    def test_get_class_input_datatype(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_input_datatype as f

        assert f("vtkSphereSource", ctx) == ""  # None → ""

    def test_get_class_output_datatype(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_output_datatype as f

        assert f("vtkSphereSource", ctx) == "vtkPolyData"

    def test_get_class_methods(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_methods as f

        r = f("vtkSphereSource", ctx)
        assert len(r) == 3
        names = [m["name"] for m in r]
        assert "SetRadius" in names

    def test_get_class_methods_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_methods as f

        assert f("vtkMissing", ctx) == []

    def test_get_class_semantic_methods(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_semantic_methods as f

        r = f("vtkSphereSource", ctx)
        assert "SetRadius" in r

    def test_get_method_info_found(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_method_info as f

        r = f("vtkSphereSource", "SetRadius", ctx)
        assert r["name"] == "SetRadius"
        assert "float" in r["signatures"][0]

    def test_get_method_info_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_method_info as f

        r = f("vtkSphereSource", "NonExistent", ctx)
        assert "error" in r

    def test_get_method_doc(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_method_doc as f

        assert "radius" in f("vtkSphereSource", "SetRadius", ctx).lower()

    def test_get_method_signature(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_method_signature as f

        sig = f("vtkSphereSource", "SetRadius", ctx)
        assert "SetRadius" in sig

    def test_get_class_module(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_module as f

        assert f("vtkSphereSource", ctx) == "vtkmodules.vtkFiltersSources"

    def test_get_module_classes(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_module_classes as f

        r = f("vtkmodules.vtkFiltersSources", ctx)
        assert "vtkSphereSource" in r

    def test_get_module_classes_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_module_classes as f

        assert f("vtkmodules.vtkMissing", ctx) == []

    def test_is_a_class_true(self, ctx):
        from vtk_mcp.tools.docs import vtk_is_a_class as f

        assert f("vtkSphereSource", ctx) is True

    def test_is_a_class_false(self, ctx):
        from vtk_mcp.tools.docs import vtk_is_a_class as f

        assert f("NotAClass", ctx) is False

    def test_get_class_action_phrase(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_action_phrase as f

        assert "sphere" in f("vtkSphereSource", ctx).lower()

    def test_get_class_visibility(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_visibility as f

        assert f("vtkSphereSource", ctx) == pytest.approx(0.92)

    def test_get_class_visibility_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_visibility as f

        assert f("vtkMissing", ctx) is None

    def test_get_class_inheritance(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_inheritance as f

        r = f("vtkSphereSource", ctx)
        assert "vtkObject" in r
        assert r[0] == "vtkSphereSource"

    def test_get_class_inheritance_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_inheritance as f

        assert f("vtkMissing", ctx) == []

    def test_get_class_record_metadata(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_record_metadata as f

        r = f("vtkSphereSource", ctx)
        assert r["vtk_version"] == "9.6.1"
        assert r["content_hash"] == "abc123"
        assert "schema_version" in r

    def test_get_class_record_metadata_missing(self, ctx):
        from vtk_mcp.tools.docs import vtk_get_class_record_metadata as f

        r = f("vtkMissing", ctx)
        assert "error" in r


# ── search tools ──────────────────────────────────────────────────────────


class TestSearchTools:
    def test_search_docs_no_retriever(self, ctx):
        from vtk_mcp.tools.search import vector_search_docs as f

        r = f("sphere", ctx)
        assert r[0]["error"].startswith("Retrieval not enabled")

    def test_search_examples_no_retriever(self, ctx):
        from vtk_mcp.tools.search import vector_search_examples as f

        r = f("render sphere", ctx)
        assert r[0]["error"].startswith("Retrieval not enabled")

    def test_search_docs_with_retriever(self, ctx_with_retriever):
        from vtk_mcp.tools.search import vector_search_docs as f

        r = f("sphere", ctx_with_retriever, k=3)
        assert len(r) == 1
        assert r[0]["class_names"] == ["vtkSphereSource"]
        ctx_with_retriever.retriever.search_docs.assert_called_once_with("sphere", k=3, filters=None)

    def test_search_examples_with_retriever(self, ctx_with_retriever):
        from vtk_mcp.tools.search import vector_search_examples as f

        r = f("render sphere", ctx_with_retriever, k=5)
        assert r[0]["content"] == "vtkSphereSource produces a polygonal sphere."
        ctx_with_retriever.retriever.search_code.assert_called_once_with("render sphere", k=5, filters=None)

    def test_search_docs_with_role_filter(self, ctx_with_retriever):
        from vtk_mcp.tools.search import vector_search_docs as f

        f("sphere", ctx_with_retriever, role="source")
        _, kwargs = ctx_with_retriever.retriever.search_docs.call_args
        assert kwargs["filters"] == {"role": "source"}

    def test_search_docs_with_class_filter(self, ctx_with_retriever):
        from vtk_mcp.tools.search import vector_search_docs as f

        f("sphere", ctx_with_retriever, class_name="vtkSphereSource")
        _, kwargs = ctx_with_retriever.retriever.search_docs.call_args
        assert kwargs["filters"] == {"class_names": "vtkSphereSource"}

    def test_search_docs_with_min_visibility(self, ctx_with_retriever):
        from vtk_mcp.tools.search import vector_search_docs as f

        f("sphere", ctx_with_retriever, min_visibility=0.5)
        _, kwargs = ctx_with_retriever.retriever.search_docs.call_args
        assert kwargs["filters"] == {"visibility_score": {"gte": 0.5}}

    def test_search_docs_combined_filters(self, ctx_with_retriever):
        from vtk_mcp.tools.search import vector_search_docs as f

        f("sphere", ctx_with_retriever, role="source", min_visibility=0.8)
        _, kwargs = ctx_with_retriever.retriever.search_docs.call_args
        assert kwargs["filters"]["role"] == "source"
        assert kwargs["filters"]["visibility_score"] == {"gte": 0.8}


# ── validation tools ──────────────────────────────────────────────────────


class TestValidationTools:
    def test_validate_vtk_code_valid(self, ctx):
        from vtk_mcp.tools.validation import validate_vtk_code as f

        r = f("x = 1", ctx)
        assert r["status"] == "ok"
        assert "diagnostics" in r

    def test_validate_vtk_code_no_validator(self, ctx):
        from vtk_mcp.tools.validation import validate_vtk_code as f

        ctx.validate = None
        r = f("x = 1", ctx)
        assert "error" in r

    def test_vtk_validate_import_no_validator(self, ctx):
        from vtk_mcp.tools.validation import vtk_validate_import as f

        r = f("from vtkmodules.vtkFiltersSources import vtkSphereSource", ctx)
        assert "valid" in r or "diagnostics" in r
