import html
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import UTC, datetime
from urllib.parse import quote, urlencode
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import AuthPrincipal, org_id, require_organization, require_permission
from app.domain.models import Client, Invoice, InvoiceStatus, Organization, Payment, PaymentStatus
from app.infrastructure.payments import get_payment_provider
from app.infrastructure.razorpay_webhook import verify_razorpay_webhook_signature

router = APIRouter(prefix="/api/v1", tags=["billing"])


class LineItem(BaseModel):
    description: str
    quantity: int = 1
    unit_paise: int = Field(ge=0)
    meta: dict | None = None


class InvoiceCreate(BaseModel):
    client_id: UUID
    line_items: list[LineItem]
    tax_paise: int | None = None
    discount_paise: int = Field(default=0, ge=0)
    apply_default_gst: bool = True
    tax_inclusive: bool = False
    pt_duration: str | None = None
    terms_and_conditions: list[str] = Field(default_factory=list)
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


class CashPaymentBody(BaseModel):
    invoice_id: UUID
    notes: str | None = None


class UpiQrOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    amount_paise: int
    currency: str
    upi_vpa: str
    upi_uri: str
    qr_image_url: str


def _compute_tax_paise(
    taxable: int,
    *,
    tax_paise: int | None,
    apply_default_gst: bool,
    default_gst_pct: float,
) -> int:
    if tax_paise is not None:
        return max(0, tax_paise)
    if apply_default_gst and default_gst_pct > 0:
        return int(round(taxable * (default_gst_pct / 100.0)))
    return 0


def _split_inclusive_tax_paise(gross: int, gst_pct: float) -> tuple[int, int]:
    """Split a GST-inclusive gross into taxable base and tax (both in paise)."""
    if gross <= 0 or gst_pct <= 0:
        return gross, 0
    ratio = Decimal("100") / (Decimal("100") + Decimal(str(gst_pct)))
    taxable = int((Decimal(gross) * ratio).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    taxable = min(gross, max(0, taxable))
    return taxable, gross - taxable


def _build_upi_uri(*, vpa: str, amount_paise: int, note: str) -> str:
    rupees = f"{amount_paise / 100:.2f}"
    params = urlencode(
        {
            "pa": vpa,
            "am": rupees,
            "cu": "INR",
            "tn": note[:80],
        }
    )
    return f"upi://pay?{params}"


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    client_id: UUID | None = None,
    principal: AuthPrincipal = Depends(require_permission("invoice:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceOut]:
    filters = [
        Invoice.organization_id == org_id(principal),
        Invoice.deleted_at.is_(None),
    ]
    if client_id is not None:
        filters.append(Invoice.client_id == client_id)
    result = await db.execute(select(Invoice).where(*filters).order_by(Invoice.created_at.desc()))
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
    org = await db.scalar(select(Organization).where(Organization.id == oid))
    subtotal = sum(i.quantity * i.unit_paise for i in body.line_items)
    discount = min(body.discount_paise, subtotal)
    gross_after_discount = max(0, subtotal - discount)
    default_gst_pct = float(org.default_gst_pct if org else 0)
    if body.tax_inclusive:
        if body.tax_paise is not None:
            tax = min(max(0, body.tax_paise), gross_after_discount)
            taxable = gross_after_discount - tax
        else:
            taxable, tax = _split_inclusive_tax_paise(gross_after_discount, default_gst_pct)
        total = gross_after_discount
    else:
        taxable = gross_after_discount
        tax = _compute_tax_paise(
            taxable,
            tax_paise=body.tax_paise,
            apply_default_gst=body.apply_default_gst,
            default_gst_pct=default_gst_pct,
        )
        total = taxable + tax
    count = await db.scalar(
        select(func.count()).select_from(Invoice).where(Invoice.organization_id == oid)
    )
    number = f"TF-{(count or 0) + 1:05d}"
    line_items = [i.model_dump() for i in body.line_items]
    if line_items:
        existing_meta = line_items[0].get("meta") or {}
        terms = [t.strip() for t in body.terms_and_conditions if t and t.strip()]
        line_items[0]["meta"] = {
            **existing_meta,
            "tax_inclusive": body.tax_inclusive,
            "pt_duration": body.pt_duration,
            "terms_and_conditions": terms,
        }
    row = Invoice(
        organization_id=oid,
        client_id=body.client_id,
        invoice_number=number,
        status=InvoiceStatus.SENT,
        subtotal_paise=subtotal,
        discount_paise=discount,
        tax_paise=tax,
        total_paise=total,
        line_items=line_items,
        notes=body.notes,
        due_at=body.due_at,
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return InvoiceOut.model_validate(row)


@router.get("/invoices/{invoice_id}/upi-qr", response_model=UpiQrOut)
async def invoice_upi_qr(
    invoice_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("payment:collect")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> UpiQrOut:
    oid = org_id(principal)
    invoice = await db.scalar(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.organization_id == oid,
            Invoice.deleted_at.is_(None),
        )
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    org = await db.scalar(select(Organization).where(Organization.id == oid))
    vpa = (org.upi_vpa if org else None) or ""
    if not vpa.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set UPI VPA in Settings before generating a QR",
        )
    upi_uri = _build_upi_uri(
        vpa=vpa.strip(),
        amount_paise=invoice.total_paise,
        note=f"{invoice.invoice_number} TetherFit",
    )
    qr_image_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=280x280&data=" + quote(upi_uri, safe="")
    )
    return UpiQrOut(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        amount_paise=invoice.total_paise,
        currency=invoice.currency,
        upi_vpa=vpa.strip(),
        upi_uri=upi_uri,
        qr_image_url=qr_image_url,
    )


@router.get("/invoices/{invoice_id}/gst-invoice", response_class=HTMLResponse)
async def gst_invoice_html(
    invoice_id: UUID,
    principal: AuthPrincipal = Depends(require_permission("invoice:view")),
    _: AuthPrincipal = Depends(require_organization),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Printable GST tax invoice. Available for any invoice status (not payment-gated)."""
    oid = org_id(principal)
    invoice = await db.scalar(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.organization_id == oid,
            Invoice.deleted_at.is_(None),
        )
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    org = await db.scalar(select(Organization).where(Organization.id == oid))
    client = await db.scalar(select(Client).where(Client.id == invoice.client_id))
    lines = ""
    for item in invoice.line_items or []:
        qty = int(item.get("quantity") or 1)
        unit = int(item.get("unit_paise") or 0)
        desc = html.escape(str(item.get("description") or "Item"))
        lines += (
            f"<tr><td>{desc}</td><td>{qty}</td>"
            f"<td>₹{unit / 100:.2f}</td><td>₹{(qty * unit) / 100:.2f}</td></tr>"
        )
    taxable = max(0, invoice.subtotal_paise - invoice.discount_paise)
    gst_pct = 0.0
    if taxable > 0 and invoice.tax_paise > 0:
        gst_pct = round((invoice.tax_paise / taxable) * 100, 2)
    line_meta = {}
    if invoice.line_items:
        first = invoice.line_items[0] or {}
        line_meta = first.get("meta") or {}
    tax_inclusive = bool(line_meta.get("tax_inclusive"))
    pt_duration = str(line_meta.get("pt_duration") or "").strip()
    terms = [str(t).strip() for t in (line_meta.get("terms_and_conditions") or []) if str(t).strip()]
    cgst = invoice.tax_paise // 2
    sgst = invoice.tax_paise - cgst
    org_name = html.escape(org.name if org else "TetherFit")
    inv_num = html.escape(invoice.invoice_number)
    created = invoice.created_at.strftime("%d %b %Y")
    gstin_line = f"GSTIN: {html.escape(org.gstin)}<br/>" if org and org.gstin else ""
    addr_line = (
        f"{html.escape(org.business_address)}<br/>" if org and org.business_address else ""
    )
    phone_line = html.escape(org.business_phone) if org and org.business_phone else ""
    client_name = html.escape(client.full_name if client else "Client")
    client_phone = html.escape(client.phone or "") if client else ""
    client_email = (
        f"<br/>{html.escape(client.email)}" if client and client.email else ""
    )
    pt_duration_html = (
        f"<p><strong>PT Duration:</strong> {html.escape(pt_duration)}</p>" if pt_duration else ""
    )
    tax_mode_label = "Inclusive" if tax_inclusive else "Exclusive"
    terms_html = "".join(f"<li>{html.escape(term)}</li>" for term in terms)
    if not terms_html:
        terms_html = (
            "<li>Payments are due as per invoice schedule unless otherwise agreed in writing.</li>"
            "<li>Services once delivered are non-refundable except where required by law.</li>"
            "<li>Please retain this invoice for accounting and GST record purposes.</li>"
        )
    body = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>GST Invoice {inv_num}</title>
<style>
body{{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;background:#f3f7f4;color:#13231b;}}
.sheet{{max-width:920px;margin:2rem auto;background:#fff;border:1px solid #dbe5de;border-radius:14px;padding:2rem 2rem 1.5rem;box-shadow:0 10px 30px rgba(18,35,27,.08)}}
.header{{display:flex;justify-content:space-between;gap:1rem;align-items:flex-start}}
h1{{font-size:1.5rem;margin:0 0 .25rem 0;letter-spacing:.01em}}
.muted{{color:#5e6e65;font-size:.92rem}}
.pill{{display:inline-block;background:#eaf3ee;color:#214132;border-radius:999px;padding:.2rem .65rem;font-size:.75rem;font-weight:600;letter-spacing:.02em}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}}
.card{{border:1px solid #dbe5de;border-radius:10px;padding:.9rem}}
.card h3{{margin:0 0 .4rem 0;font-size:.84rem;text-transform:uppercase;letter-spacing:.05em;color:#446053}}
table{{width:100%;border-collapse:collapse;margin-top:1.25rem}}
th{{background:#f4f8f5;color:#355246;border:1px solid #dbe5de;padding:.6rem;text-align:left;font-size:.82rem}}
td{{border:1px solid #e3ebe5;padding:.58rem;text-align:left;font-size:.92rem}}
.num{{text-align:right;white-space:nowrap}}
.totals{{margin-top:1rem;margin-left:auto;width:340px}}
.totals-row{{display:flex;justify-content:space-between;padding:.25rem 0;border-bottom:1px dashed #dbe5de}}
.totals-row.total{{font-size:1.08rem;font-weight:700;border-bottom:0;padding-top:.55rem}}
.tc{{margin-top:1.3rem;border-top:1px solid #dbe5de;padding-top:.85rem}}
.tc ul{{margin:.45rem 0 0 1rem;padding:0}}
.tc li{{margin:.22rem 0;line-height:1.35}}
.footer{{margin-top:1rem;font-size:.8rem;color:#6b7b72}}
button{{margin-bottom:1rem;border:0;background:#183426;color:#fff;padding:.5rem .8rem;border-radius:.5rem;cursor:pointer}}
@media print{{body{{background:#fff}} .sheet{{margin:0;border:0;box-shadow:none;border-radius:0;padding:0}} button{{display:none}}}}
</style></head><body>
<div class="sheet">
<button onclick="window.print()">Print / Save PDF</button>
<div class="header">
  <div>
    <span class="pill">TAX INVOICE</span>
    <h1>{org_name}</h1>
    <p class="muted">{gstin_line}{addr_line}{phone_line}</p>
  </div>
  <div class="card">
    <h3>Invoice Details</h3>
    <p><strong>No:</strong> {inv_num}</p>
    <p><strong>Date:</strong> {created}</p>
    <p><strong>Status:</strong> {html.escape(invoice.status)}</p>
    <p><strong>Tax Mode:</strong> {tax_mode_label}</p>
  </div>
</div>
<div class="grid">
  <div class="card">
    <h3>Bill To</h3>
    <p><strong>{client_name}</strong><br/>{client_phone}{client_email}</p>
  </div>
  <div class="card">
    <h3>Service Summary</h3>
    {pt_duration_html}
    <p><strong>Notes:</strong> {html.escape(invoice.notes or "—")}</p>
  </div>
</div>
<table><thead><tr><th>Description</th><th class="num">Qty</th><th class="num">Rate</th><th class="num">Amount</th></tr></thead>
<tbody>{lines}</tbody></table>
<div class="totals">
  <div class="totals-row"><span>Subtotal</span><span>₹{invoice.subtotal_paise / 100:.2f}</span></div>
  <div class="totals-row"><span>Discount</span><span>- ₹{invoice.discount_paise / 100:.2f}</span></div>
  <div class="totals-row"><span>Taxable Value</span><span>₹{taxable / 100:.2f}</span></div>
  <div class="totals-row"><span>CGST ({gst_pct / 2:.2f}%)</span><span>₹{cgst / 100:.2f}</span></div>
  <div class="totals-row"><span>SGST ({gst_pct / 2:.2f}%)</span><span>₹{sgst / 100:.2f}</span></div>
  <div class="totals-row total"><span>Total (INR)</span><span>₹{invoice.total_paise / 100:.2f}</span></div>
</div>
<div class="tc">
  <h3>Terms &amp; Conditions</h3>
  <ul>{terms_html}</ul>
</div>
<p class="footer">This is a system-generated invoice from TetherFit and does not require a physical signature.</p>
</div>
</body></html>"""
    return HTMLResponse(content=body)


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


@router.post("/payments/cash", response_model=PaymentOut, status_code=201)
async def record_cash_payment(
    body: CashPaymentBody,
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
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice already paid")
    payment = Payment(
        organization_id=oid,
        invoice_id=invoice.id,
        client_id=invoice.client_id,
        provider="cash",
        provider_order_id=f"cash_{uuid4().hex[:12]}",
        provider_payment_id=f"cashpay_{uuid4().hex[:12]}",
        amount_paise=invoice.total_paise,
        currency=invoice.currency,
        status=PaymentStatus.SUCCESS,
        method="cash",
        raw_payload={"notes": body.notes} if body.notes else {},
        created_by=principal.user.id,
        updated_by=principal.user.id,
    )
    invoice.status = InvoiceStatus.PAID
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)


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
