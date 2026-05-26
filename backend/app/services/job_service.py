"""
岗位服务层

封装岗位相关的数据库操作，提供清晰的业务逻辑接口。
负责数据库字段名（snake_case）到 API 字段名（camelCase）的映射转换。
"""
from typing import List, Optional, Dict, Any
from app.services.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)


def _map_job_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    将数据库记录（snake_case）映射为 API 格式（camelCase）
    
    数据库字段 → API 字段映射：
    - deadline → date
    - women_friendly → womenFriendly
    - 其他字段保持不变
    """
    return {
        "id": record.get("id"),
        "company": record.get("company", ""),
        "title": record.get("title", ""),
        "date": record.get("deadline", ""),          # deadline → date
        "salary": record.get("salary", ""),
        "category": record.get("category", ""),
        "capital": record.get("capital", ""),
        "requirements": record.get("requirements", ""),
        "womenFriendly": record.get("women_friendly", False),  # snake → camel
        "education": record.get("education", "不限"),
        "url": record.get("url", ""),
    }


class JobService:
    """
    岗位服务类
    
    提供岗位数据的查询、筛选等功能。
    所有方法都是静态方法，无需实例化即可使用。
    """
    
    @staticmethod
    def get_jobs(category: str = "all", education: str = "all") -> List[Dict[str, Any]]:
        """
        获取岗位列表
        
        Args:
            category: 岗位分类筛选，默认 "all" 返回全部
                     可选值: robot, ai, lowAltitude, material, energy
            education: 学历筛选，默认 "all" 返回全部
                     可选值: 本科, 硕士
        
        Returns:
            List[Dict]: 岗位列表，每个岗位是一个字典（camelCase 格式）
        """
        try:
            supabase = get_supabase()
            
            # 构建查询
            query = supabase.table("jobs").select("*")
            
            # 如果指定了分类，添加筛选条件
            if category != "all":
                query = query.eq("category", category)
            
            # 学历筛选逻辑：
            # "本科" → 返回"本科及以上"和"不限"
            # "硕士" → 返回"硕士及以上"和"不限"
            # "all" → 不筛选
            if education == "本科":
                query = query.in_("education", ["本科及以上", "不限"])
            elif education == "硕士":
                query = query.in_("education", ["硕士及以上", "不限"])
            
            # 执行查询
            result = query.execute()
            
            # 字段映射：数据库 snake_case → API camelCase
            mapped = [_map_job_record(record) for record in result.data]
            
            logger.info(f"查询岗位数据成功，分类: {category}, 数量: {len(mapped)}")
            return mapped
            
        except Exception as e:
            logger.error(f"查询岗位数据失败: {e}")
            # 出错时返回空列表，避免前端崩溃
            return []
    
    @staticmethod
    def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取单个岗位详情
        
        Args:
            job_id: 岗位 ID
        
        Returns:
            Dict: 岗位详情（camelCase 格式），如果不存在返回 None
            
        Example:
            >>> job = JobService.get_job_by_id(1)
            >>> print(job["title"])  # "机器人算法工程师"
        """
        try:
            supabase = get_supabase()
            
            result = supabase.table("jobs")\
                .select("*")\
                .eq("id", job_id)\
                .single()\
                .execute()
            
            if result.data:
                return _map_job_record(result.data)
            return None
            
        except Exception as e:
            logger.error(f"查询岗位详情失败, id={job_id}: {e}")
            return None
    
    @staticmethod
    def get_categories() -> List[str]:
        """
        获取所有岗位分类
        
        Returns:
            List[str]: 分类列表
        """
        try:
            supabase = get_supabase()
            
            # 使用 distinct 查询去重
            result = supabase.table("jobs")\
                .select("category", count="exact")\
                .execute()
            
            # 提取唯一的分类
            categories = list(set([job["category"] for job in result.data]))
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"查询分类失败: {e}")
            return []


# 快捷函数，方便直接导入使用
def get_jobs(category: str = "all") -> List[Dict[str, Any]]:
    """快捷函数：获取岗位列表"""
    return JobService.get_jobs(category)


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """快捷函数：获取单个岗位"""
    return JobService.get_job_by_id(job_id)
