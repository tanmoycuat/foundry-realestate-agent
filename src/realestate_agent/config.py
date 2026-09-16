"""Application configuration for local and Foundry-hosted execution."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    foundry_project_endpoint: str = ""
    azure_ai_model_deployment_name: str = ""
    toolbox_endpoint: str | None = None
    toolbox_name: str = "realestate-data"
    default_model_profile: str = "foundry-default"
    skill_cache_ttl_seconds: int = Field(default=60, ge=0, le=3600)

    def validate_hosted_requirements(self) -> None:
        missing = []
        if not self.foundry_project_endpoint:
            missing.append("FOUNDRY_PROJECT_ENDPOINT")
        if not self.azure_ai_model_deployment_name:
            missing.append("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        if missing:
            raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")
