"""Configuración de la aplicación, cargada desde variables de entorno."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Conexión a SQL Server ---
    db_host: str = Field(default="sqlserver", alias="DB_HOST")
    db_port: int = Field(default=1433, alias="DB_PORT")
    db_user: str = Field(default="sa", alias="DB_USER")
    db_password: str = Field(default="Dev_Camaras_2026!", alias="DB_PASSWORD")
    db_name: str = Field(default="DBCAMARADETECCIONIM", alias="DB_NAME")

    # --- JWT ---
    jwt_secret: str = Field(default="clave-demo-insegura", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MINUTES")

    # --- Usuarios semilla: "user1:pass1,user2:pass2" ---
    demo_users: str = Field(default="admin:admin123,demo:demo123", alias="DEMO_USERS")

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """URL SQLAlchemy usando el driver pymssql (no requiere ODBC)."""
        return (
            f"mssql+pymssql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            "?charset=utf8"
        )

    @property
    def users_map(self) -> dict[str, str]:
        """Devuelve {usuario: contraseña} a partir de DEMO_USERS."""
        result: dict[str, str] = {}
        for pair in self.demo_users.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            user, _, password = pair.partition(":")
            result[user.strip()] = password.strip()
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
