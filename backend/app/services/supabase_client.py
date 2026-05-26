"""
Supabase 客户端封装模块

使用单例模式确保整个应用只维护一个 Supabase 连接，
避免重复创建客户端带来的性能开销和连接泄漏。
"""
from supabase import create_client, Client
from config import settings
import logging

# 配置日志
logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase 客户端单例类
    
    为什么用单例模式？
    1. 性能：避免每次请求都创建新连接
    2. 资源管理：控制连接池大小
    3. 一致性：全应用使用同一配置
    
    使用示例：
        supabase = get_supabase()
        result = supabase.table("jobs").select("*").execute()
    """
    
    _instance: Client = None
    _initialized: bool = False
    
    @classmethod
    def get_client(cls) -> Client:
        """
        获取 Supabase 客户端实例
        
        Returns:
            Client: Supabase 客户端实例
            
        Raises:
            ValueError: 如果环境变量未配置
            ConnectionError: 如果连接失败
        """
        if cls._instance is None:
            # 验证配置
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                raise ValueError(
                    "Supabase 配置缺失！请检查 .env 文件中的 "
                    "SUPABASE_URL 和 SUPABASE_SERVICE_KEY"
                )
            
            try:
                # 创建客户端
                # 使用 service_role key 可以绕过 RLS，适合后端使用
                cls._instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                cls._initialized = True
                logger.info("Supabase 客户端初始化成功")
                
            except Exception as e:
                logger.error(f"Supabase 客户端初始化失败: {e}")
                raise ConnectionError(f"无法连接到 Supabase: {e}")
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """
        重置客户端（主要用于测试）
        """
        cls._instance = None
        cls._initialized = False
        logger.info("Supabase 客户端已重置")


# 快捷函数，方便其他模块导入使用
def get_supabase() -> Client:
    """
    获取 Supabase 客户端的快捷函数
    
    这是推荐的使用方式，简单直接：
        from app.services import get_supabase
        supabase = get_supabase()
        
    Returns:
        Client: Supabase 客户端实例
    """
    return SupabaseClient.get_client()


# 健康检查函数
def check_supabase_health() -> dict:
    """
    检查 Supabase 连接健康状态
    
    Returns:
        dict: 包含状态信息的字典
        
    Example:
        {
            "status": "healthy" | "unhealthy",
            "message": "连接正常" | 错误信息,
            "url": "https://..."
        }
    """
    try:
        supabase = get_supabase()
        # 简单查询测试连接
        result = supabase.table("jobs").select("count", count="exact").limit(1).execute()
        return {
            "status": "healthy",
            "message": "Supabase 连接正常",
            "url": settings.SUPABASE_URL,
            "tables_accessible": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
            "url": settings.SUPABASE_URL,
            "tables_accessible": False
        }


# 如果直接运行此文件，测试连接
if __name__ == "__main__":
    print("测试 Supabase 连接...")
    try:
        health = check_supabase_health()
        print(f"状态: {health['status']}")
        print(f"消息: {health['message']}")
        print(f"URL: {health['url']}")
    except Exception as e:
        print(f"测试失败: {e}")
