from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Prometheus
    prometheus_url: str = Field(default="http://localhost:9090")
    prometheus_username: str = Field(default="")
    prometheus_password: str = Field(default="")

    # Grafana
    grafana_url: str = Field(default="http://localhost:3000")
    grafana_api_key: str = Field(default="")
    grafana_org_id: int = Field(default=1)

    # Loki
    loki_url: str = Field(default="http://localhost:3100")
    loki_username: str = Field(default="")
    loki_password: str = Field(default="")

    # PagerDuty
    pagerduty_api_key: str = Field(default="")
    pagerduty_from_email: str = Field(default="oncall@example.com")
    pagerduty_service_id: str = Field(default="")
    pagerduty_escalation_policy_id: str = Field(default="")

    # Slack
    slack_bot_token: str = Field(default="")
    slack_default_channel: str = Field(default="#incidents")


settings = Settings()
