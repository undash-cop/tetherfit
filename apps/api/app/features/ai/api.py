from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import AiGenerationLog
from app.infrastructure.ai import get_ai_provider

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

SYSTEM_JSON = (
    "You are TetherFit Coach Copilot for personal trainers. "
    "Respond with valid JSON only, no markdown."
)


class GenerateIn(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    client_context: dict[str, Any] | None = None


class CopilotIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context: dict[str, Any] | None = None


class AiOut(BaseModel):
    feature: str
    provider: str
    model: str | None
    result: dict[str, Any]
    log_id: UUID


async def _run(
    *,
    db: AsyncSession,
    principal: AuthPrincipal,
    feature: str,
    user_prompt: str,
) -> AiOut:
    provider = get_ai_provider()
    completion = provider.complete(SYSTEM_JSON, user_prompt)
    log = AiGenerationLog(
        organization_id=org_id(principal),
        user_id=principal.user.id,
        feature=feature,
        provider=completion.provider,
        model=completion.model,
        prompt=user_prompt,
        response=completion.content,
        tokens_in=completion.tokens_in,
        tokens_out=completion.tokens_out,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return AiOut(
        feature=feature,
        provider=completion.provider,
        model=completion.model,
        result=completion.content,
        log_id=log.id,
    )


@router.post("/workout", response_model=AiOut)
async def generate_workout(
    body: GenerateIn,
    principal: AuthPrincipal = Depends(require_permission("ai:use")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AiOut:
    ctx = body.client_context or {}
    prompt = (
        f"Generate a workout plan as JSON with keys title, duration_min, items[], notes.\n"
        f"Request: {body.prompt}\nClient context: {ctx}"
    )
    return await _run(db=db, principal=principal, feature="workout_generator", user_prompt=prompt)


@router.post("/diet", response_model=AiOut)
async def generate_diet(
    body: GenerateIn,
    principal: AuthPrincipal = Depends(require_permission("ai:use")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AiOut:
    ctx = body.client_context or {}
    prompt = (
        f"Generate a diet/meal plan as JSON with keys name, calories, protein_g, carbs_g, "
        f"fat_g, meals[].\nRequest: {body.prompt}\nClient context: {ctx}"
    )
    return await _run(db=db, principal=principal, feature="diet_generator", user_prompt=prompt)


@router.post("/session-summary", response_model=AiOut)
async def session_summary(
    body: GenerateIn,
    principal: AuthPrincipal = Depends(require_permission("ai:use")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AiOut:
    ctx = body.client_context or {}
    prompt = (
        f"Write a session summary as JSON with keys summary, highlights[], next_focus[].\n"
        f"Notes: {body.prompt}\nContext: {ctx}"
    )
    return await _run(db=db, principal=principal, feature="session_summary", user_prompt=prompt)


@router.post("/copilot", response_model=AiOut)
async def coach_copilot(
    body: CopilotIn,
    principal: AuthPrincipal = Depends(require_permission("ai:use")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AiOut:
    ctx = body.context or {}
    prompt = (
        f"Coach copilot chat. Reply JSON with reply and suggestions[].\n"
        f"Message: {body.message}\nContext: {ctx}"
    )
    return await _run(db=db, principal=principal, feature="coach_copilot", user_prompt=prompt)


@router.post("/insights", response_model=AiOut)
async def business_insights(
    body: GenerateIn | None = None,
    principal: AuthPrincipal = Depends(require_permission("ai:use")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> AiOut:
    extra = (body.prompt if body else "") or "Analyze my trainer business."
    prompt = (
        f"Produce business insights JSON with insights[] and actions[]. "
        f"Include retention and revenue themes.\nRequest: {extra}\n"
        f"Generated at: {datetime.now(UTC).isoformat()}"
    )
    return await _run(db=db, principal=principal, feature="business_insights", user_prompt=prompt)
