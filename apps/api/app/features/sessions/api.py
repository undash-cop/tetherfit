from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.features.sessions.schemas import (
    FinishSessionBody,
    SessionCreate,
    SessionOut,
    SessionUpdate,
)
from app.features.sessions.services import SessionService

router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.get("/sessions", response_model=list[SessionOut])
@router.get("/calendar", response_model=list[SessionOut])
async def list_sessions(
    from_: datetime = Query(..., alias="from"),
    to: datetime = Query(...),
    client_id: UUID | None = None,
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[SessionOut]:
    # session:create as baseline calendar access; also allow with client:view via reports?
    # Using session:create from trainer pack; business_owner has all.
    return await SessionService(db).list_range(
        org_id(principal), start=from_, end=to, client_id=client_id
    )


@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(
    body: SessionCreate,
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).create(org_id(principal), principal.user.id, body)


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).get(org_id(principal), session_id)


@router.patch("/sessions/{session_id}", response_model=SessionOut)
async def update_session(
    session_id: UUID,
    body: SessionUpdate,
    principal: AuthPrincipal = Depends(require_permission("session:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).update(org_id(principal), session_id, body, principal.user.id)


@router.post("/sessions/{session_id}/check-in", response_model=SessionOut)
async def check_in_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:start")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).check_in(org_id(principal), session_id)


@router.post("/sessions/{session_id}/start", response_model=SessionOut)
async def start_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:start")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).start(org_id(principal), session_id)


@router.post("/sessions/{session_id}/pause", response_model=SessionOut)
async def pause_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:start")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).pause(org_id(principal), session_id)


@router.post("/sessions/{session_id}/resume", response_model=SessionOut)
async def resume_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:start")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).resume(org_id(principal), session_id)


@router.post("/sessions/{session_id}/finish", response_model=SessionOut)
async def finish_session(
    session_id: UUID,
    body: FinishSessionBody | None = None,
    principal: AuthPrincipal = Depends(require_permission("session:finish")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).finish(org_id(principal), session_id, body)


@router.post("/sessions/{session_id}/cancel", response_model=SessionOut)
async def cancel_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:cancel")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).cancel(org_id(principal), session_id)


@router.post("/sessions/{session_id}/no-show", response_model=SessionOut)
async def no_show_session(
    session_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("session:cancel")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await SessionService(db).mark_no_show(org_id(principal), session_id)
