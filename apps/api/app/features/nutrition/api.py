from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import MealPlan, NotificationLog
from app.infrastructure.notifications import NotificationMessage, get_notification_provider

router = APIRouter(prefix="/api/v1", tags=["nutrition-notifications"])


class MealPlanCreate(BaseModel):
    name: str
    client_id: UUID | None = None
    calories: int | None = None
    protein_g: int | None = None
    carbs_g: int | None = None
    fat_g: int | None = None
    meals: list[dict] = Field(default_factory=list)
    notes: str | None = None


class MealPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    client_id: UUID | None
    name: str
    calories: int | None
    protein_g: int | None
    carbs_g: int | None
    fat_g: int | None
    meals: list
    notes: str | None


class NotifyBody(BaseModel):
    channel: str = "email"
    recipient: str
    subject: str | None = None
    body: str


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    channel: str
    recipient: str
    subject: str | None
    body: str
    status: str
    provider: str


@router.get("/meal-plans", response_model=list[MealPlanOut])
async def list_meal_plans(
    client_id: UUID | None = Query(None),
    principal: AuthPrincipal = Depends(require_permission("client:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[MealPlanOut]:
    filters = [MealPlan.organization_id == org_id(principal), MealPlan.deleted_at.is_(None)]
    if client_id:
        filters.append(MealPlan.client_id == client_id)
    result = await db.execute(select(MealPlan).where(*filters).order_by(MealPlan.updated_at.desc()))
    return [MealPlanOut.model_validate(m) for m in result.scalars().all()]


@router.post("/meal-plans", response_model=MealPlanOut, status_code=201)
async def create_meal_plan(
    body: MealPlanCreate,
    principal: AuthPrincipal = Depends(require_permission("client:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> MealPlanOut:
    row = MealPlan(
        organization_id=org_id(principal),
        **body.model_dump(),
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return MealPlanOut.model_validate(row)


@router.post("/notifications/send", response_model=NotificationOut, status_code=201)
async def send_notification(
    body: NotifyBody,
    principal: AuthPrincipal = Depends(require_permission("settings:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> NotificationOut:
    provider = get_notification_provider()
    status_str = provider.send(
        NotificationMessage(
            channel=body.channel,
            recipient=body.recipient,
            subject=body.subject,
            body=body.body,
        )
    )
    row = NotificationLog(
        organization_id=org_id(principal),
        channel=body.channel,
        recipient=body.recipient,
        subject=body.subject,
        body=body.body,
        status=status_str,
        provider=provider.name,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return NotificationOut.model_validate(row)
