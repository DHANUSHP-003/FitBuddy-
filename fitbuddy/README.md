# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI web application for generating
personalized 7-day fitness plans using Google Gemini.

The application also generates nutrition/recovery tips,
supports feedback-based plan regeneration, stores data
in SQLite, and provides an admin dashboard.

## Architecture

- FastAPI
- Jinja2
- SQLAlchemy
- SQLite
- Google Gemini
- Pydantic
- pytest

## Project Structure

```text
fitbuddy/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_client.py
│   │   ├── gemini_generator.py
│   │   ├── gemini_flash_generator.py
│   │   └── updated_plan.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── result.html
│   │   └── all_users.html
│   │
│   └── static/
│       └── styles.css
│
├── tests/
│   └── test_api.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md