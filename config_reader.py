from os.path import dirname, join
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    BOT_TOKEN: SecretStr

    WEBAPP_URL: str = "https://randomgiftss.web.app/"
    WEBHOOK_URL: str = ""
    WEBHOOK_PATH: str = "/webhook"

    APP_HOST: str = "localhost"
    APP_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=join(dirname(__file__), '.env'),
        env_file_encoding="utf-8"
    )

config = Config()

