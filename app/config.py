from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    SECRET_KEY: str
    ALGORITHM: str
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    S3_BUCKET: str
    S3_REGION: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str

    CELERY_BROKER_URL: str

    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings() 

