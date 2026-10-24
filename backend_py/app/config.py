from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 3000
    mongo_uri: str = ""
    mongo_db_name: str = "iotProj"
    jwt_secret: str = ""
    mqtt_url: str = ""
    mqtt_client_id: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"   # must support Structured Outputs (json_schema)
    # credentials that backend sends to device in MQTT settings
    device_admin_login: str = "Admin"
    device_admin_password: str = "4444"


settings = Settings()
