from __future__ import annotations

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import (
    AuthPrincipal,
    get_auth_principal,
    org_id,
    require_organization,
    require_permission,
)
from app.domain.models import (
    Assessment,
    Client,
    ClientPortalInvite,
    Invoice,
    MealPlan,
    Organization,
    PtSession,
    SessionPackage,
    User,
    WorkoutAssignment,
    WorkoutPlan,
)
from app.features.sessions.schemas import SessionCreate, SessionOut
from app.features.sessions.services import SessionService

router = APIRouter(prefix="/api/v1", tags=["portal"])


class PortalInviteIn(BaseModel):
    email: EmailStr | None = None


class PortalInviteOut(BaseModel):
    id: UUID
    client_id: UUID
    email: str
    token: str
    status: str
    expires_at: datetime


class PortalHomeOut(BaseModel):
    client_id: UUID
    full_name: str
    organization_name: str
    remaining_credits: int
    upcoming_sessions: int
    active_workouts: int


async def _linked_client(db: AsyncSession, user: User) -> Client:
    client = await db.scalar(
        select(Client).where(
            Client.linked_user_id == user.id,
            Client.deleted_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="No linked client profile")
    return client


@router.post(
    "/clients/{client_id}/portal-invite",
    response_model=PortalInviteOut,
    status_code=status.HTTP_201_CREATED,
)
async def invite_client_portal(
    client_id: UUID,
    body: PortalInviteIn | None = None,
    principal: AuthPrincipal = Depends(require_permission("client:update")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ClientPortalInvite:
    oid = org_id(principal)
    client = await db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == oid,
            Client.deleted_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    email = (body.email if body and body.email else client.email) or ""
    if not email:
        raise HTTPException(status_code=400, detail="Client email required for portal invite")
    invite = ClientPortalInvite(
        organization_id=oid,
        client_id=client.id,
        email=str(email).lower(),
        token=token_urlsafe(24),
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=14),
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


@router.post("/portal/accept-invite/{token}")
async def accept_portal_invite(
    token: str,
    principal: AuthPrincipal = Depends(get_auth_principal),
    db: AsyncSession = Depends(get_db),
) -> dict:
    invite = await db.scalar(
        select(ClientPortalInvite).where(
            ClientPortalInvite.token == token,
            ClientPortalInvite.status == "pending",
            ClientPortalInvite.deleted_at.is_(None),
        )
    )
    if not invite or invite.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invite invalid or expired")
    client = await db.get(Client, invite.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    user = principal.user
    user.organization_id = invite.organization_id
    user.org_role = "client"
    user.onboarding_completed = True
    client.linked_user_id = user.id
    if not client.email:
        client.email = invite.email
    invite.status = "accepted"
    await db.commit()
    return {"status": "linked", "client_id": str(client.id)}


@router.get("/portal/home", response_model=PortalHomeOut)
async def portal_home(
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> PortalHomeOut:
    client = await _linked_client(db, principal.user)
    org = await db.get(Organization, client.organization_id)
    credits = await db.scalar(
        select(func.coalesce(func.sum(SessionPackage.remaining_sessions), 0)).where(
            SessionPackage.client_id == client.id,
            SessionPackage.deleted_at.is_(None),
        )
    )
    upcoming = await db.scalar(
        select(func.count())
        .select_from(PtSession)
        .where(
            PtSession.client_id == client.id,
            PtSession.deleted_at.is_(None),
            PtSession.starts_at >= datetime.now(UTC),
            PtSession.status.in_(["scheduled", "checked_in"]),
        )
    )
    workouts = await db.scalar(
        select(func.count())
        .select_from(WorkoutAssignment)
        .where(
            WorkoutAssignment.client_id == client.id,
            WorkoutAssignment.deleted_at.is_(None),
        )
    )
    return PortalHomeOut(
        client_id=client.id,
        full_name=client.full_name,
        organization_name=org.name if org else "Coach",
        remaining_credits=int(credits or 0),
        upcoming_sessions=int(upcoming or 0),
        active_workouts=int(workouts or 0),
    )


@router.get("/portal/sessions")
async def portal_sessions(
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    client = await _linked_client(db, principal.user)
    rows = await db.scalars(
        select(PtSession)
        .where(PtSession.client_id == client.id, PtSession.deleted_at.is_(None))
        .order_by(PtSession.starts_at.desc())
        .limit(50)
    )
    return [
        {
            "id": str(s.id),
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
            "status": s.status,
            "location": s.location,
            "notes": s.notes,
        }
        for s in rows
    ]


@router.post("/portal/sessions", response_model=SessionOut, status_code=201)
async def portal_book_session(
    body: SessionCreate,
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    client = await _linked_client(db, principal.user)
    body = body.model_copy(update={"client_id": client.id})
    trainer = await db.scalar(
        select(User).where(
            User.organization_id == client.organization_id,
            User.org_role.in_(["business_owner", "trainer"]),
            User.deleted_at.is_(None),
        )
    )
    trainer_id = trainer.id if trainer else principal.user.id
    return await SessionService(db).create(client.organization_id, trainer_id, body)


@router.get("/portal/workouts")
async def portal_workouts(
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    client = await _linked_client(db, principal.user)
    assignments = await db.scalars(
        select(WorkoutAssignment).where(
            WorkoutAssignment.client_id == client.id,
            WorkoutAssignment.deleted_at.is_(None),
        )
    )
    out = []
    for a in assignments:
        plan = await db.get(WorkoutPlan, a.workout_plan_id)
        out.append(
            {
                "assignment_id": str(a.id),
                "plan_id": str(a.workout_plan_id),
                "plan_name": plan.name if plan else "Workout",
                "items": plan.items if plan else [],
                "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
            }
        )
    return out


@router.get("/portal/nutrition")
async def portal_nutrition(
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    client = await _linked_client(db, principal.user)
    rows = await db.scalars(
        select(MealPlan).where(
            MealPlan.client_id == client.id,
            MealPlan.deleted_at.is_(None),
        )
    )
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "calories": m.calories,
            "protein_g": m.protein_g,
            "carbs_g": m.carbs_g,
            "fat_g": m.fat_g,
            "meals": m.meals,
        }
        for m in rows
    ]


@router.get("/portal/progress")
async def portal_progress(
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    client = await _linked_client(db, principal.user)
    rows = await db.scalars(
        select(Assessment)
        .where(Assessment.client_id == client.id, Assessment.deleted_at.is_(None))
        .order_by(Assessment.recorded_at.desc())
        .limit(40)
    )
    return [
        {
            "id": str(a.id),
            "recorded_at": a.recorded_at.isoformat(),
            "weight_kg": a.weight_kg,
            "bmi": a.bmi,
            "body_fat_pct": a.body_fat_pct,
        }
        for a in rows
    ]


@router.get("/portal/payments")
async def portal_payments(
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    client = await _linked_client(db, principal.user)
    rows = await db.scalars(
        select(Invoice)
        .where(Invoice.client_id == client.id, Invoice.deleted_at.is_(None))
        .order_by(Invoice.created_at.desc())
        .limit(40)
    )
    return [
        {
            "id": str(i.id),
            "invoice_number": i.invoice_number,
            "status": i.status,
            "total_paise": i.total_paise,
            "currency": i.currency,
            "due_at": i.due_at.isoformat() if i.due_at else None,
        }
        for i in rows
    ]


class ProfilePatch(BaseModel):
    goals: str | None = None
    phone: str | None = Field(default=None, max_length=32)


@router.patch("/portal/profile")
async def portal_profile_patch(
    body: ProfilePatch,
    principal: AuthPrincipal = Depends(require_permission("portal:access")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    client = await _linked_client(db, principal.user)
    if body.goals is not None:
        client.goals = body.goals
    if body.phone is not None:
        client.phone = body.phone
    await db.commit()
    return {"id": str(client.id), "goals": client.goals, "phone": client.phone}
