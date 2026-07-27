from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import MediaAsset
from app.infrastructure.r2 import create_presigned_put, public_url_for_key

router = APIRouter(prefix="/api/v1/media", tags=["media"])


class PresignIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=128)
    kind: str = "attachment"
    client_id: UUID | None = None
    size_bytes: int = Field(default=0, ge=0)


class PresignOut(BaseModel):
    asset_id: UUID
    upload_url: str
    object_key: str
    public_url: str | None
    headers: dict[str, str]


@router.post("/presign", response_model=PresignOut)
async def presign_upload(
    body: PresignIn,
    principal: AuthPrincipal = Depends(require_permission("media:upload")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> PresignOut:
    oid = org_id(principal)
    safe_name = body.filename.replace("/", "_")
    key = f"orgs/{oid}/{body.kind}/{uuid4().hex}_{safe_name}"
    upload_url, headers = create_presigned_put(key, body.content_type)
    if not upload_url:
        # Local/dev fallback: record asset; client can skip binary upload
        upload_url = f"local://upload/{key}"
        headers = {"Content-Type": body.content_type}
    url = public_url_for_key(key)
    asset = MediaAsset(
        organization_id=oid,
        uploaded_by=principal.user.id,
        client_id=body.client_id,
        kind=body.kind,
        object_key=key,
        content_type=body.content_type,
        size_bytes=body.size_bytes,
        public_url=url,
        meta={"filename": body.filename},
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return PresignOut(
        asset_id=asset.id,
        upload_url=upload_url,
        object_key=key,
        public_url=url,
        headers=headers,
    )


@router.get("/{asset_id}")
async def get_asset(
    asset_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("media:upload")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> dict:
    asset = await db.get(MediaAsset, asset_id)
    if not asset or asset.organization_id != org_id(principal):
        raise HTTPException(status_code=404, detail="Asset not found")
    settings = get_settings()
    return {
        "id": str(asset.id),
        "object_key": asset.object_key,
        "public_url": asset.public_url or public_url_for_key(asset.object_key, settings),
        "content_type": asset.content_type,
        "kind": asset.kind,
    }
