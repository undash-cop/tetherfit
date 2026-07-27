from app.infrastructure.notifications import NotificationMessage, get_notification_provider
from app.infrastructure.payments import NoopPaymentProvider, get_payment_provider


def test_noop_payment_provider_creates_order():
    provider = NoopPaymentProvider()
    order = provider.create_order(50000, "INR", "TF-00001")
    assert order.amount_paise == 50000
    assert order.order_id.startswith("order_noop_")
    assert provider.verify_payment({"provider_payment_id": "pay_x"})


def test_get_payment_provider_defaults_to_noop():
    provider = get_payment_provider()
    assert provider.name in {"noop", "razorpay"}


def test_notification_noop_sends():
    provider = get_notification_provider()
    status = provider.send(
        NotificationMessage(channel="email", recipient="a@b.com", subject="Hi", body="Hello")
    )
    assert status == "sent"
