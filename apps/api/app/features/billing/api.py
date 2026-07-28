import json
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Client, Invoice, InvoiceStatus, Payment, PaymentStatus
from app.infrastructure.payments import get_payment_provider
from app.infrastructure.razorpay_webhook import verify_razorpay_webhook_signature

router = APIRouter(prefix="/api/v1", tags=["billing"])


class LineItem(BaseModel):
    description: str
    quantity: int = 1
    unit_paise: int = Field(ge=0)


class InvoiceCreate(BaseModel):
    client_id: UUID
    line_items: list[LineItem]
    tax_paise: int = 0
    discount_paise: int = Field(default=0, ge=0)
    notes: str | None = None
    due_at: datetime | None = None


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    client_id: UUID
    invoice_number: str
    status: str
    currency: str
    subtotal_paise: int
    discount_paise: int = 0
    tax_paise: int
    total_paise: int
    line_items: list
    notes: str | None
    due_at: datetime | None
    created_at: datetime


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    invoice_id: UUID | None
    client_id: UUID
    provider: str
    provider_order_id: str | None
    provider_payment_id: str | None
    amount_paise: int
    currency: str
    status: str
    method: str | None
    created_at: datetime
    checkout: dict | None = None


class CollectPaymentBody(BaseModel):
    invoice_id: UUID


class ConfirmPaymentBody(BaseModel):
    payment_id: UUID
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None
    provider_payment_id: str | None = None
    method: str | None = "upi"


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    principal: AuthPrincipal = Depends(require_permission("invoice:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceOut]:
    result = await db.execute(
        select(Invoice)
        .where(Invoice.organization_id == org_id(principal), Invoice.deleted_at.is_(None))
        .order_by(Invoice.created_at.desc())
    )
    return [InvoiceOut.model_validate(i) for i in result.scalars().all()]


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    principal: AuthPrincipal = Depends(require_permission("invoice:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> InvoiceOut:
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
    subtotal = sum(i.quantity * i.unit_paise for i in body.line_items)
    discount = min(body.discount_paise, subtotal)
    count = await db.scalar(
        select(func.count()).select_from(Invoice).where(Invoice.organization_id == oid)
    )
    number = f"TF-{(count or 0) + 1:05d}"
    row = Invoice(
        organization_id=oid,
        client_id=body.client_id,
        invoice_number=number,
        status=InvoiceStatus.SENT,
        subtotal_paise=subtotal,
        discount_paise=discount,
        tax_paise=body.tax_paise,
        total_paise=max(0, subtotal - discount) + body.tax_paise,
        line_items=[i.model_dump() for i in body.line_items],
        notes=body.notes,
        due_at=body.due_at,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return InvoiceOut.model_validate(row)


@router.get("/payments", response_model=list[PaymentOut])
async def list_payments(
    principal: AuthPrincipal = Depends(require_permission("payment:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[PaymentOut]:
    result = await db.execute(
        select(Payment)
        .where(Payment.organization_id == org_id(principal), Payment.deleted_at.is_(None))
        .order_by(Payment.created_at.desc())
    )
    return [PaymentOut.model_validate(p) for p in result.scalars().all()]


@router.post("/payments/collect", response_model=PaymentOut, status_code=201)
async def collect_payment(
    body: CollectPaymentBody,
    principal: AuthPrincipal = Depends(require_permission("payment:collect")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> PaymentOut:
    oid = org_id(principal)
    invoice = await db.scalar(
        select(Invoice).where(
            Invoice.id == body.invoice_id,
            Invoice.organization_id == oid,
            Invoice.deleted_at.is_(None),
        )
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    provider = get_payment_provider()
    order = provider.create_order(
        invoice.total_paise, invoice.currency, receipt=invoice.invoice_number
    )
    payment = Payment(
        organization_id=oid,
        invoice_id=invoice.id,
        client_id=invoice.client_id,
        provider=order.provider,
        provider_order_id=order.order_id,
        amount_paise=order.amount_paise,
        currency=order.currency,
        status=PaymentStatus.PENDING,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    out = PaymentOut.model_validate(payment)
    out.checkout = order.checkout_payload
    return out


@router.post("/payments/confirm", response_model=PaymentOut)
async def confirm_payment(
    body: ConfirmPaymentBody,
    principal: AuthPrincipal = Depends(require_permission("payment:collect")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> PaymentOut:
    oid = org_id(principal)
    payment = await db.scalar(
        select(Payment).where(
            Payment.id == body.payment_id,
            Payment.organization_id == oid,
            Payment.deleted_at.is_(None),
        )
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    provider = get_payment_provider()
    payload = body.model_dump()
    if not provider.verify_payment(payload):
        payment.status = PaymentStatus.FAILED
        await db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed")
    payment.status = PaymentStatus.SUCCESS
    payment.provider_payment_id = (
        body.razorpay_payment_id or body.provider_payment_id or str(uuid4())
    )
    payment.method = body.method
    payment.raw_payload = payload
    if payment.invoice_id:
        invoice = await db.scalar(select(Invoice).where(Invoice.id == payment.invoice_id))
        if invoice:
            invoice.status = InvoiceStatus.PAID
    await db.flush()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)


@router.post("/payments/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: str | None = Header(default=None, alias="X-Razorpay-Signature"),
) -> dict:
    """Public Razorpay webhook — signature verified; rate-limited by IP middleware."""
    raw = await request.body()
    settings = get_settings()
    secret = settings.razorpay_webhook_secret
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )
    if not x_razorpay_signature or not verify_razorpay_webhook_signature(
        raw, x_razorpay_signature, secret
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from exc

    event = payload.get("event")
    if event != "payment.captured":
        return {"status": "ignored", "event": event}

    entity = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    order_id = entity.get("order_id")
    payment_id = entity.get("id")
    method = entity.get("method")
    if not order_id:
        return {"status": "ignored", "reason": "missing_order_id"}

    payment = await db.scalar(
        select(Payment).where(
            Payment.provider_order_id == order_id,
            Payment.deleted_at.is_(None),
        )
    )
    if not payment:
        return {"status": "ignored", "reason": "payment_not_found"}
    if payment.status == PaymentStatus.SUCCESS:
        return {"status": "ok", "idempotent": True}

    payment.status = PaymentStatus.SUCCESS
    payment.provider_payment_id = payment_id or payment.provider_payment_id
    payment.method = method or payment.method
    payment.raw_payload = payload
    if payment.invoice_id:
        invoice = await db.scalar(select(Invoice).where(Invoice.id == payment.invoice_id))
        if invoice:
            invoice.status = InvoiceStatus.PAID
    await db.commit()
    return {"status": "ok", "payment_id": str(payment.id)}


class RefundBody(BaseModel):
    amount_paise: int | None = Field(default=None, ge=1)
    reason: str | None = None


@router.post("/payments/{payment_id}/refund", response_model=PaymentOut)
async def refund_payment(
    payment_id: UUID,
    body: RefundBody,
    principal: AuthPrincipal = Depends(require_permission("payment:collect")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> PaymentOut:
    from datetime import UTC, datetime

    oid = org_id(principal)
    payment = await db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.organization_id == oid,
            Payment.deleted_at.is_(None),
        )
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status not in {PaymentStatus.SUCCESS, PaymentStatus.REFUNDED}:
        raise HTTPException(status_code=400, detail="Only successful payments can be refunded")
    amount = body.amount_paise or payment.amount_paise
    remaining = payment.amount_paise - payment.refunded_paise
    if amount > remaining:
        raise HTTPException(status_code=400, detail="Refund exceeds remaining amount")
    payment.refunded_paise += amount
    payment.refunded_at = datetime.now(UTC)
    payment.refund_reason = body.reason
    payment.status = PaymentStatus.REFUNDED
    payment.updated_by = principal.user.id
    if payment.invoice_id and payment.refunded_paise >= payment.amount_paise:
        invoice = await db.scalar(select(Invoice).where(Invoice.id == payment.invoice_id))
        if invoice:
            invoice.status = InvoiceStatus.VOID
    await db.commit()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)


class MembershipIn(BaseModel):
    client_id: UUID
    name: str = Field(min_length=2, max_length=255)
    amount_paise: int = Field(ge=0)
    currency: str = "INR"
    interval: str = Field(default="monthly", pattern="^(weekly|monthly|quarterly)$")
    sessions_per_period: int | None = Field(default=None, ge=1)
    next_billing_at: datetime | None = None


class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    name: str
    status: str
    amount_paise: int
    currency: str
    interval: str
    next_billing_at: datetime | None
    sessions_per_period: int | None


@router.get("/memberships", response_model=list[MembershipOut])
async def list_memberships(
    principal: AuthPrincipal = Depends(require_permission("invoice:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list:
    from app.domain.models import Membership

    rows = await db.scalars(
        select(Membership).where(
            Membership.organization_id == org_id(principal),
            Membership.deleted_at.is_(None),
        )
    )
    return list(rows)


@router.post("/memberships", response_model=MembershipOut, status_code=201)
async def create_membership(
    body: MembershipIn,
    principal: AuthPrincipal = Depends(require_permission("invoice:create")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> MembershipOut:
    from app.domain.models import Membership

    oid = org_id(principal)
    client = await db.scalar(
        select(Client).where(
            Client.id == body.client_id,
            Client.organization_id == oid,
            Client.deleted_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    row = Membership(
        organization_id=oid,
        client_id=body.client_id,
        name=body.name,
        amount_paise=body.amount_paise,
        currency=body.currency,
        interval=body.interval,
        sessions_per_period=body.sessions_per_period,
        next_billing_at=body.next_billing_at,
        status="active",
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return MembershipOut.model_validate(row)
