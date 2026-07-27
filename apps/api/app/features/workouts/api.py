from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.features.workouts.schemas import (
    AssignmentCreate,
    AssignmentOut,
    ExerciseCreate,
    ExerciseOut,
    WorkoutPlanCreate,
    WorkoutPlanOut,
)
from app.features.workouts.services import WorkoutService

router = APIRouter(prefix="/api/v1", tags=["workouts"])


@router.get("/exercises", response_model=list[ExerciseOut])
async def list_exercises(
    principal: AuthPrincipal = Depends(require_permission("workout:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[ExerciseOut]:
    return await WorkoutService(db).list_exercises(org_id(principal))


@router.post("/exercises", response_model=ExerciseOut, status_code=201)
async def create_exercise(
    body: ExerciseCreate,
    principal: AuthPrincipal = Depends(require_permission("workout:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ExerciseOut:
    return await WorkoutService(db).create_exercise(org_id(principal), body, principal.user.id)


@router.get("/workouts", response_model=list[WorkoutPlanOut])
async def list_workouts(
    principal: AuthPrincipal = Depends(require_permission("workout:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[WorkoutPlanOut]:
    return await WorkoutService(db).list_plans(org_id(principal))


@router.post("/workouts", response_model=WorkoutPlanOut, status_code=201)
async def create_workout(
    body: WorkoutPlanCreate,
    principal: AuthPrincipal = Depends(require_permission("workout:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> WorkoutPlanOut:
    return await WorkoutService(db).create_plan(org_id(principal), body, principal.user.id)


@router.get("/workouts/{plan_id}", response_model=WorkoutPlanOut)
async def get_workout(
    plan_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("workout:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> WorkoutPlanOut:
    return await WorkoutService(db).get_plan(org_id(principal), plan_id)


@router.post("/workout-assignments", response_model=AssignmentOut, status_code=201)
async def assign_workout(
    body: AssignmentCreate,
    principal: AuthPrincipal = Depends(require_permission("workout:assign")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AssignmentOut:
    return await WorkoutService(db).assign(org_id(principal), body, principal.user.id)


@router.get("/workout-assignments", response_model=list[AssignmentOut])
async def list_assignments(
    client_id: UUID | None = Query(None),
    principal: AuthPrincipal = Depends(require_permission("workout:assign")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[AssignmentOut]:
    return await WorkoutService(db).list_assignments(org_id(principal), client_id)
