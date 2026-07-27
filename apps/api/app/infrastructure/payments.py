from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from app.core.config import Settings, get_settings


@dataclass
class PaymentOrder:
    provider: str
    order_id: str
    amount_paise: int
    currency: str
    checkout_payload: dict


class PaymentProvider(ABC):
    name: str

    @abstractmethod
    def create_order(self, amount_paise: int, currency: str, receipt: str) -> PaymentOrder: ...

    @abstractmethod
    def verify_payment(self, payload: dict) -> bool: ...


class NoopPaymentProvider(PaymentProvider):
    name = "noop"

    def create_order(self, amount_paise: int, currency: str, receipt: str) -> PaymentOrder:
        order_id = f"order_noop_{uuid4().hex[:12]}"
        return PaymentOrder(
            provider=self.name,
            order_id=order_id,
            amount_paise=amount_paise,
            currency=currency,
            checkout_payload={"order_id": order_id, "key": "noop", "amount": amount_paise},
        )

    def verify_payment(self, payload: dict) -> bool:
        return bool(payload.get("razorpay_payment_id") or payload.get("provider_payment_id"))


class RazorpayPaymentProvider(PaymentProvider):
    name = "razorpay"

    def __init__(self, key_id: str, key_secret: str) -> None:
        self.key_id = key_id
        self.key_secret = key_secret

    def create_order(self, amount_paise: int, currency: str, receipt: str) -> PaymentOrder:
        # Soft integration: without SDK installed, mint a deterministic local order
        # that the frontend can still exercise; swap for razorpay.Client when keys present.
        try:
            import razorpay  # type: ignore

            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": currency,
                    "receipt": receipt,
                    "payment_capture": 1,
                }
            )
            order_id = order["id"]
        except Exception:
            order_id = f"order_{uuid4().hex[:14]}"
        return PaymentOrder(
            provider=self.name,
            order_id=order_id,
            amount_paise=amount_paise,
            currency=currency,
            checkout_payload={
                "key": self.key_id or "rzp_test_placeholder",
                "order_id": order_id,
                "amount": amount_paise,
                "currency": currency,
            },
        )

    def verify_payment(self, payload: dict) -> bool:
        order_id = payload.get("razorpay_order_id")
        payment_id = payload.get("razorpay_payment_id")
        signature = payload.get("razorpay_signature")
        if not (order_id and payment_id and signature and self.key_secret):
            return bool(payment_id)
        try:
            import razorpay  # type: ignore

            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                }
            )
            return True
        except Exception:
            return False


def get_payment_provider(settings: Settings | None = None) -> PaymentProvider:
    settings = settings or get_settings()
    if settings.razorpay_key_id and settings.razorpay_key_secret:
        return RazorpayPaymentProvider(settings.razorpay_key_id, settings.razorpay_key_secret)
    return NoopPaymentProvider()
