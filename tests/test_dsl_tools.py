"""Unit tests for the DSL tools in vtk_mcp.tools.dsl."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def _make_ctx(
    translate_model: str = "test-model",
    translate_base_url: str | None = None,
    translate_api_key: str | None = None,
) -> MagicMock:
    ctx = MagicMock()
    ctx.settings.translate_model = translate_model
    ctx.settings.translate_base_url = translate_base_url
    ctx.settings.translate_api_key = translate_api_key
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

        ctx = _make_ctx(translate_model="haiku")
        expected_dsl = "create plane_source called src with x_resolution 10"

        with patch("vtk_validate.dsl.translate_to_dsl", return_value=expected_dsl) as mock_fn:
            result = translate_prompt_to_dsl("make a plane", ctx)

        mock_fn.assert_called_once_with(
            query="make a plane",
            api_index=ctx.api_index,
            model="haiku",
            base_url=None,
            api_key=None,
        )
        assert result == expected_dsl

    def test_model_override_takes_precedence(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx(translate_model="default-model")
        with patch("vtk_validate.dsl.translate_to_dsl", return_value="render render with background [0,0,0]") as mock_fn:
            translate_prompt_to_dsl("make a scene", ctx, model="override-model")

        mock_fn.assert_called_once_with(
            query="make a scene",
            api_index=ctx.api_index,
            model="override-model",
            base_url=None,
            api_key=None,
        )

    def test_no_override_uses_settings_model(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx(translate_model="settings-model")
        with patch("vtk_validate.dsl.translate_to_dsl", return_value="render render with background [0,0,0]") as mock_fn:
            translate_prompt_to_dsl("make a scene", ctx)

        assert mock_fn.call_args.kwargs["model"] == "settings-model"

    def test_missing_vtk_validate_returns_error(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx()
        with patch.dict("sys.modules", {"vtk_validate.dsl": None}):
            result = translate_prompt_to_dsl("make a sphere", ctx)

        assert result.startswith("Error:")

    def test_returns_string(self):
        from vtk_mcp.tools.dsl import translate_prompt_to_dsl

        ctx = _make_ctx()
        with patch("vtk_validate.dsl.translate_to_dsl", return_value="render render with background [0,0,0]"):
            result = translate_prompt_to_dsl("render a black background", ctx)

        assert isinstance(result, str)
        assert len(result) > 0
