"""Anthropic identity-linked Keys — Workspace-Header."""

from app.services.llm_provider_service import make_runtime_config, provider_extra_headers


def test_provider_extra_headers_anthropic_with_workspace(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_provider_service.config.settings.anthropic_workspace_id",
        "wrkspc_01TEST",
    )
    assert provider_extra_headers("anthropic") == {
        "anthropic-workspace-id": "wrkspc_01TEST",
    }
    assert provider_extra_headers("openai") == {}


def test_make_runtime_config_includes_headers(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_provider_service.config.settings.anthropic_workspace_id",
        "wrkspc_01TEST",
    )
    cfg = make_runtime_config(
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        base_url="https://api.anthropic.com/v1",
        api_key="sk-ant-test",
        is_local=False,
    )
    assert cfg.extra_headers == {"anthropic-workspace-id": "wrkspc_01TEST"}
