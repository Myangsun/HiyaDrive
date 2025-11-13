"""
Configuration and settings management for HiyaDrive.
Uses pydantic for validation and environment variable parsing.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Main settings class with environment variable support."""

    # Application Metadata
    app_name: str = "HiyaDrive"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # =========================================================================
    # API Keys & Credentials
    # =========================================================================

    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    deepgram_api_key: str = Field(default="", env="DEEPGRAM_API_KEY")
    elevenlabs_api_key: str = Field(default="", env="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(default="sarah", env="ELEVENLABS_VOICE_ID")

    google_calendar_credentials: Optional[str] = Field(
        default=None, env="GOOGLE_CALENDAR_CREDENTIALS"
    )
    google_places_api_key: str = Field(default="", env="GOOGLE_PLACES_API_KEY")

    twilio_account_sid: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", env="TWILIO_PHONE_NUMBER")

    # =========================================================================
    # Database
    # =========================================================================

    database_url: str = Field(
        default="sqlite:///./hiya_drive.db", env="DATABASE_URL"
    )
    database_echo: bool = False

    # =========================================================================
    # Voice Settings (Mac Audio)
    # =========================================================================

    sample_rate: int = Field(default=16000, env="SAMPLE_RATE")
    channels: int = Field(default=1, env="CHANNELS")
    audio_chunk_size: int = Field(default=4096, env="AUDIO_CHUNK_SIZE")
    voice_timeout: int = Field(default=30, env="VOICE_TIMEOUT")
    silence_threshold: float = Field(default=-40.0, env="SILENCE_THRESHOLD")

    # =========================================================================
    # Feature Flags
    # =========================================================================

    use_mock_stt: bool = Field(default=False, env="USE_MOCK_STT")
    use_mock_tts: bool = Field(default=False, env="USE_MOCK_TTS")
    use_mock_calendar: bool = Field(default=False, env="USE_MOCK_CALENDAR")
    use_mock_places: bool = Field(default=False, env="USE_MOCK_PLACES")
    use_mock_twilio: bool = Field(default=False, env="USE_MOCK_TWILIO")

    # =========================================================================
    # Demo Settings
    # =========================================================================

    demo_mode: bool = Field(default=True, env="DEMO_MODE")
    demo_restaurant_name: str = Field(
        default="Olive Garden", env="DEMO_RESTAURANT_NAME"
    )
    demo_restaurant_phone: str = Field(
        default="+1-555-0100", env="DEMO_RESTAURANT_PHONE"
    )
    max_call_duration: int = Field(default=120, env="MAX_CALL_DURATION")

    # =========================================================================
    # LLM Configuration
    # =========================================================================

    llm_model: str = "claude-sonnet-4-5-20250929"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7

    # =========================================================================
    # Orchestration Settings
    # =========================================================================

    max_conversation_turns: int = 10
    conversation_timeout: int = 120  # seconds
    silence_timeout: int = 5  # seconds
    max_retries: int = 2

    # =========================================================================
    # Paths
    # =========================================================================

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory."""
        logs = self.project_root / "data" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        return logs

    @property
    def recordings_dir(self) -> Path:
        """Get the recordings directory."""
        recordings = self.project_root / "data" / "recordings"
        recordings.mkdir(parents=True, exist_ok=True)
        return recordings

    @property
    def config_dir(self) -> Path:
        """Get the config directory."""
        return self.project_root / "config"

    class Config:
        """Pydantic config."""

        env_file = Path(__file__).parent.parent.parent / ".env"
        case_sensitive = False
        extra = "allow"

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"

    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.app_env == "staging"


# Global settings instance
settings = Settings()
