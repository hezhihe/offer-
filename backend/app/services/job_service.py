"""
岗位服务层。

负责从 Supabase 读取岗位数据，并把数据库字段映射成前端使用的 API 字段。
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import logging
import time

from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
_jobs_cache: Dict[str, Dict[str, Any]] = {}
JOBS_CACHE_SECONDS = 300


def _parse_deadline(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _days_until_deadline(deadline: Any) -> Optional[int]:
    deadline_date = _parse_deadline(deadline)
    if deadline_date is None:
        return None
    return (deadline_date - date.today()).days


def _derive_job_status(deadline: Any, explicit_status: Optional[str] = None) -> str:
    if explicit_status in {"active", "closed", "expired"}:
        return explicit_status
    days = _days_until_deadline(deadline)
    if days is not None and days < 0:
        return "expired"
    return "active"


def _is_visible_job(record: Dict[str, Any], include_expired: bool) -> bool:
    status = _derive_job_status(record.get("deadline"), record.get("status"))
    if status in {"closed", "expired"}:
        return include_expired
    return True


def _infer_education_from_requirements(requirements: str) -> str:
    if "硕士及以上" in requirements:
        return "硕士及以上"
    if "本科及以上" in requirements:
        return "本科及以上"
    if "专科及以上" in requirements or "大专及以上" in requirements:
        return "专科及以上"
    return "不限"


def _map_job_record(record: Dict[str, Any]) -> Dict[str, Any]:
    requirements = record.get("requirements", "")
    deadline = record.get("deadline", "")
    status = _derive_job_status(deadline, record.get("status"))
    education = record.get("education") or _infer_education_from_requirements(requirements)

    return {
        "id": record.get("id"),
        "company": record.get("company", ""),
        "title": record.get("title", ""),
        "date": deadline,
        "salary": record.get("salary", ""),
        "category": record.get("category", ""),
        "capital": record.get("capital", ""),
        "requirements": requirements,
        "womenFriendly": record.get("women_friendly", False),
        "education": education,
        "url": record.get("url", ""),
        "status": status,
        "isExpired": status == "expired",
        "daysUntilDeadline": _days_until_deadline(deadline),
    }


class JobService:
    """岗位服务类，提供岗位查询和筛选。"""

    @staticmethod
    def get_jobs(
        category: str = "all",
        education: str = "all",
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        try:
            cache_key = f"{category}:{education}:{include_expired}"
            cached = _jobs_cache.get(cache_key)
            if cached and time.time() < cached["expires_at"]:
                return cached["data"]

            query = get_supabase().table("jobs").select("*")

            if category != "all":
                query = query.eq("category", category)

            if education == "专科":
                query = query.in_("education", ["专科及以上", "不限"])
            elif education == "本科":
                query = query.in_("education", ["专科及以上", "本科及以上", "不限"])

            result = query.execute()
            visible_records = [
                record
                for record in (result.data or [])
                if _is_visible_job(record, include_expired)
            ]
            mapped = [_map_job_record(record) for record in visible_records]

            _jobs_cache[cache_key] = {
                "data": mapped,
                "expires_at": time.time() + JOBS_CACHE_SECONDS,
            }

            logger.info(
                "查询岗位数据成功，分类: %s, 学历: %s, include_expired: %s, 数量: %s",
                category,
                education,
                include_expired,
                len(mapped),
            )
            return mapped
        except Exception as e:
            logger.error("查询岗位数据失败: %s", e)
            return []

    @staticmethod
    def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
        try:
            result = (
                get_supabase()
                .table("jobs")
                .select("*")
                .eq("id", job_id)
                .single()
                .execute()
            )
            if result.data:
                return _map_job_record(result.data)
            return None
        except Exception as e:
            logger.error("查询岗位详情失败, id=%s: %s", job_id, e)
            return None

    @staticmethod
    def get_categories() -> List[str]:
        try:
            result = get_supabase().table("jobs").select("category", count="exact").execute()
            categories = list(set([job["category"] for job in result.data]))
            return sorted(categories)
        except Exception as e:
            logger.error("查询分类失败: %s", e)
            return []


def get_jobs(category: str = "all") -> List[Dict[str, Any]]:
    return JobService.get_jobs(category)


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    return JobService.get_job_by_id(job_id)
