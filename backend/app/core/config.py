from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pengaturan aplikasi. Nilai diambil dari environment / file .env."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RME STT-NLP Demo API"
    api_v1_prefix: str = "/api/v1"

    # Keamanan
    secret_key: str = "dev-secret-ganti-dengan-nilai-acak-panjang"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    access_token_cookie_name: str = "access_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/rme_stt"

    # CORS (dipisah koma)
    cors_origins: str = "http://localhost:5173"

    # Pipeline NLP: "mock" | "real"
    nlp_engine: str = "mock"

    # Upload audio & STT
    max_upload_mb: int = 50
    audio_upload_dir: str = "data/audio"
    audio_samples_dir: str = "data/samples"
    whisper_model_path: str = "models_store/whisper"
    whisper_device: str = "auto"  # auto | cuda | cpu
    whisper_chunk_length_s: int = 30
    whisper_language: str = "id"
    whisper_task: str = "transcribe"
    stt_engine: str = "auto"  # auto | whisper | mock

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
