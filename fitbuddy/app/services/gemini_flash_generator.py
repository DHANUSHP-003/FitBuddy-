from ..config import get_settings
from .gemini_client import generate_gemini_content


def generate_nutrition_tip_with_flash(
    *,
    goal: str,
    intensity: str,
) -> str:

    settings = get_settings()

    prompt = f"""
Give one concise, practical nutrition
or recovery tip for a fitness user.

Goal:
{goal}

Workout intensity:
{intensity}

Keep the answer to 2-4 sentences.

Focus on ordinary healthy foods,
hydration, sleep, or recovery habits.

Do not prescribe medication.

Do not prescribe supplements.

Do not provide dangerous dieting advice.

Mention that individual nutrition needs
can vary when relevant.
"""

    response = generate_gemini_content(
    model=settings.gemini_nutrition_model,
    contents=prompt,
    )

    text = (
        response.text or ""
    ).strip()

    if not text:

        raise RuntimeError(
            "Gemini returned an empty nutrition tip."
        )

    return text