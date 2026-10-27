import time
from functools import lru_cache

from google import genai

from ..config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Copy .env.example to .env and add your Gemini API key."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_gemini_content(
    *,
    model: str,
    contents: str,
    retries: int = 3,
):
    """
    Send a request to Gemini.

    Automatically retries temporary 503 / UNAVAILABLE errors.
    """

    client = get_gemini_client()

    last_error = None

    for attempt in range(1, retries + 1):

        try:
            print(
                f"Gemini request: model={model}, "
                f"attempt={attempt}/{retries}"
            )

            response = client.models.generate_content(
                model=model,
                contents=contents,
            )

            return response

        except Exception as exc:

            last_error = exc
            error_text = str(exc)

            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text.upper()
                or "temporarily unavailable" in error_text.lower()
            )

            if not temporary_error:
                raise

            print(
                f"Gemini model {model} is temporarily unavailable."
            )

            if attempt < retries:
                wait_seconds = 2 ** attempt

                print(
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)

    raise RuntimeError(
        "Gemini is temporarily unavailable after multiple attempts. "
        "Please wait a little while and try again."
    ) from last_error