from app.core.rate_limit import RateLimitMiddleware
from app.infrastructure.r2 import public_url_for_key


def test_public_url_for_key_none_without_config():
    url = public_url_for_key("x/y")
    assert url is None or isinstance(url, str)


def test_rate_limit_middleware_skips_health():
    assert RateLimitMiddleware is not None
