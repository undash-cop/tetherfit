from __future__ import annotations

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings, get_settings


def create_r2_client(settings: Settings | None = None) -> BaseClient | None:
    settings = settings or get_settings()
    if not settings.r2_endpoint or not settings.r2_access_key_id:
        return None
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def check_r2_configured(settings: Settings | None = None) -> tuple[bool, str]:
    settings = settings or get_settings()
    if not settings.r2_endpoint or not settings.r2_access_key_id or not settings.r2_bucket:
        return False, "R2 credentials not configured"
    client = create_r2_client(settings)
    if client is None:
        return False, "R2 client unavailable"
    try:
        client.head_bucket(Bucket=settings.r2_bucket)
        return True, "ok"
    except (ClientError, BotoCoreError) as exc:
        return False, str(exc)


def public_url_for_key(key: str, settings: Settings | None = None) -> str | None:
    settings = settings or get_settings()
    if not settings.r2_public_url:
        return None
    return f"{settings.r2_public_url.rstrip('/')}/{key.lstrip('/')}"


def create_presigned_put(
    key: str,
    content_type: str,
    expires_in: int = 3600,
    settings: Settings | None = None,
) -> tuple[str | None, dict[str, str]]:
    settings = settings or get_settings()
    client = create_r2_client(settings)
    if client is None or not settings.r2_bucket:
        return None, {}
    try:
        url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.r2_bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return url, {"Content-Type": content_type}
    except (ClientError, BotoCoreError):
        return None, {}
