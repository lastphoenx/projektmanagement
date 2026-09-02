"""Tests für Ollama-Modellfilter."""

from app.core.llm.model_catalog import (
    STATIC_MODELS,
    filter_ollama_models,
    is_ollama_planning_model,
    pick_default_from_list,
)
from app.core.llm.providers.openai_compat import _anthropic_omits_sampling


def test_anthropic_static_models_use_valid_api_ids():
    models = STATIC_MODELS["anthropic"]
    assert "claude-3-5-sonnet-latest" not in models
    assert "claude-haiku-4-5-20251001" in models
    assert "claude-sonnet-5" in models
    assert "claude-sonnet-4-6" in models


def test_anthropic_sampling_omission_for_sonnet_5():
    assert _anthropic_omits_sampling("claude-sonnet-5")
    assert not _anthropic_omits_sampling("claude-haiku-4-5-20251001")
    assert not _anthropic_omits_sampling("claude-sonnet-4-6")


def test_excludes_embedding_and_vision_models():
    raw = [
        "bge-m3:latest",
        "llama3.3:70b",
        "qwen2.5vl:32b",
        "mikgr/doctype-classifier-vl:latest",
        "qwen2.5:32b",
    ]
    filtered = filter_ollama_models(raw)
    assert filtered == ["llama3.3:70b", "qwen2.5:32b"]


def test_is_ollama_planning_model():
    assert not is_ollama_planning_model("bge-m3:latest")
    assert is_ollama_planning_model("llama3:latest")


def test_pick_default_respects_env():
    models = ["llama3:latest", "llama3.3:70b"]
    assert pick_default_from_list("ollama", models, "llama3:latest") == "llama3:latest"
    assert pick_default_from_list("ollama", models, "") == "llama3.3:70b"
