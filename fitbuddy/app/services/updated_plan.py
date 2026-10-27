from ..config import get_settings
from .gemini_client import generate_gemini_content


def update_workout_plan(
    *,
    original_plan: str,
    feedback: str,
    goal: str,
    intensity: str,
) -> str:

    settings = get_settings()

    prompt = f"""
You are revising an existing FitBuddy
7-day workout plan.

Fitness goal:
{goal}

Preferred intensity:
{intensity}

Original plan:
----------------
{original_plan}
----------------

User feedback:
----------------
{feedback}
----------------

Return a COMPLETE revised 7-day plan.

Do not return only a list of changes.

Preserve useful parts of the original
plan while applying the user's feedback safely.

Use these headings:

Day 1
Day 2
Day 3
Day 4
Day 5
Day 6
Day 7

Every day should include:

1. Focus
2. Warm-up
3. Main workout
4. Cool-down/recovery

Include exercise details such as:

- sets
- repetitions
- duration
- rest

Never make medical claims.

Never prescribe medication.

Never recommend unsafe exercise.

Include a short safety note.
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
            "Gemini returned an empty revised plan."
        )

    return text