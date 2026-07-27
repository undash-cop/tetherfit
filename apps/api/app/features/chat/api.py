from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import ChatMessage, ChatThread, Client

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ThreadOut(BaseModel):
    id: UUID
    client_id: UUID
    subject: str
    last_message_at: datetime | None

    model_config = {"from_attributes": True}


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: UUID
    thread_id: UUID
    sender_user_id: UUID
    body: str
    created_at: datetime
    read_at: datetime | None

    model_config = {"from_attributes": True}


async def _client_for_user(db: AsyncSession, user_id: UUID) -> Client | None:
    return await db.scalar(
        select(Client).where(Client.linked_user_id == user_id, Client.deleted_at.is_(None))
    )


async def _ensure_thread_access(
    db: AsyncSession, principal: AuthPrincipal, thread: ChatThread
) -> None:
    if principal.is_client():
        client = await _client_for_user(db, principal.user.id)
        if not client or client.id != thread.client_id:
            raise HTTPException(status_code=403, detail="Not your thread")
    elif thread.organization_id != principal.user.organization_id:
        raise HTTPException(status_code=403, detail="Wrong organization")


@router.get("/threads", response_model=list[ThreadOut])
async def list_threads(
    principal: AuthPrincipal = Depends(require_permission("chat:use")),
    db: AsyncSession = Depends(get_db),
) -> list[ChatThread]:
    if principal.is_client():
        client = await _client_for_user(db, principal.user.id)
        if not client:
            return []
        rows = await db.scalars(
            select(ChatThread).where(
                ChatThread.client_id == client.id,
                ChatThread.deleted_at.is_(None),
            )
        )
        return list(rows)
    oid = org_id(principal)
    rows = await db.scalars(
        select(ChatThread)
        .where(ChatThread.organization_id == oid, ChatThread.deleted_at.is_(None))
        .order_by(ChatThread.last_message_at.desc().nullslast())
    )
    return list(rows)


@router.post("/threads/{client_id}", response_model=ThreadOut, status_code=201)
async def open_thread(
    client_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("chat:use")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> ChatThread:
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
    existing = await db.scalar(
        select(ChatThread).where(
            ChatThread.client_id == client_id,
            ChatThread.organization_id == oid,
            ChatThread.deleted_at.is_(None),
        )
    )
    if existing:
        return existing
    thread = ChatThread(
        organization_id=oid,
        client_id=client_id,
        subject=f"Chat · {client.full_name}",
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread


@router.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
async def list_messages(
    thread_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("chat:use")),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessage]:
    thread = await db.get(ChatThread, thread_id)
    if not thread or thread.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Thread not found")
    await _ensure_thread_access(db, principal, thread)
    rows = await db.scalars(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id, ChatMessage.deleted_at.is_(None))
        .order_by(ChatMessage.created_at.asc())
    )
    return list(rows)


@router.post(
    "/threads/{thread_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    thread_id: UUID,
    body: MessageIn,
    principal: AuthPrincipal = Depends(require_permission("chat:use")),
    db: AsyncSession = Depends(get_db),
) -> ChatMessage:
    thread = await db.get(ChatThread, thread_id)
    if not thread or thread.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Thread not found")
    await _ensure_thread_access(db, principal, thread)
    msg = ChatMessage(
        organization_id=thread.organization_id,
        thread_id=thread.id,
        sender_user_id=principal.user.id,
        body=body.body.strip(),
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    thread.last_message_at = datetime.now(UTC)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@router.post("/me/thread", response_model=ThreadOut, status_code=201)
async def open_my_thread(
    principal: AuthPrincipal = Depends(require_permission("chat:use")),
    db: AsyncSession = Depends(get_db),
) -> ChatThread:
    client = await _client_for_user(db, principal.user.id)
    if not client:
        raise HTTPException(status_code=404, detail="No linked client profile")
    existing = await db.scalar(
        select(ChatThread).where(
            ChatThread.client_id == client.id,
            ChatThread.deleted_at.is_(None),
        )
    )
    if existing:
        return existing
    thread = ChatThread(
        organization_id=client.organization_id,
        client_id=client.id,
        subject="Coaching chat",
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread
