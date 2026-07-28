from __future__ import annotations

import hashlib
import hmac


def verify_razorpay_webhook_signature(
    body: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify X-Razorpay-Signature (HMAC-SHA256 hex digest of raw body)."""
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
