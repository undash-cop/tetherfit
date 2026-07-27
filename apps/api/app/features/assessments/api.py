from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Assessment, Client

router = APIRouter(prefix="/api/v1", tags=["assessments"])


class AssessmentCreate(BaseModel):
    client_id: UUID
    recorded_at: datetime
    weight_kg: float | None = None
    height_cm: float | None = None
    body_fat_pct: float | None = None
    measurements: dict = Field(default_factory=dict)
    photo_urls: list[str] = Field(default_factory=list)
    notes: str | None = None


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    client_id: UUID
    recorded_at: datetime
    weight_kg: float | None
    height_cm: float | None
    body_fat_pct: float | None
    measurements: dict
    photo_urls: list
    notes: str | None
    bmi: float | None = None


def _bmi(weight_kg: float | None, height_cm: float | None) -> float | None:
    if not weight_kg or not height_cm or height_cm <= 0:
        return None
    meters = height_cm / 100
    return round(weight_kg / (meters * meters), 1)


@router.get("/assessments", response_model=list[AssessmentOut])
async def list_assessments(
    client_id: UUID = Query(...),
    principal: AuthPrincipal = Depends(require_permission("client:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[AssessmentOut]:
    result = await db.execute(
        select(Assessment)
        .where(
            Assessment.organization_id == org_id(principal),
            Assessment.client_id == client_id,
            Assessment.deleted_at.is_(None),
        )
        .order_by(Assessment.recorded_at.desc())
    )
    outs: list[AssessmentOut] = []
    for row in result.scalars().all():
        out = AssessmentOut.model_validate(row)
        out.bmi = _bmi(row.weight_kg, row.height_cm)
        outs.append(out)
    return outs


@router.post("/assessments", response_model=AssessmentOut, status_code=201)
async def create_assessment(
    body: AssessmentCreate,
    principal: AuthPrincipal = Depends(require_permission("client:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AssessmentOut:
    oid = org_id(principal)
    client = await db.scalar(
        select(Client).where(
            Client.id == body.client_id,
            Client.organization_id == oid,
            Client.deleted_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    row = Assessment(
        organization_id=oid,
        client_id=body.client_id,
        recorded_at=body.recorded_at,
        weight_kg=body.weight_kg,
        height_cm=body.height_cm,
        body_fat_pct=body.body_fat_pct,
        measurements=body.measurements,
        photo_urls=body.photo_urls,
        notes=body.notes,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    out = AssessmentOut.model_validate(row)
    out.bmi = _bmi(row.weight_kg, row.height_cm)
    return out
