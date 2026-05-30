"""
User service for phone/password accounts.

The source of truth is Supabase public.users_data. The in-memory dict is only
a short-lived cache for the running backend process.
"""
from typing import Any, Dict, Optional
import logging
from datetime import datetime, timezone

from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)

USERS_TABLE = "users_data"

_users_db: Dict[str, Dict[str, Any]] = {
    "13800138000": {
        "phone": "13800138000",
        "email": "test@example.com",
        "hashed_password": "$2b$12$MBb9yXDmIzSaku0kvX5XYOMjKQV1xFC9YV66e8M.acAzIaKJSwLNK",
        "nickname": "测试用户",
        "avatar": None,
    }
}
_loaded = False


def _normalize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "phone": user["phone"],
        "email": user.get("email"),
        "hashed_password": user["hashed_password"],
        "nickname": user["nickname"],
        "avatar": user.get("avatar"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "last_login_at": user.get("last_login_at"),
    }


def _load_users_from_db() -> None:
    """Load users from Supabase into the process cache once."""
    global _loaded
    if _loaded:
        return

    try:
        result = get_supabase().table(USERS_TABLE).select("*").execute()
        for user in result.data or []:
            normalized = _normalize_user(user)
            _users_db[normalized["phone"]] = normalized
        logger.info("Loaded %s users from %s", len(result.data or []), USERS_TABLE)
        _loaded = True
    except Exception as e:
        logger.warning("Failed to load users from %s: %s", USERS_TABLE, e)


def _fetch_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Fetch one user directly from Supabase when the cache misses."""
    try:
        result = get_supabase().table(USERS_TABLE).select("*").eq("phone", phone).limit(1).execute()
        if not result.data:
            return None
        normalized = _normalize_user(result.data[0])
        _users_db[phone] = normalized
        return normalized
    except Exception as e:
        logger.warning("Failed to fetch user %s from %s: %s", phone, USERS_TABLE, e)
        return None


def get_user(phone: str) -> Optional[Dict[str, Any]]:
    """Get a user by phone number."""
    _load_users_from_db()
    cached = _users_db.get(phone)
    if cached:
        return cached
    return _fetch_user_by_phone(phone)


def user_exists(phone: str) -> bool:
    """Return whether a phone number is already registered."""
    _load_users_from_db()
    return phone in _users_db or _fetch_user_by_phone(phone) is not None


def create_user(phone: str, hashed_password: str, nickname: str, email: Optional[str] = None) -> Dict[str, Any]:
    """Create a user in Supabase, then update the process cache."""
    _load_users_from_db()

    if phone in _users_db:
        raise ValueError("该手机号已注册")

    user_data = {
        "phone": phone,
        "email": email,
        "hashed_password": hashed_password,
        "nickname": nickname,
        "avatar": None,
    }

    try:
        get_supabase().table(USERS_TABLE).insert(user_data).execute()
    except Exception as e:
        logger.error("Failed to insert user into %s: %s", USERS_TABLE, e)
        raise RuntimeError("用户数据写入失败，请稍后重试")

    _users_db[phone] = user_data
    return user_data


def update_last_login(phone: str) -> Optional[str]:
    """Persist and cache the latest successful login time."""
    logged_in_at = datetime.now(timezone.utc).isoformat()

    try:
        get_supabase().table(USERS_TABLE).update({
            "last_login_at": logged_in_at,
        }).eq("phone", phone).execute()
    except Exception as e:
        logger.error("Failed to update last_login_at for %s: %s", phone, e)
        return None

    if phone in _users_db:
        _users_db[phone]["last_login_at"] = logged_in_at
    return logged_in_at


def update_user_password(phone: str, hashed_password: str) -> bool:
    """Persist a new password hash and keep the process cache in sync."""
    try:
        get_supabase().table(USERS_TABLE).update({
            "hashed_password": hashed_password,
        }).eq("phone", phone).execute()
    except Exception as e:
        logger.error("Failed to update password for %s: %s", phone, e)
        return False

    if phone in _users_db:
        _users_db[phone]["hashed_password"] = hashed_password
    else:
        user = _fetch_user_by_phone(phone)
        if user:
            user["hashed_password"] = hashed_password
    return True


def get_all_users() -> Dict[str, Dict[str, Any]]:
    """Return a copy of the process user cache."""
    _load_users_from_db()
    return _users_db.copy()
