from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ROOT_ENV, _BACKEND_ENV),
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://pm:pm@localhost:5433/projektmanagement"
    encryption_master_key: str = ""
    session_secret: str = ""
    session_ttl_sec: int = 28800
    pbkdf2_iterations: int = 600_000
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    default_tenant_slug: str = "default"
    allow_registration: bool = False
    cookie_name: str = "pm_session"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    login_challenge_ttl_sec: int = 300
    challenge_cookie_name: str = "pm_2fa_challenge"

    # LLM — Infrastruktur-Defaults (.env); aktive Wahl in tenant_llm_configs (Admin-UI)
    ollama_base_url: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "ollama"
    llm_model: str = ""  # Legacy-Fallback für alle Provider
    llm_model_ollama: str = ""
    llm_model_openai: str = ""
    llm_model_anthropic: str = ""
    llm_base_url: str = ""
    llm_api_key_fallback: str = ""

    # B.3 Rate-Limiting (togglebar; CrowdSec-Vorbereitung)
    rate_limit_enabled: bool = True
    api_rate_limit_per_minute: int = 120
    login_max_failures_per_user: int = 5
    login_lockout_seconds: int = 900
    login_max_attempts_per_ip: int = 30
    login_ip_window_seconds: int = 300

    # PII-Gate (swiss-pii-anonymizer)
    pii_anonymizer_enabled: bool = True
    pii_anonymizer_required: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
