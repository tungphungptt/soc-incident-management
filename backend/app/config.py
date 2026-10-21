from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SOC Incident Management"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "mysql+pymysql://root:password@127.0.0.1:3306/soc_incident_management?charset=utf8mb4"
    jwt_secret: str = "CHANGE-ME-TO-A-LONG-RANDOM-SECRET"
    jwt_expire_minutes: int = 480
    admin_username: str = "admin"
    admin_password: str = "ChangeThisImmediately!"
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
