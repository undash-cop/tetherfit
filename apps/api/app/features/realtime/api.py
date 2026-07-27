from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, get_db
from app.core.deps import AuthPrincipal, require_permission
from app.core.security import decode_access_token
from app.domain.models import PushSubscription
from app.features.users.repositories import UserRepository
from app.infrastructure.realtime import chat_hub

router = APIRouter(prefix="/api/v1", tags=["realtime"])


class PushIn(BaseModel):
    endpoint: str = Field(min_length=8)
    p256dh: str
    auth: str
    user_agent: str | None = None


class PushOut(BaseModel):
    id: UUID
    endpoint: str

    model_config = {"from_attributes": True}


@router.post("/push/subscribe", response_model=PushOut, status_code=201)
async def subscribe_push(
    body: PushIn,
    principal: AuthPrincipal = Depends(require_permission("chat:use")),
    db: AsyncSession = Depends(get_db),
) -> PushSubscription:
    existing = await db.scalar(
        select(PushSubscription).where(
            PushSubscription.user_id == principal.user.id,
            PushSubscription.endpoint == body.endpoint,
            PushSubscription.deleted_at.is_(None),
        )
    )
    if existing:
        existing.p256dh = body.p256dh
        existing.auth = body.auth
        await db.commit()
        await db.refresh(existing)
        return existing
    row = PushSubscription(
        organization_id=principal.user.organization_id,
        user_id=principal.user.id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        user_agent=body.user_agent,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/push/vapid-public-key")
async def vapid_public_key() -> dict:
    settings = get_settings()
    return {"publicKey": getattr(settings, "vapid_public_key", "") or ""}


@router.websocket("/ws/chat/{thread_id}")
async def chat_websocket(websocket: WebSocket, thread_id: UUID) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    settings = get_settings()
    try:
        payload = decode_access_token(token, settings)
        sub = payload.get("sub")
        if not sub:
            raise ValueError("missing sub")
    except Exception:
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_keycloak_id(str(sub))
        if not user:
            await websocket.close(code=4401)
            return
        user_id = user.id

    await chat_hub.connect(thread_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "thread_id": str(thread_id)})
        while True:
            data = await websocket.receive_json()
            body = str(data.get("body") or "").strip()
            if not body:
                continue
            # Persist via REST pattern inline
            from datetime import UTC, datetime

            from app.domain.models import ChatMessage, ChatThread

            async with AsyncSessionLocal() as db:
                thread = await db.get(ChatThread, thread_id)
                if not thread or thread.deleted_at is not None:
                    await websocket.send_json({"type": "error", "detail": "Thread not found"})
                    continue
                msg = ChatMessage(
                    organization_id=thread.organization_id,
                    thread_id=thread.id,
                    sender_user_id=user_id,
                    body=body,
                    created_by=user_id,
                    updated_by=user_id,
                )
                thread.last_message_at = datetime.now(UTC)
                db.add(msg)
                await db.commit()
                await db.refresh(msg)
                event = {
                    "type": "message",
                    "id": str(msg.id),
                    "thread_id": str(thread_id),
                    "sender_user_id": str(user_id),
                    "body": msg.body,
                    "created_at": msg.created_at.isoformat(),
                }
            await chat_hub.broadcast(thread_id, event)
    except WebSocketDisconnect:
        chat_hub.disconnect(thread_id, websocket)
