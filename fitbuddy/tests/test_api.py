import os


os.environ["DATABASE_URL"] = (
    "sqlite:///./test_fitbuddy.db"
)

os.environ["ADMIN_KEY"] = "test-admin"


from fastapi.testclient import TestClient

from app.database import (
    Base,
    engine,
)

from app.main import app


client = TestClient(app)


def setup_function():

    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )


def teardown_module():

    Base.metadata.drop_all(
        bind=engine
    )

    if os.path.exists(
        "test_fitbuddy.db"
    ):

        os.remove(
            "test_fitbuddy.db"
        )


def test_health():

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_create_plan_with_mocked_ai(
    monkeypatch,
):

    import app.routes as routes


    monkeypatch.setattr(
        routes,
        "generate_workout_gemini",
        lambda **kwargs:
            "Day 1\nWarm-up\nSquats 3x10",
    )


    monkeypatch.setattr(
        routes,
        "generate_nutrition_tip_with_flash",
        lambda **kwargs:
            "Drink water and include protein-rich foods.",
    )


    payload = {

        "user_id": "test01",

        "name": "Test User",

        "age": 30,

        "weight_kg": 70,

        "goal": "muscle gain",

        "intensity": "medium",
    }


    response = client.post(
        "/api/plans",
        json=payload,
    )


    assert response.status_code == 201


    body = response.json()


    assert body["user_id"] == "test01"


    assert "Day 1" in (
        body["workout_plan"]
    )


def test_feedback_updates_plan(
    monkeypatch,
):

    import app.routes as routes


    monkeypatch.setattr(
        routes,
        "generate_workout_gemini",
        lambda **kwargs:
            "ORIGINAL PLAN",
    )


    monkeypatch.setattr(
        routes,
        "generate_nutrition_tip_with_flash",
        lambda **kwargs:
            "NUTRITION TIP",
    )


    monkeypatch.setattr(
        routes,
        "update_workout_plan",
        lambda **kwargs:
            "UPDATED PLAN",
    )


    payload = {

        "user_id": "test02",

        "name": "Test User",

        "age": 30,

        "weight_kg": 70,

        "goal": "weight loss",

        "intensity": "low",
    }


    response = client.post(
        "/api/plans",
        json=payload,
    )


    assert response.status_code == 201


    response = client.post(
        "/api/plans/feedback",
        json={
            "user_id": "test02",
            "feedback": "Add more cardio",
        },
    )


    assert response.status_code == 200


    assert (
        response.json()["workout_plan"]
        == "UPDATED PLAN"
    )


def test_admin_requires_key():

    response = client.get(
        "/api/admin/users"
    )

    assert response.status_code == 401


    response = client.get(
        "/api/admin/users",
        headers={
            "X-Admin-Key": "test-admin"
        },
    )


    assert response.status_code == 200