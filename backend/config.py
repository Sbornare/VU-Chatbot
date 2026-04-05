from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./admissions.db"
    AWS_S3_BUCKET: str = Field(..., env="AWS_S3_BUCKET")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_S3_PREFIX: str = Field(default="vu-chatbot-db", env="AWS_S3_PREFIX")
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    APP_NAME: str = "College Admission Agent"

    # IBM Cloud
    IBM_CLOUD_API_KEY: str = Field(..., env="IBM_CLOUD_API_KEY")
    IBM_PROJECT_ID: str = Field(..., env="IBM_PROJECT_ID")
    IBM_WATSONX_URL: str = Field(..., env="IBM_WATSONX_URL")

    # Granite models
    GRANITE_EMBEDDING_MODEL: str
    GRANITE_CHAT_MODEL: str

    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str = Field(default="", env="TWILIO_WHATSAPP_NUMBER")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

