from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)

from fastapi.responses import HTMLResponse

from fastapi.templating import (
    Jinja2Templates,
)

from sqlalchemy import select

from sqlalchemy.orm import (
    Session,
    joinedload,
)

from .database import get_db
from .dependencies import require_admin
from .models import User, WorkoutPlan
from .schemas import (
    FeedbackRequest,
    UserInput,
)

from .services.gemini_flash_generator import (
    generate_nutrition_tip_with_flash,
)

from .services.gemini_generator import (
    generate_workout_gemini,
)

from .services.updated_plan import (
    update_workout_plan,
)


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)


def _get_user_by_external_id(
    db: Session,
    user_id: str,
) -> User | None:

    return db.scalar(
        select(User)
        .options(
            joinedload(User.plan)
        )
        .where(
            User.user_id == user_id
        )
    )


def _context_from_plan(
    user: User,
    plan: WorkoutPlan,
    *,
    is_updated: bool = False,
) -> dict:

    return {
        "user": user,

        "plan": (
            plan.updated_plan
            if is_updated
            and plan.updated_plan
            else plan.original_plan
        ),

        "nutrition_tip":
            plan.nutrition_tip,

        "is_updated":
            is_updated
            and bool(plan.updated_plan),

        "feedback":
            plan.latest_feedback,
    }


def _save_user_and_plan(
    db: Session,
    payload: UserInput,
    workout: str,
    nutrition: str,
) -> tuple[User, WorkoutPlan]:

    user = _get_user_by_external_id(
        db,
        payload.user_id,
    )

    data = payload.model_dump()

    if user is None:

        user = User(**data)

        db.add(user)

        db.flush()

    else:

        for key, value in data.items():

            setattr(
                user,
                key,
                value,
            )

    if user.plan:

        user.plan.original_plan = workout

        user.plan.updated_plan = None

        user.plan.latest_feedback = None

        user.plan.nutrition_tip = nutrition

        user.plan.updated_at = None

        plan = user.plan

    else:

        plan = WorkoutPlan(
            user_id=user.id,
            original_plan=workout,
            nutrition_tip=nutrition,
        )

        db.add(plan)

    db.commit()

    db.refresh(user)

    db.refresh(plan)

    return user, plan


@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
)
def generate_workout_form(
    request: Request,

    user_id: str = Form(...),

    name: str = Form(...),

    age: int = Form(...),

    weight_kg: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        user_input = UserInput(
            user_id=user_id,
            name=name,
            age=age,
            weight_kg=weight_kg,
            goal=goal,
            intensity=intensity,
        )

        workout = generate_workout_gemini(
            name=user_input.name,
            age=user_input.age,
            weight_kg=user_input.weight_kg,
            goal=user_input.goal,
            intensity=user_input.intensity,
        )

        nutrition = (
            generate_nutrition_tip_with_flash(
                goal=user_input.goal,
                intensity=user_input.intensity,
            )
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc),

                "form": {
                    "user_id": user_id,
                    "name": name,
                    "age": age,
                    "weight_kg": weight_kg,
                    "goal": goal,
                    "intensity": intensity,
                },
            },
            status_code=502,
        )

    user, plan = _save_user_and_plan(
        db=db,
        payload=user_input,
        workout=workout,
        nutrition=nutrition,
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=_context_from_plan(
            user,
            plan,
        ),
    )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
)
def submit_feedback_form(
    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        payload = FeedbackRequest(
            user_id=user_id,
            feedback=feedback,
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "error": str(exc)
            },
            status_code=422,
        )

    user = _get_user_by_external_id(
        db,
        payload.user_id,
    )

    if not user or not user.plan:

        raise HTTPException(
            status_code=404,
            detail="User or workout plan not found",
        )

    current_plan = (
        user.plan.updated_plan
        or user.plan.original_plan
    )

    try:

        revised = update_workout_plan(
            original_plan=current_plan,
            feedback=payload.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )

        nutrition = (
            generate_nutrition_tip_with_flash(
                goal=user.goal,
                intensity=user.intensity,
            )
        )

        user.plan.updated_plan = revised

        user.plan.latest_feedback = (
            payload.feedback
        )

        user.plan.nutrition_tip = nutrition

        user.plan.updated_at = (
            datetime.now(timezone.utc)
        )

        db.commit()

        db.refresh(user.plan)

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": current_plan,
                "nutrition_tip":
                    user.plan.nutrition_tip,
                "error": str(exc),
            },
            status_code=502,
        )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=_context_from_plan(
            user,
            user.plan,
            is_updated=True,
        ),
    )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
)
def view_all_users(
    request: Request,

    key: str = Query(
        default=""
    ),

    db: Session = Depends(get_db),
):

    from .config import get_settings

    settings = get_settings()

    if key != settings.admin_key:

        return templates.TemplateResponse(
            request=request,
            name="all_users.html",
            context={
                "users": [],

                "admin_error":
                    "Valid admin key required. "
                    "Open /view-all-users?"
                    "key=YOUR_ADMIN_KEY.",
            },
            status_code=401,
        )

    users = (
        db.scalars(
            select(User)
            .options(
                joinedload(User.plan)
            )
            .order_by(
                User.created_at.desc()
            )
        )
        .unique()
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users
        },
    )


# ---------------------------------------------------------
# JSON API
# ---------------------------------------------------------


@router.get("/api/health")
def api_health():

    return {
        "status": "ok",
        "service": "FitBuddy",
    }


@router.post(
    "/api/plans",
    status_code=status.HTTP_201_CREATED,
)
def api_generate_plan(
    payload: UserInput,

    db: Session = Depends(get_db),
):

    try:

        workout = generate_workout_gemini(
            name=payload.name,
            age=payload.age,
            weight_kg=payload.weight_kg,
            goal=payload.goal,
            intensity=payload.intensity,
        )

        nutrition = (
            generate_nutrition_tip_with_flash(
                goal=payload.goal,
                intensity=payload.intensity,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    user, plan = _save_user_and_plan(
        db=db,
        payload=payload,
        workout=workout,
        nutrition=nutrition,
    )

    return {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "weight_kg": user.weight_kg,
        "goal": user.goal,
        "intensity": user.intensity,
        "workout_plan": plan.original_plan,
        "nutrition_tip": plan.nutrition_tip,
        "is_updated": False,
    }


@router.post(
    "/api/plans/feedback"
)
def api_update_plan(
    payload: FeedbackRequest,

    db: Session = Depends(get_db),
):

    user = _get_user_by_external_id(
        db,
        payload.user_id,
    )

    if not user or not user.plan:

        raise HTTPException(
            status_code=404,
            detail="User or workout plan not found",
        )

    current_plan = (
        user.plan.updated_plan
        or user.plan.original_plan
    )

    try:

        revised = update_workout_plan(
            original_plan=current_plan,
            feedback=payload.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )

        nutrition = (
            generate_nutrition_tip_with_flash(
                goal=user.goal,
                intensity=user.intensity,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    user.plan.updated_plan = revised

    user.plan.latest_feedback = (
        payload.feedback
    )

    user.plan.nutrition_tip = nutrition

    user.plan.updated_at = (
        datetime.now(timezone.utc)
    )

    db.commit()

    return {
        "user_id": user.user_id,
        "workout_plan": revised,
        "nutrition_tip": nutrition,
        "is_updated": True,
    }


@router.get(
    "/api/plans/{user_id}"
)
def api_get_plan(
    user_id: str,

    db: Session = Depends(get_db),
):

    user = _get_user_by_external_id(
        db,
        user_id,
    )

    if not user or not user.plan:

        raise HTTPException(
            status_code=404,
            detail="User or workout plan not found",
        )

    return {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "weight_kg": user.weight_kg,
        "goal": user.goal,
        "intensity": user.intensity,

        "original_plan":
            user.plan.original_plan,

        "updated_plan":
            user.plan.updated_plan,

        "latest_feedback":
            user.plan.latest_feedback,

        "nutrition_tip":
            user.plan.nutrition_tip,
    }


@router.get(
    "/api/admin/users",
    dependencies=[
        Depends(require_admin)
    ],
)
def api_admin_users(
    db: Session = Depends(get_db),
):

    users = (
        db.scalars(
            select(User)
            .options(
                joinedload(User.plan)
            )
            .order_by(
                User.created_at.desc()
            )
        )
        .unique()
        .all()
    )

    return [
        {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "weight_kg": user.weight_kg,
            "goal": user.goal,
            "intensity": user.intensity,

            "original_plan":
                user.plan.original_plan
                if user.plan
                else None,

            "updated_plan":
                user.plan.updated_plan
                if user.plan
                else None,

            "latest_feedback":
                user.plan.latest_feedback
                if user.plan
                else None,

            "nutrition_tip":
                user.plan.nutrition_tip
                if user.plan
                else None,
        }

        for user in users
    ]