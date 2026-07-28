#!/usr/bin/env python3
"""Seed demo org, trainer, clients, packages, sessions, and an invoice.

Usage (from repo root, with DATABASE_URL set):

  cd apps/api && python ../../scripts/seed_demo.py

Or:

  PYTHONPATH=apps/api python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

# Allow running from repo root without install
ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models import (
    Client,
    ClientStatus,
    Invoice,
    InvoiceStatus,
    Organization,
    PtSession,
    SessionPackage,
    SessionStatus,
    User,
)

DEMO_ORG_SLUG = "demo-studio"
DEMO_KEYCLOAK_ID = "demo-owner-keycloak"
DEMO_ORG_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
DEMO_USER_ID = UUID("11111111-2222-3333-4444-555555555555")
DEMO_CLIENT_IDS = (
    UUID("c1000000-0000-0000-0000-000000000001"),
    UUID("c1000000-0000-0000-0000-000000000002"),
)


async def seed(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    org = await session.scalar(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    if not org:
        org = Organization(
            id=DEMO_ORG_ID,
            name="Demo Studio",
            slug=DEMO_ORG_SLUG,
            timezone="Asia/Kolkata",
            working_hours={},
            feature_flags={},
            created_at=now,
            updated_at=now,
        )
        session.add(org)
        await session.flush()

    user = await session.scalar(select(User).where(User.keycloak_user_id == DEMO_KEYCLOAK_ID))
    if not user:
        user = User(
            id=DEMO_USER_ID,
            keycloak_user_id=DEMO_KEYCLOAK_ID,
            organization_id=org.id,
            email="owner@demo.tetherfit.local",
            full_name="Demo Trainer",
            onboarding_completed=True,
            org_role="business_owner",
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        await session.flush()
    else:
        user.organization_id = org.id
        user.onboarding_completed = True

    clients: list[Client] = []
    for i, cid in enumerate(DEMO_CLIENT_IDS):
        client = await session.get(Client, cid)
        if not client:
            client = Client(
                id=cid,
                organization_id=org.id,
                full_name=f"Demo Client {i + 1}",
                email=f"client{i + 1}@demo.tetherfit.local",
                phone=f"+91987654321{i}",
                status=ClientStatus.ACTIVE,
                goals="Strength + fat loss",
                tags=["demo"],
                created_at=now,
                updated_at=now,
            )
            session.add(client)
        clients.append(client)
    await session.flush()

    for client in clients:
        existing_pkg = await session.scalar(
            select(SessionPackage).where(
                SessionPackage.client_id == client.id,
                SessionPackage.deleted_at.is_(None),
            )
        )
        if not existing_pkg:
            session.add(
                SessionPackage(
                    id=uuid4(),
                    organization_id=org.id,
                    client_id=client.id,
                    total_sessions=10,
                    remaining_sessions=8,
                    notes="Demo pack",
                    created_at=now,
                    updated_at=now,
                )
            )

        existing_session = await session.scalar(
            select(PtSession).where(
                PtSession.client_id == client.id,
                PtSession.deleted_at.is_(None),
            )
        )
        if not existing_session:
            start = now.replace(minute=0, second=0, microsecond=0) + timedelta(days=1, hours=9)
            session.add(
                PtSession(
                    id=uuid4(),
                    organization_id=org.id,
                    client_id=client.id,
                    trainer_id=user.id,
                    starts_at=start,
                    ends_at=start + timedelta(hours=1),
                    status=SessionStatus.SCHEDULED,
                    location="Demo gym floor",
                    created_at=now,
                    updated_at=now,
                )
            )

    invoice = await session.scalar(
        select(Invoice).where(
            Invoice.organization_id == org.id,
            Invoice.invoice_number == "TF-DEMO-0001",
        )
    )
    if not invoice:
        session.add(
            Invoice(
                id=uuid4(),
                organization_id=org.id,
                client_id=clients[0].id,
                invoice_number="TF-DEMO-0001",
                status=InvoiceStatus.SENT,
                currency="INR",
                subtotal_paise=1000000,
                tax_paise=180000,
                total_paise=1180000,
                line_items=[{"description": "10-session pack", "quantity": 1, "unit_paise": 1000000}],
                notes="Demo invoice",
                created_at=now,
                updated_at=now,
            )
        )

    await session.commit()
    print(f"Seeded org slug={org.slug} id={org.id}")
    print(f"Owner keycloak_user_id={DEMO_KEYCLOAK_ID} email=owner@demo.tetherfit.local")
    print(f"Clients: {', '.join(str(c) for c in DEMO_CLIENT_IDS)}")


async def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        from app.core.config import get_settings

        url = get_settings().database_url
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
