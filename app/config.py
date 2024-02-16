from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://root:example@local-mongodb?retryWrites=true&w=majority&uuidRepresentation=standard"
    MONGODB_DATABASE_NAME: str = "local-mongodb"

    AUTH_SECRET: str = "bad_secret"
    GOOGLE_OAUTH_CLIENT_ID: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
