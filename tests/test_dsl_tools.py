"""Unit tests for the DSL tools in vtk_mcp.tools.dsl."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.api_index = MagicMock()
    ctx.api_index.vtk_version = "9.6.1"
    return ctx


class TestIsDslPrompt:
    def test_dsl_text_returns_true(self):
        from vtk_mcp.tools.dsl import is_dsl_prompt

        assert is_dsl_prompt("create plane_source called src with x_resolution 60") is True

    def test_natural_language_returns_false(self):
        from vtk_mcp.tools.dsl import is_dsl_prompt

        assert is_dsl_prompt("make a sphere with a colormap") is False

    def test_empty_string_returns_false(self):
        from vtk_mcp.tools.dsl import is_dsl_prompt

        assert is_dsl_prompt("") is False


class TestTranslatePromptToDsl:
    def test_delegates_to_vtk_validate(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx()
        expected_context = "SYNTAX\n------\n...\n\nRequest: make a plane"

        with patch("vtk_validate.dsl.build_dsl_translation_context", return_value=expected_context) as mock_fn:
            result = translate_prompt_to_dsl("make a plane", ctx)

        mock_fn.assert_called_once_with(query="make a plane", api_index=ctx.api_index)
        assert result == expected_context

    def test_missing_vtk_validate_returns_error(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx()
        with patch.dict("sys.modules", {"vtk_validate.dsl": None}):
            result = translate_prompt_to_dsl("make a sphere", ctx)

        assert result.startswith("Error:")

    def test_returns_string(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx()
        with patch("vtk_validate.dsl.build_dsl_translation_context", return_value="render render with background [0,0,0]"):
            result = translate_prompt_to_dsl("render a black background", ctx)

        assert isinstance(result, str)
        assert len(result) > 0
