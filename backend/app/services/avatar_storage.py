from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
from urllib.parse import quote

import requests

from config import settings

logger = logging.getLogger(__name__)

AVATAR_BUCKET = "avatars"
MAX_AVATAR_BYTES = 350 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _storage_headers(content_type: str | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def ensure_avatar_bucket() -> None:
    """Create the public avatar bucket if it does not already exist."""
    bucket_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/bucket/{AVATAR_BUCKET}"
    response = requests.get(bucket_url, headers=_storage_headers(), timeout=10)
    if response.status_code == 200:
        return

    create_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/bucket"
    create_response = requests.post(
        create_url,
        headers=_storage_headers("application/json"),
        json={"id": AVATAR_BUCKET, "name": AVATAR_BUCKET, "public": True},
        timeout=10,
    )
    if create_response.status_code not in (200, 201, 409):
        logger.error("Failed to create avatar bucket: %s", create_response.text)
        raise RuntimeError("Avatar storage bucket is not ready")


def build_avatar_path(phone: str, filename: str, content_type: str) -> str:
    suffix = ALLOWED_AVATAR_TYPES.get(content_type) or Path(filename).suffix.lower() or ".jpg"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_phone = "".join(ch for ch in phone if ch.isdigit()) or "user"
    return f"{safe_phone}/avatar-{timestamp}{suffix}"


def upload_avatar_file(phone: str, filename: str, content_type: str, content: bytes) -> Tuple[str, str]:
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise ValueError("Only JPG, PNG, and WebP avatar images are supported")
    if len(content) > MAX_AVATAR_BYTES:
        raise ValueError("Avatar image is too large")

    ensure_avatar_bucket()

    object_path = build_avatar_path(phone, filename, content_type)
    encoded_path = quote(object_path, safe="/")
    upload_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{AVATAR_BUCKET}/{encoded_path}"

    response = requests.post(
        upload_url,
        headers={
            **_storage_headers(content_type),
            "x-upsert": "true",
            "Cache-Control": "3600",
        },
        data=content,
        timeout=20,
    )
    if response.status_code not in (200, 201):
        logger.error("Failed to upload avatar: %s", response.text)
        raise RuntimeError("Avatar upload to storage failed")

    public_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{AVATAR_BUCKET}/{encoded_path}"
    return public_url, object_path
