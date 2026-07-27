from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Client, Exercise, WorkoutAssignment, WorkoutPlan
from app.features.workouts.schemas import (
    AssignmentCreate,
    AssignmentOut,
    ExerciseCreate,
    ExerciseOut,
    WorkoutPlanCreate,
    WorkoutPlanOut,
)


class WorkoutService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_exercises(self, organization_id: UUID) -> list[ExerciseOut]:
        result = await self.db.execute(
            select(Exercise)
            .where(Exercise.organization_id == organization_id, Exercise.deleted_at.is_(None))
            .order_by(Exercise.name.asc())
        )
        return [ExerciseOut.model_validate(e) for e in result.scalars().all()]

    async def create_exercise(
        self, organization_id: UUID, data: ExerciseCreate, actor_id: UUID
    ) -> ExerciseOut:
        row = Exercise(
            organization_id=organization_id,
            **data.model_dump(),
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return ExerciseOut.model_validate(row)

    async def list_plans(self, organization_id: UUID) -> list[WorkoutPlanOut]:
        result = await self.db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.organization_id == organization_id, WorkoutPlan.deleted_at.is_(None))
            .order_by(WorkoutPlan.updated_at.desc())
        )
        return [WorkoutPlanOut.model_validate(p) for p in result.scalars().all()]

    async def create_plan(
        self, organization_id: UUID, data: WorkoutPlanCreate, actor_id: UUID
    ) -> WorkoutPlanOut:
        row = WorkoutPlan(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            is_template=data.is_template,
            items=[i.model_dump(mode="json") for i in data.items],
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return WorkoutPlanOut.model_validate(row)

    async def get_plan(self, organization_id: UUID, plan_id: UUID) -> WorkoutPlanOut:
        result = await self.db.execute(
            select(WorkoutPlan).where(
                WorkoutPlan.id == plan_id,
                WorkoutPlan.organization_id == organization_id,
                WorkoutPlan.deleted_at.is_(None),
            )
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return WorkoutPlanOut.model_validate(plan)

    async def assign(
        self, organization_id: UUID, data: AssignmentCreate, actor_id: UUID
    ) -> AssignmentOut:
        client = await self.db.scalar(
            select(Client).where(
                Client.id == data.client_id,
                Client.organization_id == organization_id,
                Client.deleted_at.is_(None),
            )
        )
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        plan = await self.db.scalar(
            select(WorkoutPlan).where(
                WorkoutPlan.id == data.workout_plan_id,
                WorkoutPlan.organization_id == organization_id,
                WorkoutPlan.deleted_at.is_(None),
            )
        )
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        row = WorkoutAssignment(
            organization_id=organization_id,
            client_id=data.client_id,
            workout_plan_id=data.workout_plan_id,
            assigned_at=datetime.now(UTC),
            notes=data.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        await self.db.flush()
        out = AssignmentOut.model_validate(row)
        out.plan_name = plan.name
        return out

    async def list_assignments(
        self, organization_id: UUID, client_id: UUID | None = None
    ) -> list[AssignmentOut]:
        filters = [
            WorkoutAssignment.organization_id == organization_id,
            WorkoutAssignment.deleted_at.is_(None),
        ]
        if client_id:
            filters.append(WorkoutAssignment.client_id == client_id)
        result = await self.db.execute(
            select(WorkoutAssignment, WorkoutPlan.name)
            .join(WorkoutPlan, WorkoutPlan.id == WorkoutAssignment.workout_plan_id)
            .where(*filters)
            .order_by(WorkoutAssignment.assigned_at.desc())
        )
        outs: list[AssignmentOut] = []
        for assignment, plan_name in result.all():
            out = AssignmentOut.model_validate(assignment)
            out.plan_name = plan_name
            outs.append(out)
        return outs
