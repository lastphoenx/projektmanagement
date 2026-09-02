"""Tests für Ollama-Modellfilter."""

from app.core.llm.model_catalog import filter_ollama_models, is_ollama_planning_model, pick_default_from_list


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
