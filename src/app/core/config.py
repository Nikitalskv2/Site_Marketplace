from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
_project_timezone = "Europe/Moscow"


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "auth" / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "auth" / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30


class Settings(BaseSettings):
    auth_jwt: AuthJWT = AuthJWT()
    timezone: str
    tz: ZoneInfo
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_echo: bool = False

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"  # noqa: 501

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings(timezone=_project_timezone, tz=ZoneInfo(_project_timezone))
