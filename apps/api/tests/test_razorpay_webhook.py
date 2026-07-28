import hashlib
import hmac

from app.infrastructure.razorpay_webhook import verify_razorpay_webhook_signature


def test_verify_razorpay_webhook_signature_valid():
    secret = "whsec_test_fixed"
    body = b'{"event":"payment.captured","payload":{}}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_razorpay_webhook_signature(body, sig, secret) is True


def test_verify_razorpay_webhook_signature_invalid():
    secret = "whsec_test_fixed"
    body = b'{"event":"payment.captured"}'
    assert verify_razorpay_webhook_signature(body, "deadbeef", secret) is False
    assert verify_razorpay_webhook_signature(body, "", secret) is False
    assert verify_razorpay_webhook_signature(body, "abc", "") is False
