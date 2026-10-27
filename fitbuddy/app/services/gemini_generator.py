from ..config import get_settings
from .gemini_client import generate_gemini_content


SAFETY = """
Include a brief safety note:
this is general wellness guidance,
not medical advice.

Tell the user to stop if they experience
pain and to consult a qualified professional
for injuries or medical conditions.
"""


def generate_workout_gemini(
    *,
    name: str,
    age: int,
    weight_kg: float,
    goal: str,
    intensity: str,
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy, a careful fitness-planning assistant.

Create a practical 7-day workout plan for this user.

User information:
- Name: {name}
- Age: {age}
- Weight: {weight_kg} kg
- Goal: {goal}
- Preferred intensity: {intensity}

Return plain text.

Do NOT use a markdown table.

Use exactly these headings:

Day 1
Day 2
Day 3
Day 4
Day 5
Day 6
Day 7

For every day include:

1. Focus
2. Warm-up (5-10 minutes)
3. Main workout
4. Cool-down/recovery

For every main exercise include:

- Exercise name
- Sets x repetitions OR duration
- Rest period

Make the program practical and varied.

At least one day should be
lower-intensity recovery/rest,
appropriate to the user's goal and intensity.

Do not prescribe:

- medication
- supplements
- extreme calorie restriction
- unsafe exercise

Do not claim that a specific result
is guaranteed.

{SAFETY}
"""

    response = generate_gemini_content(
    model=settings.gemini_workout_model,
    contents=prompt,
    )

    text = (
        response.text or ""
    ).strip()

    if not text:

        raise RuntimeError(
            "Gemini returned an empty workout plan."
        )

    return text