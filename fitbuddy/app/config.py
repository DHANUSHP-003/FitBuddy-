from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()


class Settings(BaseModel):
    app_name: str = Field(default="FitBuddy")

    database_url: str = Field(
        default="sqlite:///./fitbuddy.db"
    )

    gemini_api_key: str = Field(default="")

    gemini_workout_model: str = Field(
        default="gemini-3.8-flash"
    )

    gemini_nutrition_model: str = Field(
        default="gemini-3.8-flash"
    )

    admin_key: str = Field(
        default="change-this-admin-key"
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
    )


@lru_cache
def get_settings() -> Settings:
    origins = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    )

    return Settings(
        app_name=os.getenv(
            "APP_NAME",
            "FitBuddy",
        ),

        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./fitbuddy.db",
        ),

        gemini_api_key=os.getenv(
            "GEMINI_API_KEY",
            os.getenv("GOOGLE_API_KEY", ""),
        ),

        gemini_workout_model=os.getenv(
            "GEMINI_WORKOUT_MODEL",
            "gemini-3.8-flash",
        ),

        gemini_nutrition_model=os.getenv(
            "GEMINI_NUTRITION_MODEL",
            "gemini-3.8-flash",
        ),

        admin_key=os.getenv(
            "ADMIN_KEY",
            "change-this-admin-key",
        ),

        cors_origins=[
            item.strip()
            for item in origins.split(",")
            if item.strip()
        ],
    )