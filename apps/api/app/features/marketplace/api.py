from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import MarketplaceInquiry, MarketplaceListing

router = APIRouter(prefix="/api/v1", tags=["marketplace"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "listing"


class ListingIn(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    headline: str | None = None
    bio: str | None = None
    city: str | None = None
    specialties: list[str] = Field(default_factory=list)
    session_rate_paise: int | None = Field(default=None, ge=0)
    currency: str = "INR"
    is_published: bool = False
    cover_image_url: str | None = None
    slug: str | None = None


class ListingOut(BaseModel):
    id: UUID
    slug: str
    title: str
    headline: str | None
    bio: str | None
    city: str | None
    specialties: list
    session_rate_paise: int | None
    currency: str
    is_published: bool
    cover_image_url: str | None

    model_config = {"from_attributes": True}


class InquiryIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: str | None = None
    message: str = Field(min_length=5, max_length=4000)


class InquiryOut(BaseModel):
    id: UUID
    listing_id: UUID
    name: str
    email: str
    phone: str | None
    message: str
    status: str

    model_config = {"from_attributes": True}


@router.get("/marketplace/listings", response_model=list[ListingOut])
async def my_listings(
    principal: AuthPrincipal = Depends(require_permission("marketplace:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[MarketplaceListing]:
    oid = org_id(principal)
    rows = await db.scalars(
        select(MarketplaceListing).where(
            MarketplaceListing.organization_id == oid,
            MarketplaceListing.deleted_at.is_(None),
        )
    )
    return list(rows)


@router.post(
    "/marketplace/listings",
    response_model=ListingOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_listing(
    body: ListingIn,
    principal: AuthPrincipal = Depends(require_permission("marketplace:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> MarketplaceListing:
    slug = _slugify(body.slug or body.title)
    exists = await db.scalar(select(MarketplaceListing).where(MarketplaceListing.slug == slug))
    if exists:
        slug = f"{slug}-{str(org_id(principal))[:8]}"
    row = MarketplaceListing(
        organization_id=org_id(principal),
        slug=slug,
        title=body.title,
        headline=body.headline,
        bio=body.bio,
        city=body.city,
        specialties=body.specialties,
        session_rate_paise=body.session_rate_paise,
        currency=body.currency,
        is_published=body.is_published,
        cover_image_url=body.cover_image_url,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/marketplace/listings/{listing_id}", response_model=ListingOut)
async def update_listing(
    listing_id: UUID,
    body: ListingIn,
    principal: AuthPrincipal = Depends(require_permission("marketplace:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> MarketplaceListing:
    oid = org_id(principal)
    row = await db.scalar(
        select(MarketplaceListing).where(
            MarketplaceListing.id == listing_id,
            MarketplaceListing.organization_id == oid,
            MarketplaceListing.deleted_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "slug" and value:
            setattr(row, field, _slugify(value))
        else:
            setattr(row, field, value)
    row.updated_by = principal.user.id
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/marketplace/inquiries", response_model=list[InquiryOut])
async def list_inquiries(
    principal: AuthPrincipal = Depends(require_permission("marketplace:manage")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[MarketplaceInquiry]:
    oid = org_id(principal)
    rows = await db.scalars(
        select(MarketplaceInquiry)
        .where(
            MarketplaceInquiry.organization_id == oid,
            MarketplaceInquiry.deleted_at.is_(None),
        )
        .order_by(MarketplaceInquiry.created_at.desc())
    )
    return list(rows)


@router.get("/public/marketplace", response_model=list[ListingOut])
async def public_discover(
    city: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[MarketplaceListing]:
    stmt = select(MarketplaceListing).where(
        MarketplaceListing.is_published.is_(True),
        MarketplaceListing.deleted_at.is_(None),
    )
    if city:
        stmt = stmt.where(MarketplaceListing.city.ilike(f"%{city}%"))
    if q:
        stmt = stmt.where(MarketplaceListing.title.ilike(f"%{q}%"))
    rows = await db.scalars(stmt.limit(50))
    return list(rows)


@router.get("/public/marketplace/{slug}", response_model=ListingOut)
async def public_listing(slug: str, db: AsyncSession = Depends(get_db)) -> MarketplaceListing:
    row = await db.scalar(
        select(MarketplaceListing).where(
            MarketplaceListing.slug == slug,
            MarketplaceListing.is_published.is_(True),
            MarketplaceListing.deleted_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    return row


@router.post(
    "/public/marketplace/{slug}/inquire",
    response_model=InquiryOut,
    status_code=status.HTTP_201_CREATED,
)
async def public_inquire(
    slug: str,
    body: InquiryIn,
    db: AsyncSession = Depends(get_db),
) -> MarketplaceInquiry:
    listing = await db.scalar(
        select(MarketplaceListing).where(
            MarketplaceListing.slug == slug,
            MarketplaceListing.is_published.is_(True),
            MarketplaceListing.deleted_at.is_(None),
        )
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    inquiry = MarketplaceInquiry(
        organization_id=listing.organization_id,
        listing_id=listing.id,
        name=body.name,
        email=str(body.email),
        phone=body.phone,
        message=body.message,
        status="new",
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry
