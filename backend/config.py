"""
配置管理模块
集中管理所有环境变量和配置项
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    """应用配置类"""
    
    # Supabase 配置
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # DeepSeek AI 配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL: str = os.getenv(
        "DEEPSEEK_API_URL", 
        "https://api.deepseek.com/v1/chat/completions"
    )
    
    # JWT 配置
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @classmethod
    def validate(cls) -> None:
        """验证必要配置是否已设置"""
        required_vars = [
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_SERVICE_KEY", cls.SUPABASE_SERVICE_KEY),
        ]
        
        missing = [name for name, value in required_vars if not value]
        if missing:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing)}")


# 全局配置实例
settings = Settings()
