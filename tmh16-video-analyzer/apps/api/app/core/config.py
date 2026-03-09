from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str
    redis_url: str = 'redis://localhost:6379/0'
    jwt_secret: str = 'dev-secret'
    storage_path: str = '/tmp/tmh16-storage'
    report_temp_path: str = '/tmp/tmh16-reports'


settings = Settings()
