from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import io
import requests
import json
import logging
import re
import time
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 导入 Supabase 服务
from app.services import get_supabase, JobService, get_user as get_user_from_service, user_exists, create_user
from app.services.avatar_storage import upload_avatar_file
from app.services.interview_knowledge import build_interview_prompt, build_rule_based_interview_feedback
from app.services.resume_knowledge import build_resume_prompt
from app.services.user_service import update_last_login, update_user_password

SECRET_KEY = os.getenv("API_SECRET_KEY", "secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

app = FastAPI(title="Offer Compass API", version="1.0.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173,https://bejewelled-lamington-a93247.netlify.app").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

fake_users_db = {
    "13800138000": {
        "phone": "13800138000",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYbB.rK4fl8x2q7Meu6Q6D2V5fF5Q5Q5Q5Q5Q5Q5Q5Q",
        "nickname": "测试用户"
    }
}

class TokenData(BaseModel):
    phone: Optional[str] = None

class User(BaseModel):
    phone: str
    nickname: str
    email: Optional[str] = None
    avatar: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[User] = None

class UserInDB(User):
    hashed_password: str

class AvatarUploadRequest(BaseModel):
    avatar: str

class FeedbackRequest(BaseModel):
    content: str
    contact: Optional[str] = None
    page_url: Optional[str] = None

class ResumeAnalysisRequest(BaseModel):
    jd_content: str
    experience: str

class ResumeAnalysisResponse(BaseModel):
    match_score: int
    keywords: List[Dict[str, str]]
    refactored_resume: str

class InterviewStartRequest(BaseModel):
    job_type: str

class InterviewStartResponse(BaseModel):
    id: str
    questions: List[str]

class InterviewAnswerRequest(BaseModel):
    interview_id: str
    question_index: int
    answer: str

class InterviewAnswerResponse(BaseModel):
    score: int
    feedback: Dict
    next_question: Optional[str] = None

class InterviewCompleteRequest(BaseModel):
    interview_id: str

class InterviewCompleteResponse(BaseModel):
    total_score: int
    avg_score: float
    advice: str
    details: List[Dict]

class JobCategory(BaseModel):
    id: str
    name: str

class Job(BaseModel):
    id: int
    company: str
    title: str
    date: str
    salary: str
    category: str
    capital: str
    requirements: str
    womenFriendly: bool
    education: str = "不限"
    url: str

class TipResponse(BaseModel):
    content: str

class TipsResponse(BaseModel):
    tips: List[str]

class StatsResponse(BaseModel):
    resume: int
    interview: int
    browse: int

stats_cache: Dict[str, Dict] = {}

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        # bcrypt 版本兼容：如果 verify 失败，尝试重新 hash 后比较
        import hashlib
        safe_pwd = hashlib.sha256(plain_password.encode()).hexdigest()[:72]
        try:
            return pwd_context.verify(safe_pwd, hashed_password)
        except (ValueError, TypeError):
            return False

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, phone: str):
    if phone in db:
        user_dict = db[phone]
        return UserInDB(**user_dict)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise credentials_exception
        token_data = TokenData(phone=phone)
    except JWTError:
        raise credentials_exception
    user_data = get_user_from_service(token_data.phone)
    if user_data is None:
        raise credentials_exception
    return UserInDB(**user_data)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

async def get_optional_user(request: Request) -> Optional[User]:
    """获取当前用户，未登录返回 None 而不是抛出 401"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]  # 去掉 "Bearer "
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            return None
        user_data = get_user_from_service(phone)
        if user_data:
            return UserInDB(**user_data)
        return None
    except:
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class LoginRequest(BaseModel):
    phone: str
    password: str

@app.post("/api/auth/login", response_model=Token)
async def login_for_access_token(request: LoginRequest):
    user_data = get_user_from_service(request.phone)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该用户不存在，请先注册",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(request.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误，请重新输入",
            headers={"WWW-Authenticate": "Bearer"},
        )
    update_last_login(user_data["phone"])

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["phone"]}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "phone": user_data["phone"],
            "nickname": user_data["nickname"],
            "email": user_data.get("email"),
            "avatar": user_data.get("avatar")
        }
    }

class SignupRequest(BaseModel):
    phone: str
    password: str
    nickname: str
    email: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@app.post("/api/auth/signup")
async def signup(req: SignupRequest):
    if user_exists(req.phone):
        raise HTTPException(status_code=400, detail="该手机号已注册")
    hashed_password = get_password_hash(req.password)
    try:
        user_data = create_user(req.phone, hashed_password, req.nickname, req.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": req.phone}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"phone": req.phone, "nickname": req.nickname, "email": req.email, "avatar": None}}

@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/api/auth/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if len(req.new_password.strip()) < 6:
        raise HTTPException(status_code=400, detail="新密码至少需要 6 位")
    if verify_password(req.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="新密码不能和旧密码相同")

    hashed_password = get_password_hash(req.new_password)
    if not update_user_password(current_user.phone, hashed_password):
        raise HTTPException(status_code=500, detail="密码更新失败，请稍后重试")
    return {"success": True}

@app.post("/api/auth/avatar")
async def upload_avatar(
    req: AvatarUploadRequest,
    current_user: User = Depends(get_current_active_user)
):
    """上传头像（base64格式）"""
    if not req.avatar.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Invalid avatar image")
    if len(req.avatar) > 500_000:
        raise HTTPException(status_code=413, detail="Avatar image is too large")

    try:
        supabase = get_supabase()
        supabase.table("users_data").update({"avatar": req.avatar}).eq("phone", current_user.phone).execute()
        user_data = get_user_from_service(current_user.phone)
        if user_data is not None:
            user_data["avatar"] = req.avatar
        return {"success": True, "avatar": req.avatar}
    except Exception as e:
        logger.error(f"头像上传失败: {e}")
        raise HTTPException(status_code=500, detail="头像上传失败")

@app.post("/api/auth/avatar-file")
async def upload_avatar_file_endpoint(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload avatar to Supabase Storage and store only the public URL in users_data.avatar."""
    content_type = avatar.content_type or ""
    content = await avatar.read()

    try:
        avatar_url, _object_path = upload_avatar_file(
            phone=current_user.phone,
            filename=avatar.filename or "avatar",
            content_type=content_type,
            content=content,
        )
        supabase = get_supabase()
        supabase.table("users_data").update({"avatar": avatar_url}).eq("phone", current_user.phone).execute()
        user_data = get_user_from_service(current_user.phone)
        if user_data is not None:
            user_data["avatar"] = avatar_url
        return {"success": True, "avatar": avatar_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Avatar file upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Avatar upload failed")

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Successfully logged out"}

@app.post("/api/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_active_user)
):
    content = req.content.strip()
    contact = req.contact.strip() if req.contact else None
    page_url = req.page_url.strip() if req.page_url else None

    if not content:
        raise HTTPException(status_code=400, detail="Feedback content is required")
    if len(content) > 2000:
        raise HTTPException(status_code=400, detail="Feedback content is too long")
    if contact and len(contact) > 120:
        raise HTTPException(status_code=400, detail="Contact is too long")
    if page_url and len(page_url) > 500:
        page_url = page_url[:500]

    try:
        supabase = get_supabase()
        result = supabase.table("user_feedback").insert({
            "user_phone": current_user.phone,
            "content": content,
            "contact": contact,
            "page_url": page_url
        }).execute()
        feedback_id = result.data[0].get("id") if result.data else None
        return {"success": True, "id": feedback_id}
    except Exception as e:
        logger.warning("Save feedback failed: %s", e)
        raise HTTPException(status_code=500, detail="Feedback submit failed")

def call_deepseek_api(prompt: str) -> str:
    """
    双模型容灾调用：
    - 主模型：DeepSeek V4 Pro（DeepSeek 官方 API）
    - 备用模型：DeepSeek V3（硅基流动 SiliconFlow API）

    工作原理：
    1. 先用 V4 Pro 调用（质量更高）
    2. 如果 Pro 超时/报错 → 自动切换 V3（硅基流动，速度更快）
    3. 两个都挂了 → 返回 None，触发业务层的降级方案（mock 数据）
    """
    # 主模型配置（DeepSeek 官方）
    primary_key = os.getenv("DEEPSEEK_API_KEY")
    primary_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    primary_model = "deepseek-ai/DeepSeek-V4-Pro"

    # 备用模型配置（硅基流动）
    fallback_key = os.getenv("DEEPSEEK_FLASH_KEY", primary_key)
    fallback_url = os.getenv("DEEPSEEK_FLASH_URL", primary_url)
    fallback_model = os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-ai/DeepSeek-V3")

    if not primary_key or primary_key == "your-deepseek-api-key":
        return None

    # 尝试主模型 V4 Pro
    try:
        headers = {
            "Authorization": f"Bearer {primary_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": primary_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        response = requests.post(primary_url, headers=headers, json=payload, timeout=18)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        logger.info("主模型 V4 Pro 调用成功")
        return result
    except Exception as e:
        logger.warning(f"主模型 V4 Pro 失败: {e}，切换硅基流动 V3")

    # 主模型失败，切换备用模型（硅基流动）
    try:
        headers = {
            "Authorization": f"Bearer {fallback_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": fallback_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        response = requests.post(fallback_url, headers=headers, json=payload, timeout=18)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        logger.info("硅基流动 V3 调用成功")
        return result
    except Exception as e:
        logger.error(f"硅基流动 V3 也失败: {e}")
        return None

def call_fast_interview_api(prompt: str) -> str:
    """
    Keep interview scoring accurate by trying the primary DeepSeek model first.
    The faster fallback is only used when the primary model is unavailable.
    """
    primary_key = os.getenv("DEEPSEEK_API_KEY")
    primary_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    fallback_key = os.getenv("DEEPSEEK_FLASH_KEY")
    fallback_url = os.getenv("DEEPSEEK_FLASH_URL")
    fallback_model = os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-ai/DeepSeek-V3")

    attempts = []
    if primary_key and primary_key != "your-deepseek-api-key":
        primary_model = os.getenv("DEEPSEEK_INTERVIEW_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
        attempts.append(("interview primary", primary_key, primary_url, primary_model, 12))
    if fallback_key and fallback_url:
        attempts.append(("interview fallback", fallback_key, fallback_url, fallback_model, 6))

    for label, api_key, api_url, model, timeout in attempts:
        try:
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.45,
                    "max_tokens": 900
                },
                timeout=timeout
            )
            response.raise_for_status()
            logger.info(f"{label} 调用成功")
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"{label} 调用失败: {e}")

    return None

def parse_model_json_response(raw: str) -> Dict:
    """Parse JSON even when the model wraps it in markdown or extra text."""
    if not raw:
        raise ValueError("empty model response")

    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])

@app.post("/api/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(request: ResumeAnalysisRequest, current_user: Optional[User] = Depends(get_optional_user)):
    prompt = f"""你是一位资深的职业顾问和简历优化专家。请分析以下职位描述和候选人经历，给出专业的简历优化建议。

【职位描述（JD）】
{request.jd_content}

【候选人经历】
{request.experience}

请完成以下分析：

1. 从 JD 中提取 5-8 个核心关键词（技能、经验、学历等硬性要求）
2. 逐一对比候选人的经历，标记每个关键词是否匹配（"true"或"false"）
3. 根据匹配情况给出综合评分（0-100分）
4. 基于候选人的真实经历，重构一份针对该岗位优化的简历
5. 给出 3-5 条具体的优化建议（要针对这个岗位，不要通用建议）

输出一个 JSON 对象：
{{
  "match_score": 75,
  "keywords": [
    {{"word": "Python", "match": "true", "reason": "候选人有Python项目经验"}},
    {{"word": "Docker", "match": "false", "reason": "候选人经历中未提及"}}
  ],
  "refactored_resume": "重构后的完整简历文本...",
  "suggestions": [
    "建议1：具体针对该岗位的建议",
    "建议2"
  ]
}}

只输出 JSON，不要输出其他内容。"""

    prompt = build_resume_prompt(request.jd_content, request.experience)
    result = call_deepseek_api(prompt)
    used_ai = False
    
    if result:
        try:
            # 尝试提取 JSON
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                match_score = data.get("match_score", 70)
                keywords = data.get("keywords", [])
                refactored_resume = data.get("refactored_resume", "")
                suggestions = data.get("suggestions", [])
                used_ai = True
        except Exception as e:
            logger.warning(f"解析 AI 简历分析结果失败: {e}")
    
    if not used_ai:
        # 降级：基于输入内容生成 mock 数据（而非硬编码机器人相关内容）
        match_score, keywords, refactored_resume, suggestions = generate_mock_resume_analysis(
            request.jd_content, request.experience
        )
    
    # 把建议合并到简历末尾
    if suggestions:
        suggestion_text = "\n\n【优化建议】\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))
        refactored_resume += suggestion_text
    
    response = ResumeAnalysisResponse(
        match_score=match_score,
        keywords=keywords,
        refactored_resume=refactored_resume
    )
    
    # 持久化到数据库（登录用户才保存）
    if current_user:
        try:
            supabase = get_supabase()
            job_title = request.jd_content.split('\n')[0].strip()[:50]
            supabase.table("resume_history").insert({
                "user_phone": current_user.phone,
                "job_title": job_title,
                "company": "",
                "original_jd": request.jd_content,
                "original_resume": request.experience,
                "match_score": match_score,
                "keywords": keywords,
                "reconstructed_resume": refactored_resume
            }).execute()
        except Exception as e:
            logger.warning(f"保存简历历史失败: {e}")
    
    return response


def generate_mock_resume_analysis(jd_content: str, experience: str):
    """
    基于实际输入的 JD 和经历生成 mock 分析结果。
    不再是硬编码"ROS、SLAM、C++"这种通用数据。
    """
    import random
    
    # 从 JD 中简单提取关键词（取 JD 中的大写英文缩写和中文关键词）
    import re as re_module
    # 提取英文缩写词（如 ROS, C++, Python 等）
    english_keywords = re_module.findall(r'\b[A-Z][A-Za-z+#]+\b', jd_content)
    # 提取中文两字以上词语作为潜在关键词
    chinese_words = re_module.findall(r'[\u4e00-\u9fa5]{2,4}', jd_content)
    
    # 构建关键词列表
    all_potential = list(set(english_keywords))[:3] + list(set(chinese_words))[:3]
    keywords = []
    for kw in all_potential[:6]:
        matched = kw.lower() in experience.lower() or kw in experience
        keywords.append({
            "word": kw,
            "match": "true" if matched else "false",
            "reason": f"经历中{'有' if matched else '未'}体现{kw}相关内容"
        })
    if len(keywords) < 3:
        keywords += [
            {"word": "专业技能", "match": "true", "reason": "基本技能匹配"},
            {"word": "项目经验", "match": "true", "reason": "有相关实践"},
            {"word": "团队协作", "match": "true", "reason": "体现协作能力"}
        ][:3-len(keywords)]
    
    # 根据匹配度算分数
    matched_count = sum(1 for k in keywords if k["match"] == "true")
    match_score = min(95, 50 + matched_count * 10 + random.randint(-5, 10))
    
    # 重构简历（基于用户输入）
    exp_lines = experience.split('|') if '|' in experience else experience.split('\n')
    refactored_resume = "【优化后简历】\n\n"
    refactored_resume += f"个人概况：{exp_lines[0].strip() if exp_lines else '待补充'}\n\n"
    refactored_resume += "专业技能：\n"
    for kw in keywords:
        refactored_resume += f"- {kw['word']}：{'✅ 已匹配' if kw['match'] == 'true' else '⚠️ 建议补充'}\n"
    refactored_resume += "\n项目经验：\n"
    refactored_resume += f"（基于你的经历：{experience[:80]}...）\n"
    refactored_resume += "建议用 STAR 法则重新组织为：情境 → 任务 → 行动 → 结果\n"
    
    gen_suggestions = [
        "根据JD要求，突出与目标岗位最相关的项目经验和技能",
        "使用量化数据描述项目成果（如提升效率X%、服务X用户等）",
        "将JD中的关键词自然地融入你的经历描述中",
        "每个经历用STAR法则组织，控制在3-5行内",
        "技术岗建议补充GitHub/技术博客链接，产品岗建议补充产品分析案例"
    ]
    random.shuffle(gen_suggestions)
    suggestions = gen_suggestions[:3]
    
    return match_score, keywords, refactored_resume, suggestions


@app.post("/api/resume/analyze-upload", response_model=ResumeAnalysisResponse)
async def analyze_resume_upload(
    jd_content: str = Form(...),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    支持上传 PDF/Word 或粘贴简历文本。
    解析文件内容后，复用 analyze_resume 的分析逻辑。
    """
    experience = ""
    
    if resume_file and resume_file.filename:
        content = await resume_file.read()
        filename = resume_file.filename.lower()
        
        try:
            if filename.endswith('.pdf'):
                pdf_reader = PdfReader(io.BytesIO(content))
                experience = "\n".join(
                    page.extract_text() or "" for page in pdf_reader.pages
                )
            elif filename.endswith('.docx'):
                doc = Document(io.BytesIO(content))
                experience = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            else:
                # 纯文本文件
                experience = content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"文件解析失败: {e}")
            raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
    elif resume_text:
        experience = resume_text.strip()
    
    if not experience or len(experience) < 10:
        raise HTTPException(status_code=400, detail="简历内容过短，请上传完整简历或粘贴更多内容")
    
    # 复用文本分析接口
    request = ResumeAnalysisRequest(jd_content=jd_content, experience=experience)
    return await analyze_resume(request, current_user)


@app.get("/api/resume/history")
async def get_resume_history(current_user: Optional[User] = Depends(get_optional_user)):
    if not current_user:
        return []
    try:
        supabase = get_supabase()
        result = supabase.table("resume_history")\
            .select("id, job_title, company, match_score, keywords, created_at")\
            .eq("user_phone", current_user.phone)\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        return result.data
    except Exception as e:
        logger.warning(f"查询简历历史失败: {e}")
        return []

@app.get("/api/resume/{id}")
async def get_resume_by_id(id: str, current_user: User = Depends(get_current_active_user)):
    try:
        supabase = get_supabase()
        result = supabase.table("resume_history")\
            .select("id, job_title, company, original_jd, original_resume, match_score, keywords, reconstructed_resume, created_at")\
            .eq("id", id)\
            .eq("user_phone", current_user.phone)\
            .limit(1)\
            .execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Resume history not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"查询简历历史详情失败: {e}")
        raise HTTPException(status_code=500, detail="查询简历历史详情失败")

# 岗位名称映射（给 AI 生成题目用的中文名）
JOB_TYPE_NAMES_CN = {
    "robot": "机器人工程师",
    "ai": "AI算法工程师",
    "lowAltitude": "低空经济运营",
    "material": "新材料研发",
    "pm": "产品经理"
}

# 保留固定题库作为 DeepSeek 不可用时的兜底
JOB_TYPE_QUESTIONS_FALLBACK = {
    "robot": [
        "请介绍一下你对ROS机器人操作系统的理解，以及在项目中如何使用的？",
        "描述一个你参与过的机器人项目，你在其中负责什么？遇到了什么技术难点？",
        "如何设计一个室内服务机器人的导航避障方案？请从传感器选型到算法实现进行说明。",
        "谈谈你对人形机器人发展前景的看法，以及当前面临的主要技术瓶颈。",
        "如果让你设计一个工业协作机器人的安全策略，你会考虑哪些方面？"
    ],
    "ai": [
        "请解释Transformer架构的核心思想，以及Self-Attention机制的工作原理。",
        "描述你做过的一个AI项目，从数据准备到模型部署的完整流程。",
        "如何解决深度学习模型训练中的过拟合问题？请列举至少三种方法。",
        "谈谈你对大模型（LLM）在垂直领域应用的理解，以及可能面临的挑战。",
        "如果让你设计一个简历筛选AI系统，你会如何定义评估指标和优化目标？"
    ],
    "lowAltitude": [
        "请谈谈你对低空经济概念的理解，以及eVTOL行业的发展现状。",
        "低空经济运营需要关注哪些政策法规？如何确保合规运营？",
        "如果让你规划一条城市低空物流航线，你会考虑哪些因素？",
        "低空经济与智慧城市如何融合？请描述一个具体的应用场景。",
        "你认为低空经济运营面临的最大挑战是什么？如何应对？"
    ],
    "material": [
        "请介绍你熟悉的一种新型材料，其特性和应用前景。",
        "描述你在材料研发或测试方面的项目经验，使用了哪些表征手段？",
        "碳纤维复合材料在航空航天领域有哪些应用？其优势是什么？",
        "如何设计一个新材料从实验室到量产的验证流程？",
        "谈谈你对新能源电池材料（如固态电解质）发展趋势的看法。"
    ],
    "pm": [
        "请描述你从0到1做产品的完整流程，重点说明需求分析阶段的方法。",
        "如何判断一个产品需求是否值得做？你的优先级排序框架是什么？",
        "谈谈你对AI产品经理角色的理解，与传统产品经理有什么区别？",
        "描述一次你处理用户反馈并推动产品改进的经历。",
        "如果让你设计一个面向大学生的求职辅助产品，你会如何规划MVP？"
    ]
}

INTERVIEW_QUESTION_POOLS = {
    "robot": {
        "warmup": [
            "请用 60 秒介绍一个最能证明你适合机器人岗位的项目，并说清你负责的模块和结果。",
            "机器人项目常常跨算法、硬件和现场调试。你最近一次把问题定位到根因的过程是什么？"
        ],
        "foundation": [
            "在 ROS2 系统里，你会怎样拆分感知、定位、规划和控制节点，并处理时序与消息延迟？",
            "请比较 PID、MPC 等控制思路在轨迹跟踪中的取舍，并给出你会关注的调参指标。",
            "定位或感知结果抖动时，你会从传感器、标定、同步和算法四层怎样排查？"
        ],
        "project": [
            "讲一个你把算法从仿真或实验数据推进到真实设备的经历，性能落差出现在哪里？",
            "如果现场日志显示机器人偶发避障失败，你会保留哪些数据并设计怎样的复现方案？",
            "请选择一个项目说明你如何做性能评估：成功率、精度、时延和安全边界分别怎么看？"
        ],
        "scenario": [
            "为校园配送机器人设计一条从感知到规划控制的最小可落地方案，你会先保哪些能力？",
            "算力和功耗预算被压缩后，你会怎样在模型效果、实时性和稳定性之间做取舍？"
        ],
        "trend": [
            "具身智能热度很高。对校招候选人而言，哪些能力是真正能落到机器人系统里的？",
            "你如何判断一个机器人算法改动值得上线，而不是只在离线指标上变好？"
        ]
    },
    "ai": {
        "warmup": [
            "请介绍一个你做过的 AI 项目，重点说数据、指标、迭代决策和最终效果。",
            "如果只能展示一个项目证明你的工程能力，你会选哪个，为什么？"
        ],
        "foundation": [
            "请比较 SFT、偏好对齐和推理阶段优化分别解决什么问题，什么时候不该上复杂方案？",
            "做 RAG 时召回质量、重排、上下文组织和答案评测会怎样互相影响？",
            "训练或微调出现效果回退时，你会如何区分数据问题、评测问题和模型问题？"
        ],
        "project": [
            "讲一次你建立评测集或误差分析表的经历，它怎样改变了后续优化方向？",
            "模型离线分数提升但线上体验变差时，你会补看哪些质量、时延、成本和安全指标？",
            "讲一次你把模型能力接进真实应用的过程，最难的工程约束是什么？"
        ],
        "scenario": [
            "为校招简历分析助手设计一套可迭代的评测方案，怎样防止只会写漂亮建议？",
            "如果业务要求响应更快但不能明显牺牲质量，你会从模型、缓存、提示词和链路哪里下手？"
        ],
        "trend": [
            "Agent 很热。你会怎样判断一个任务需要 Agent，还是普通工作流更稳？",
            "请说一个你近期关注的多模态或大模型应用方向，并说明它的落地门槛。"
        ]
    },
    "lowAltitude": {
        "warmup": [
            "请用一个具体场景说明你理解的低空经济运营，不要只讲行业概念。",
            "如果你加入低空运营团队，前三个月最想先摸清哪三类数据？"
        ],
        "foundation": [
            "规划一条低空物流航线时，你会先核对哪些空域、气象、起降点和安全约束？",
            "请说明运营岗位如何把合规、安全和用户体验放进同一套流程里。",
            "遇到飞行计划临时受天气或场地影响，你会怎样做预案和沟通？"
        ],
        "project": [
            "讲一次你做运营方案或跨部门协同的经历，怎样把模糊目标变成可执行清单？",
            "如果要评估一次试运营，你会设计哪些指标来判断航线是否值得继续投入？",
            "请举例说明你怎样处理安全风险、现场异常或用户投诉。"
        ],
        "scenario": [
            "为文旅低空体验活动设计首周试运营方案，怎样安排流程、人员和风险兜底？",
            "一条航线准点率下降但需求上涨，你会怎样平衡扩量和服务稳定性？"
        ],
        "trend": [
            "低空场景很多。你认为校招运营岗位最需要避免哪类只讲概念、不讲落地的判断？",
            "你如何判断一个低空应用是短期热点，还是能形成持续运营闭环？"
        ]
    },
    "material": {
        "warmup": [
            "请介绍一个最能体现你材料研发思路的课题，说明假设、实验和结论。",
            "你做材料实验时遇到过哪次结果不稳定？后来如何确认原因？"
        ],
        "foundation": [
            "选择一种你熟悉的表征手段，说明它能回答什么问题，不能回答什么问题。",
            "配方或工艺参数很多时，你会怎样设计实验，避免只靠逐个试错？",
            "材料性能提升后，你会怎样确认它不是由测试条件变化造成的假提升？"
        ],
        "project": [
            "讲一次你把实验结果整理成可复现实验记录或数据结论的过程。",
            "如果小试表现很好但放大后波动明显，你会先排查原料、工艺还是设备？为什么？",
            "请用一个项目说明你如何兼顾性能、成本、良率和安全性。"
        ],
        "scenario": [
            "为新能源材料候选方案设计从筛选到验证的最小研发路径，你会设哪些门槛？",
            "客户反馈批次差异影响应用，你会怎样组织验证并给出下一轮改进计划？"
        ],
        "trend": [
            "请说一个你关注的材料方向，并解释它离规模化应用还差哪一步。",
            "材料研发越来越数据化。你认为数据工具最能先改善哪个环节？"
        ]
    },
    "pm": {
        "warmup": [
            "请介绍一个你推动过的产品或项目，重点说目标、取舍和结果。",
            "如果你应聘 AI 产品经理，哪段经历最能证明你不是只会写需求文档？"
        ],
        "foundation": [
            "请说明需求优先级排序时，你怎样同时看用户价值、业务收益、成本和风险。",
            "AI 产品上线前，你会怎样定义质量、时延、成本和安全的验收指标？",
            "当模型回答有波动时，PRD、评测样例和兜底交互分别要补什么？"
        ],
        "project": [
            "讲一次你通过用户反馈或数据分析改变产品方案的经历。",
            "如果研发说方案能做但上线维护成本高，你会怎样拆 MVP 和后续版本？",
            "讲一个你写过的需求，从问题定义到验证闭环哪里最容易失真？"
        ],
        "scenario": [
            "为大学生面试练习产品设计一次迭代，怎样证明题目更有参考价值而不是更花哨？",
            "AI 功能点击率高但留存低，你会先排查内容质量、引导流程还是目标用户？"
        ],
        "trend": [
            "你如何判断一个 AI 功能该做成自动执行、辅助建议，还是只做信息检索？",
            "请说一个你近期关注的 AI 产品案例，并解释它的关键体验取舍。"
        ]
    }
}

def build_interview_question_set(job_type: str) -> List[str]:
    import random

    pool = INTERVIEW_QUESTION_POOLS.get(job_type, INTERVIEW_QUESTION_POOLS["ai"])
    ordered_sections = ("warmup", "foundation", "project", "scenario", "trend")
    return [random.choice(pool[section]) for section in ordered_sections]

INTERVIEW_CAPABILITY_FOCUS = {
    "robot": "真实设备调试、系统稳定性、传感器与控制链路、性能验证、安全边界",
    "ai": "数据质量、评测体系、模型工程、线上时延与成本、可靠性与业务落地",
    "lowAltitude": "合规安全、航线运营、现场应急、跨部门协同、试运营数据闭环",
    "material": "实验设计、表征验证、放大与良率、成本约束、研发结论可复现",
    "pm": "用户问题定义、业务指标、AI 能力边界、方案取舍、上线验证闭环"
}

INTERVIEW_FOLLOW_UP_FALLBACKS = {
    "robot": [
        "你刚才提到项目落地，请具体说一个真实设备上出现过的异常，你怎样定位到根因？",
        "这个方案如果要上线，你会用哪些指标证明稳定性和安全边界够了？",
        "在这个项目里，哪些部分是你亲自负责，哪些依赖团队协作？"
    ],
    "ai": [
        "你刚才提到项目效果，请具体说评测集怎么构建，怎样判断优化真的有效？",
        "如果线上质量、时延和成本同时受压，你会先做哪两个取舍，为什么？",
        "在这个项目里你亲自负责的数据、模型和工程环节分别是什么？"
    ],
    "lowAltitude": [
        "你刚才提到运营方案，请说一个现场异常或安全风险，你会怎样做预案和事后改进？",
        "这个场景要试运营，你会用哪些数据判断它能不能继续扩量？",
        "这里最关键的合规或跨部门协同点是什么？你会怎么推进？"
    ],
    "material": [
        "你刚才提到实验结论，请说明怎样排除测试条件变化造成的假提升？",
        "如果从小试走向放大，你最担心哪类波动，准备怎样验证？",
        "这项工作里你亲自做了哪些实验设计、数据分析和结论判断？"
    ],
    "pm": [
        "你刚才提到方案价值，请说出核心用户问题、关键指标和一次重要取舍。",
        "如果模型能力有波动，你会怎样设计评测样例、兜底交互和上线门槛？",
        "这次项目里你亲自推动了哪些决策，怎样验证不是伪需求？"
    ]
}

def build_fallback_follow_up(job_type: str, answer: str, next_turn: int) -> str:
    import random

    if len(answer.strip()) < 50:
        return "你的回答还比较概括。请用一个真实项目补充：背景是什么、你做了什么、结果怎么验证？"
    if not any(marker in answer for marker in ["%", "指标", "提升", "降低", "结果", "评测", "验证"]):
        return "你提到了做法。请继续说清结果怎么衡量：你看了哪些指标，怎样确认它对业务或岗位目标有价值？"

    options = INTERVIEW_FOLLOW_UP_FALLBACKS.get(job_type, INTERVIEW_FOLLOW_UP_FALLBACKS["ai"])
    return options[(next_turn - 1) % len(options)]

def generate_interview_follow_up(job_type: str, previous_question: str, answer: str, next_turn: int) -> str:
    job_name = JOB_TYPE_NAMES_CN.get(job_type, "技术岗位")
    focus = INTERVIEW_CAPABILITY_FOCUS.get(job_type, INTERVIEW_CAPABILITY_FOCUS["ai"])
    prompt = f"""你是一位资深 HR 与业务面试官，正在为「{job_name}」岗位做真实模拟面试。

你不是闲聊，也不是直接讲答案。你要基于候选人刚才的回答追问，考察岗位真实业务需要的能力。
岗位重点能力：{focus}

当前轮次：第 {next_turn} 轮，共 5 轮。
上一问：{previous_question}
候选人回答：{answer}

请生成下一道追问，要求：
1. 必须抓住候选人回答里提到的项目、指标、技术取舍、个人贡献或风险点追问。
2. 如果回答空泛，追问具体案例、数据、验证方法或个人边界。
3. 如果回答较强，追问 trade-off、失败原因、业务落地或上线标准。
4. 问题要像专业面试官会问的中文问题，一次只问一个核心问题。
5. 不要评价候选人，不要给答案，不要输出 JSON，不超过 80 个中文字符。"""

    result = call_fast_interview_api(prompt)
    if result:
        question = result.strip().strip('"').strip()
        if question:
            return question[:160]
    return build_fallback_follow_up(job_type, answer, next_turn)

INTERVIEW_DYNAMIC_MODULES = {
    "motivation": "公司认知与求职动机",
    "business": "底层业务逻辑拆解能力与预判力",
    "evidence": "细节与价值感真实性、迭代颗粒度",
    "self_proof": "终极能力与自信度自证",
    "growth": "成长性、自知之明与主人翁意识",
    "values": "离职动机与职业价值观",
    "pressure": "压力、情商与薪资谈判",
}

INTERVIEW_DYNAMIC_QUESTIONS = {
    "motivation": "感谢你的自我介绍。我想先听听：你对我们目标公司或这个岗位有什么了解？为什么你会觉得这个岗位适合你？",
    "business": "请用三句话说清楚这个岗位所在业务是怎么通过“流量-产品-交付”三个环节创造价值的。如果你明天入职，你觉得链路里最脆弱、最值得优化的一环是哪一个？为什么？",
    "business_probe": "凭直觉猜一下，这类公司最赚钱或最关键的核心业务线是哪一条？为什么？你可以猜，但要给出逻辑。",
    "evidence": "给我讲一个你最关键、最棘手的案例：你具体做了什么？如果现在让你回到那个场景重来，你会改变哪一个具体动作，让结果更好？",
    "self_proof": "时间有限，我们直接聊核心：你凭什么觉得你能胜任这份工作？别说空话，1分钟内从三个层面说服我：你做过什么、你能解决什么问题、为什么你比其他人更适合。",
    "self_proof_probe": "你给我一个具体证据。比如你入职第一周，哪一项工作能立刻上手并产出价值？产出怎么衡量？",
    "growth": "你觉得自己在这个岗位上，未来一年内最需要补的课是什么？你这个性格或做事风格里，最让老板头疼的一点可能是什么？",
    "owner": "如果你入职一个月后发现公司某个流程效率很低，你会不会主动告诉我？你会用什么方式、什么语言提出来？",
    "values": "我想听你真实评价上一段实习或项目经历：它做得最对的一件事和最错的一件事分别是什么？基于你的价值观，你离开的核心原因或结束后的最大反思是什么？",
    "pressure": "面试快结束了。如果你入职第二周，直属上级当着同事的面把你的方案骂得一文不值，说你根本不懂业务，你会怎么办？请你现在演给我看。",
    "salary": "假如我现在代表公司口头给你 Offer，但薪资比你预期低 20%。你有30秒，在不失礼貌的前提下说服我为你重新申请涨幅。你会怎么组织语言？",
}

INTERVIEW_DYNAMIC_FOCUS = {
    "robot": "机器人系统的流量可以理解为场景需求和客户入口，产品是硬件、算法和系统方案，交付是现场部署、调试、安全运维和售后稳定性。",
    "ai": "AI岗位的业务链路通常是需求来源或用户流量、模型/数据/应用产品、上线交付后的效果验证、成本控制和持续迭代。",
    "lowAltitude": "低空经济运营要看场景获客与资源入口、航线/服务产品设计、飞行交付、合规安全、异常响应和改进数据。",
    "material": "新材料研发要把客户或课题需求看作流量，配方/工艺/性能看作产品，样品验证、放大、良率和客户应用看作交付。",
    "pm": "产品经理要拆用户来源、产品体验和功能价值、研发上线交付、数据验证、留存转化和跨团队协同。",
}

def build_dynamic_interview_question_set(job_type: str) -> List[str]:
    return [INTERVIEW_DYNAMIC_QUESTIONS["motivation"]]

def assess_interview_answer_signal(answer: str) -> dict:
    text = answer.strip()
    lower = text.lower()
    evidence_markers = ["%", "提升", "降低", "增长", "减少", "数据", "指标", "用户", "成本", "时延", "准确率", "上线", "验证", "ROI", "roi"]
    structure_markers = ["首先", "其次", "最后", "第一", "第二", "第三", "背景", "目标", "行动", "结果", "STAR", "star"]
    motivation_markers = ["公司", "业务", "产品", "岗位", "赛道", "用户", "客户", "市场", "交付", "价值", "匹配"]
    risk_markers = ["不知道", "不了解", "随便", "都可以", "离家近", "工资", "稳定", "领导差", "同事", "太累", "没想过"]
    high_signal = sum(marker in text for marker in evidence_markers) + sum(marker in text for marker in structure_markers)
    match_signal = sum(marker in text for marker in motivation_markers)
    risk_signal = sum(marker in text for marker in risk_markers)
    score = 4 + min(3, len(text) // 90) + min(2, high_signal) + min(1, match_signal // 2) - min(3, risk_signal)
    score = max(2, min(10, score))
    if len(text) < 50 or risk_signal >= 2:
        level = "weak"
    elif score >= 8:
        level = "strong"
    elif score >= 6:
        level = "normal"
    else:
        level = "weak"
    return {"score": score, "level": level, "high_signal": high_signal, "match_signal": match_signal, "risk_signal": risk_signal}

def choose_next_interview_module(interview: dict, answer_signal: dict, next_turn: int) -> str:
    asked = interview.setdefault("modules", ["motivation"])
    previous_module = asked[-1] if asked else "motivation"
    level = answer_signal["level"]

    if next_turn >= 5:
        module = "pressure" if "pressure" not in asked else "salary"
    elif previous_module == "motivation":
        module = "business_probe" if level == "weak" else "business"
    elif previous_module in ("business", "business_probe"):
        module = "evidence" if level != "strong" else "self_proof"
    elif previous_module == "evidence":
        module = "pressure" if level == "weak" else "self_proof"
    elif previous_module == "self_proof":
        module = "self_proof_probe" if level == "weak" else "growth"
    elif previous_module in ("growth", "owner"):
        module = "values" if level != "weak" else "pressure"
    else:
        module = "pressure"

    asked.append(module)
    return module

def build_dynamic_fallback_question(job_type: str, module: str, previous_question: str, answer: str, next_turn: int) -> str:
    if len(answer.strip()) < 50 and module not in ("pressure", "salary"):
        return "你刚才的回答还比较泛。请补一个真实案例：背景是什么、你具体做了什么、结果用什么指标证明？"
    return INTERVIEW_DYNAMIC_QUESTIONS.get(module, INTERVIEW_DYNAMIC_QUESTIONS["evidence"])

def generate_interview_questions(job_type: str) -> List[str]:
    return build_dynamic_interview_question_set(job_type)

def generate_interview_follow_up(job_type: str, previous_question: str, answer: str, next_turn: int, interview: Optional[dict] = None) -> str:
    interview = interview or {"modules": ["motivation"]}
    answer_signal = assess_interview_answer_signal(answer)
    module = choose_next_interview_module(interview, answer_signal, next_turn)
    job_name = JOB_TYPE_NAMES_CN.get(job_type, "目标岗位")
    focus = INTERVIEW_DYNAMIC_FOCUS.get(job_type, INTERVIEW_DYNAMIC_FOCUS["ai"])
    fallback = build_dynamic_fallback_question(job_type, module, previous_question, answer, next_turn)

    prompt = f"""你是一位拥有10年以上经验的洞察型跨行业资深HR总监兼情商测评专家，正在面试「{job_name}」候选人。
核心原则：面试=销售；录用概率=价值感×信任感×匹配度；业务都要拆成流量、产品、交付；不要安慰候选人，要还原真实工作状态。
岗位业务参考：{focus}

当前第 {next_turn}/5 轮。
上一轮问题：{previous_question}
候选人回答：{answer}
上一答质量判断：{answer_signal["level"]}，风险信号={answer_signal["risk_signal"]}。
下一模块：{INTERVIEW_DYNAMIC_MODULES.get(module, module)}
建议追问方向：{fallback}

请只输出下一道中文追问。要求：
1. 必须根据候选人上一答动态追问，不要机械按顺序。
2. 如果回答空泛，就死磕证据、数据、个人贡献或业务链路。
3. 如果回答较强，就跳到更高压的胜任自证、预判、失败原因、情商或薪资谈判。
4. 一次只问一个核心问题，不给答案，不评价候选人，不输出JSON。
5. 控制在100个中文字符以内。"""

    result = call_fast_interview_api(prompt)
    if result:
        question = result.strip().strip('"').strip()
        if question:
            return question[:180]
    return fallback

def generate_interview_questions(job_type: str) -> List[str]:
    """
    通过 DeepSeek 动态生成面试题。
    
    工作原理：
    1. 构造 prompt，告诉 AI 目标岗位和出题要求
    2. 调用 DeepSeek API 生成 5 道题
    3. 解析返回的 JSON 数组
    4. 如果 API 不可用，降级到固定题库
    """
    if os.getenv("INTERVIEW_LEGACY_QUESTIONS", "false").lower() != "true":
        return build_dynamic_interview_question_set(job_type)

    job_name = JOB_TYPE_NAMES_CN.get(job_type, "技术岗位")
    
    prompt = f"""你现在是一位经验丰富的面试官，正在为「{job_name}」岗位面试应届毕业生。

请生成 5 道面试题，要求：
1. 题目难度由浅入深，覆盖不同考察维度
2. 第1题：自我介绍/岗位认知（考察表达能力和职业规划）
3. 第2题：专业基础知识（考察技术功底）
4. 第3题：项目/实践经验（考察动手能力）
5. 第4题：场景设计/问题解决（考察思维能力）
6. 第5题：行业认知/职业发展（考察视野和潜力）
7. 每道题要具体、有区分度，不要泛泛而谈
8. 针对应届毕业生，不要出太偏太难的题

请直接输出一个 JSON 数组，格式如下：
["题目1", "题目2", "题目3", "题目4", "题目5"]

只输出 JSON 数组，不要输出其他内容。"""

    result = call_deepseek_api(prompt)
    
    if result:
        try:
            # 尝试提取 JSON 数组
            import re
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                questions = json.loads(match.group())
                if isinstance(questions, list) and len(questions) >= 5:
                    return questions[:5]
        except Exception as e:
            logger.warning(f"解析 AI 生成的面试题失败: {e}")
    
    # 降级到固定题库
    return JOB_TYPE_QUESTIONS_FALLBACK.get(job_type, JOB_TYPE_QUESTIONS_FALLBACK["ai"])

active_interviews = {}

@app.post("/api/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    # 用 DeepSeek 动态生成题目（降级到固定题库当 API 不可用时）
    questions = generate_interview_questions(request.job_type)
    interview_id = f"int-{datetime.utcnow().timestamp()}"
    active_interviews[interview_id] = {
        "job_type": request.job_type,
        "questions": questions[:1],
        "question_plan": questions,
        "answers": [],
        "scores": [],
        "feedbacks": [],
        "modules": ["motivation"]
    }
    return InterviewStartResponse(id=interview_id, questions=questions[:1])

def generate_rule_based_interview_feedback(question: str, answer: str, job_type: str):
    text = answer.strip()
    length = len(text)
    structure_markers = ["首先", "其次", "最后", "第一", "第二", "第三", "STAR", "背景", "任务", "行动", "结果", "指标"]
    evidence_markers = ["%", "提升", "降低", "用户", "数据", "指标", "准确率", "时延", "成本", "上线", "验证"]
    job_keywords = {
        "robot": ["ROS", "ROS2", "传感器", "标定", "定位", "规划", "控制", "仿真", "日志", "实时"],
        "ai": ["数据", "评测", "模型", "RAG", "微调", "召回", "指标", "推理", "成本", "安全"],
        "lowAltitude": ["合规", "空域", "航线", "气象", "安全", "运营", "应急", "起降", "准点", "异常"],
        "material": ["实验", "表征", "工艺", "配方", "性能", "良率", "放大", "批次", "成本", "验证"],
        "pm": ["用户", "需求", "指标", "MVP", "PRD", "评测", "留存", "成本", "风险", "迭代"]
    }
    keywords = job_keywords.get(job_type, job_keywords["ai"])

    completeness = 4 + min(3, length // 80) + (1 if any(k in text for k in keywords) else 0)
    logic = 5 + min(2, sum(1 for marker in structure_markers if marker in text)) + (1 if "因为" in text or "所以" in text else 0)
    depth = 4 + min(3, sum(1 for keyword in keywords if keyword in text)) + (1 if any(marker in text for marker in evidence_markers) else 0)
    expression = 5 + (1 if length >= 80 else 0) + min(2, sum(1 for marker in structure_markers if marker in text))
    match = 4 + min(4, sum(1 for keyword in keywords if keyword in text))

    raw_scores = [completeness, logic, depth, expression, match]
    scores = [max(3, min(10, score)) for score in raw_scores]
    labels = ["内容完整性", "逻辑清晰度", "专业深度", "表达结构化", "岗位匹配度"]
    comments = [
        "回答覆盖了问题主干，继续补充关键背景和结果会更完整。" if scores[0] >= 7 else "回答还偏短，建议补齐背景、行动和结果。",
        "表达有一定层次，面试官能跟上你的思路。" if scores[1] >= 7 else "建议用“先结论、再展开、最后说明验证方式”的结构组织答案。",
        "能看到岗位相关理解，若加入更多技术或业务细节会更有说服力。" if scores[2] >= 7 else "专业关键词和具体方法还不够，建议补一个真实项目细节。",
        "表达比较清楚，适合继续压缩成 60-90 秒版本。" if scores[3] >= 7 else "建议使用 STAR 或分点表达，避免只堆叙述。",
        "回答与岗位有连接，可以继续强化岗位关键词。" if scores[4] >= 7 else "需要更明确地把经历扣回目标岗位要求。"
    ]
    avg_score = round(sum(scores) / len(scores))

    if avg_score >= 8:
        suggestion = "这版回答已经有可用度。下一步把结果量化，并在结尾补一句你从中学到的岗位方法论。"
    elif avg_score >= 6:
        suggestion = "建议按 STAR 重组：先给一句结论，再讲具体项目动作，最后用数据或验证结果收束。"
    else:
        suggestion = "先不要追求完整长答案，优先补充一个具体案例、两个岗位关键词和一个可衡量结果。"

    return {
        "score": avg_score,
        "dimensions": [
            {"label": label, "score": score, "comment": comment}
            for label, score, comment in zip(labels, scores, comments)
        ],
        "suggestion": suggestion
    }

def generate_rule_based_interview_feedback(question: str, answer: str, job_type: str):
    text = answer.strip()
    signal = assess_interview_answer_signal(text)
    length_score = min(3, len(text) // 90)
    has_business = any(k in text for k in ["流量", "产品", "交付", "业务", "用户", "客户", "盈利", "成本", "价值", "市场"])
    has_detail = any(k in text for k in ["我负责", "具体", "当时", "问题", "动作", "如果重来", "优化前", "优化后"])
    has_company = any(k in text for k in ["公司", "岗位", "产品线", "赛道", "匹配", "了解", "选择", "适合"])
    has_growth = any(k in text for k in ["短板", "不足", "学习", "补课", "改进", "老板", "流程", "主动", "沟通"])
    has_values = any(k in text for k in ["离开", "价值观", "前公司", "实习", "客观", "原因", "反思", "评价"])
    has_eq = any(k in text for k in ["我理解", "先确认", "沟通", "方案", "共赢", "评估期", "绩效", "申请", "冷静"])
    risk_penalty = min(3, signal["risk_signal"])

    hard = 4 + length_score + (2 if has_business else 0) + min(1, signal["high_signal"])
    detail = 4 + length_score + (2 if has_detail else 0) + min(1, signal["high_signal"])
    motivation = 4 + length_score + (2 if has_company else 0) + min(1, signal["match_signal"])
    growth = 4 + length_score + (2 if has_growth else 0)
    values = 5 + (2 if has_values else 0) + (1 if "客观" in text or "反思" in text else 0) - risk_penalty
    eq = 4 + length_score + (2 if has_eq else 0) - risk_penalty

    scores = [hard, detail, motivation, growth, values, eq]
    scores = [max(2, min(10, int(score))) for score in scores]
    labels = ["硬性能力", "细节与迭代能力", "公司认知与求职动机", "成长与自知之明", "离职动机与价值观", "情商与压力管理"]
    comments = [
        "能看到业务链路意识，但还要更明确流量-产品-交付里的关键约束。" if scores[0] >= 7 else "业务拆解偏弱，需要先说清价值链、脆弱环节和优化优先级。",
        "有一定细节意识，继续补充个人动作与前后指标。" if scores[1] >= 7 else "案例颗粒度不足，需要讲清具体动作、失败点和重来会改哪一步。",
        "能把经历扣回岗位和公司价值，动机可信度较好。" if scores[2] >= 7 else "公司认知或求职动机偏泛，容易被判断为海投或准备不足。",
        "能承认短板并给出改进方向，成熟度尚可。" if scores[3] >= 7 else "自我认知还浅，需要说清短板、补课计划和主动改流程的方式。",
        "价值观表达相对理性，没有明显甩锅或情绪化风险。" if scores[4] >= 7 else "价值观信号不够稳，避免抱怨式表达，要客观评价经历和选择原因。",
        "压力下有沟通和解决问题意识，关系处理较稳。" if scores[5] >= 7 else "压力应对偏弱，要先共情确认问题，再给解决路径和可验证承诺。",
    ]
    avg_score = round(sum(scores) / len(scores))
    weakest = labels[scores.index(min(scores))]
    suggestion = f"下一轮重点补强「{weakest}」。请把回答改成：先给结论，再给真实场景和个人动作，最后用指标、验证结果或沟通方案证明价值感、信任感和匹配度。"

    return {
        "score": avg_score,
        "dimensions": [
            {"label": label, "score": score, "comment": comment}
            for label, score, comment in zip(labels, scores, comments)
        ],
        "suggestion": suggestion
    }

STRICT_INTERVIEW_DIMENSIONS = [
    "问题相关性",
    "内容准确性",
    "结构完整性",
    "证据与细节",
    "岗位匹配度",
]

STRICT_JOB_KEYWORDS = {
    "robot": ["机器人", "ROS", "传感器", "定位", "规划", "控制", "设备", "调试", "算法", "安全"],
    "ai": ["AI", "模型", "数据", "评测", "算法", "RAG", "训练", "推理", "指标", "上线"],
    "lowAltitude": ["低空", "航线", "运营", "合规", "安全", "空域", "气象", "起降", "物流", "异常"],
    "material": ["材料", "实验", "表征", "工艺", "配方", "性能", "放大", "批次", "验证", "成本"],
    "pm": ["产品", "用户", "需求", "指标", "MVP", "PRD", "迭代", "上线", "验证", "成本"],
}

STRICT_OFF_TOPIC_JOB_MARKERS = {
    "robot": ["机器人", "ROS", "传感器", "定位", "路径规划", "规划", "控制", "硬件", "设备", "调试", "巡检", "配送", "仓储"],
    "ai": ["AI", "模型", "算法", "RAG", "微调", "训练", "推理", "准确率", "召回", "embedding", "大模型"],
    "lowAltitude": ["低空", "航线", "空域", "起降", "飞行", "无人机", "气象", "物流", "合规"],
    "material": ["材料", "实验", "表征", "工艺", "配方", "性能", "良率", "批次", "放大", "样品", "导电率", "强度"],
    "pm": ["产品经理", "产品", "用户", "需求", "MVP", "PRD", "原型", "留存", "转化", "迭代"],
}

STRICT_BAD_ANSWER_MARKERS = [
    "不知道", "不会", "不懂", "随便", "没有想过", "不知道怎么答", "哈哈", "测试",
    "吃饭", "睡觉", "天气", "你好", "无", "不知道了",
]

STRICT_EVIDENCE_MARKERS = [
    "%", "数据", "指标", "提升", "降低", "减少", "增长", "用户", "成本", "时延",
    "准确率", "上线", "验证", "结果", "项目", "负责", "方案",
]

STRICT_STRUCTURE_MARKERS = [
    "首先", "其次", "最后", "第一", "第二", "第三", "背景", "目标", "行动",
    "结果", "因为", "所以", "如果", "我负责",
]


def _score_dimension(label: str, score: int, comment: str) -> dict:
    return {"label": label, "score": max(0, min(10, int(score))), "comment": comment}


def _qualitative_payload(hit_points: list, missed_points: list, rewrite_advice: list, summary: str) -> dict:
    return {
        "hit_points": hit_points,
        "missed_points": missed_points,
        "rewrite_advice": rewrite_advice,
        "summary": summary,
    }


def _strict_zero_feedback(reason: str, suggestion: str = "请重新围绕面试问题作答，补充具体场景、个人动作和可验证结果。") -> dict:
    judgment = "答非所问" if "答非所问" in reason or "没有回应" in reason else "无效回答"
    return {
        "score": 0,
        "is_relevant": False,
        "strict_reason": reason,
        "dimensions": [
            _score_dimension("问题判断", 0, judgment),
            _score_dimension("原因", 0, reason),
            _score_dimension("修改方向", 0, suggestion),
        ],
        "suggestion": suggestion,
        **_qualitative_payload(
            hit_points=[],
            missed_points=[
                judgment,
                reason,
            ],
            rewrite_advice=[suggestion],
            summary=f"{judgment}：{reason}",
        ),
    }


def _meaningful_text_length(text: str) -> int:
    return len([ch for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff"])


def _has_invalid_bad_answer(text: str, meaningful_len: int) -> bool:
    normalized = "".join(ch for ch in text.strip() if not ch.isspace())
    if normalized in ["不知道", "不会", "不懂", "随便", "无", "没有", "不知道了", "测试", "test"]:
        return True

    direct_bad_phrases = [
        "我不知道", "我不会", "我不懂", "不知道怎么答", "没有想过", "随便答", "随便说",
    ]
    if meaningful_len <= 25 and any(phrase in normalized for phrase in direct_bad_phrases):
        return True

    irrelevant_markers = ["吃饭", "睡觉", "天气", "哈哈"]
    if meaningful_len <= 40 and any(marker in normalized for marker in irrelevant_markers):
        return True

    return False


def _question_keywords(question: str, job_type: str) -> list:
    base = STRICT_JOB_KEYWORDS.get(job_type, STRICT_JOB_KEYWORDS["ai"])
    extra = []
    for keyword in [
        "项目", "指标", "数据", "用户", "业务", "成本", "上线", "验证", "安全",
        "合规", "实验", "需求", "模型", "算法", "产品", "运营", "材料", "机器人",
    ]:
        if keyword in question:
            extra.append(keyword)
    return list(dict.fromkeys(base + extra))


def _detect_off_topic_job(answer: str, target_job_type: str) -> Optional[str]:
    target_markers = STRICT_OFF_TOPIC_JOB_MARKERS.get(target_job_type, [])
    target_hits = sum(1 for marker in target_markers if marker in answer)
    other_hits = {}
    for job_type, markers in STRICT_OFF_TOPIC_JOB_MARKERS.items():
        if job_type == target_job_type:
            continue
        hits = sum(1 for marker in markers if marker in answer)
        if hits:
            other_hits[job_type] = hits

    if not other_hits:
        return None

    strongest_job, strongest_hits = max(other_hits.items(), key=lambda item: item[1])
    if strongest_hits >= 3 and strongest_hits >= target_hits + 2:
        names = {
            "robot": "机器人工程师",
            "ai": "AI算法工程师",
            "lowAltitude": "低空经济运营",
            "material": "新材料研发",
            "pm": "产品经理",
        }
        return f"回答明显围绕{names.get(strongest_job, strongest_job)}，没有回应{names.get(target_job_type, target_job_type)}岗位要求，属于答非所问。"

    return None


def _assess_strict_answer(question: str, answer: str, job_type: str) -> dict:
    text = answer.strip()
    meaningful_len = _meaningful_text_length(text)
    if meaningful_len == 0:
        return {"valid": False, "reason": "回答为空，本题 0 分。"}
    if meaningful_len < 8:
        return {"valid": False, "reason": "回答过短，无法形成有效面试作答，本题 0 分。"}
    if len(set(text.replace(" ", ""))) <= 2 and len(text) >= 6:
        return {"valid": False, "reason": "回答疑似重复字符或无意义内容，本题 0 分。"}
    if _has_invalid_bad_answer(text, meaningful_len):
        return {"valid": False, "reason": "回答明确表示不会、随便作答或与面试无关，本题 0 分。"}

    off_topic_reason = _detect_off_topic_job(text, job_type)
    if off_topic_reason:
        return {"valid": False, "reason": off_topic_reason}

    keywords = _question_keywords(question, job_type)
    keyword_hits = sum(1 for keyword in keywords if keyword and keyword in text)
    evidence_hits = sum(1 for marker in STRICT_EVIDENCE_MARKERS if marker in text)
    structure_hits = sum(1 for marker in STRICT_STRUCTURE_MARKERS if marker in text)
    has_project_signal = any(marker in text for marker in ["项目", "实习", "经历", "负责", "做过", "方案", "场景"])

    relevance = min(10, keyword_hits * 2 + (2 if has_project_signal else 0) + (1 if meaningful_len >= 60 else 0))
    if relevance == 0 and meaningful_len < 40:
        return {"valid": False, "reason": "回答与问题和岗位关键词没有明显关联，本题 0 分。"}
    if relevance == 0 and evidence_hits == 0:
        return {"valid": False, "reason": "回答答非所问，没有体现岗位相关内容，本题 0 分。"}

    accuracy = min(10, 2 + keyword_hits * 2 + evidence_hits)
    structure = min(10, 2 + structure_hits * 2 + (1 if meaningful_len >= 80 else 0))
    evidence = min(10, evidence_hits * 2 + (2 if has_project_signal else 0) + (1 if meaningful_len >= 100 else 0))
    match = min(10, keyword_hits * 2 + (2 if has_project_signal else 0))

    if relevance <= 1:
        cap = 3
    elif evidence == 0 and meaningful_len < 80:
        cap = 4
    else:
        cap = 10

    raw_total = round((relevance * 0.30) + (accuracy * 0.25) + (structure * 0.15) + (evidence * 0.15) + (match * 0.15))
    total = min(cap, raw_total)

    return {
        "valid": True,
        "relevance": relevance,
        "accuracy": accuracy,
        "structure": structure,
        "evidence": evidence,
        "match": match,
        "total": total,
        "keyword_hits": keyword_hits,
        "evidence_hits": evidence_hits,
        "structure_hits": structure_hits,
        "cap": cap,
    }


def generate_rule_based_interview_feedback(question: str, answer: str, job_type: str):
    assessment = _assess_strict_answer(question, answer, job_type)
    if not assessment["valid"]:
        return _strict_zero_feedback(assessment["reason"])

    return build_rule_based_interview_feedback(question, answer, job_type, assessment)

    total = assessment["total"]
    dimensions = [
        _score_dimension(
            "问题相关性",
            assessment["relevance"],
            "回答与题目和岗位有明确关联。" if assessment["relevance"] >= 6 else "回答和题目的关联偏弱，需要先扣回问题本身。",
        ),
        _score_dimension(
            "内容准确性",
            assessment["accuracy"],
            "能体现一定专业判断。" if assessment["accuracy"] >= 6 else "专业判断或关键概念不足，需要补充方法和边界。",
        ),
        _score_dimension(
            "结构完整性",
            assessment["structure"],
            "回答有基本结构。" if assessment["structure"] >= 6 else "结构偏散，建议使用“结论-动作-结果-下一步改法”。",
        ),
        _score_dimension(
            "证据与细节",
            assessment["evidence"],
            "提供了项目、指标或验证信号。" if assessment["evidence"] >= 6 else "缺少可验证证据，不能只讲态度或泛泛思路。",
        ),
        _score_dimension(
            "岗位匹配度",
            assessment["match"],
            "能看出和岗位能力要求的连接。" if assessment["match"] >= 6 else "需要明确说明这段经历如何匹配目标岗位。",
        ),
    ]
    suggestion = (
        "本题按严格评分规则计算。下一版请围绕题目先给结论，再补充一个真实项目、你的具体动作、"
        "量化结果或下一步改法；如果没有项目，也要说明方法、边界和验证方式。"
    )
    if assessment["cap"] < 10:
        suggestion = (
            f"本题触发分数上限规则，最高只能给 {assessment['cap']} 分。"
            "原因是相关性或证据不足。请先回答题目本身，再补具体例子和结果。"
        )
    hit_points = []
    if assessment["relevance"] >= 4:
        hit_points.append("回答能扣回题目和目标岗位，没有完全跑题。")
    if assessment["structure"] >= 4:
        hit_points.append("回答已经有一定表达结构，面试官能看到基本思路。")
    if assessment["evidence"] >= 4:
        hit_points.append("回答里出现了项目、结果或验证信号。")
    if assessment["match"] >= 4:
        hit_points.append("回答尝试把个人经历和岗位要求连接起来。")

    missed_points = []
    if assessment["relevance"] < 6:
        missed_points.append("对题目本身的回应还不够直接，开头需要先给明确结论。")
    if assessment["evidence"] < 6:
        missed_points.append("缺少可验证证据，比如具体项目、个人动作、数据结果或测试记录。")
    if assessment["match"] < 6:
        missed_points.append("岗位匹配还偏泛，需要明确说明这段经历为什么适合目标岗位。")
    if assessment["structure"] < 6:
        missed_points.append("表达结构还可以更清楚，建议按“结论-场景-动作-结果-下一步改法”组织。")

    rewrite_advice = [
        "开头先用一句话回答“我为什么适合这个岗位”。",
        "中间补一个真实项目或真实经历，说明背景、你负责的动作和解决的问题。",
        "结尾把经历扣回岗位要求，说明它能证明你的哪项能力。",
    ]
    dimensions = [
        _score_dimension(
            "切中的点",
            0,
            "；".join(hit_points) if hit_points else "这版回答有基本信息量，但还没有形成清楚的岗位证据。",
        ),
        _score_dimension(
            "没有切中的点",
            0,
            "；".join(missed_points) if missed_points else "没有明显跑题，但具体案例和结果证据仍然不足。",
        ),
        _score_dimension(
            "下一版怎么改",
            0,
            "；".join(rewrite_advice),
        ),
    ]
    suggestion = (
        "不要只说理解岗位和愿意参与，要补一个真实或模拟的低空运营场景。"
        "例如：巡检、物流、文旅航线或应急任务中，你如何做合规检查、资源调度、异常处理和事后改进。"
    )
    return {
        "score": total,
        "is_relevant": assessment["relevance"] > 0,
        "strict_reason": "定性反馈分析",
        "dimensions": dimensions,
        "suggestion": suggestion,
        **_qualitative_payload(
            hit_points=hit_points or ["回答有一定信息量，可以继续打磨成更清晰的面试表达。"],
            missed_points=missed_points or ["当前主要问题不是方向错误，而是还可以补更多具体证据。"],
            rewrite_advice=rewrite_advice,
            summary="这版回答不再用分数评价，重点看是否切中题目、证据是否充分、是否能证明岗位匹配。",
        ),
    }


@app.post("/api/interview/answer", response_model=InterviewAnswerResponse)
async def submit_answer(request: InterviewAnswerRequest):
    if request.interview_id not in active_interviews:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = active_interviews[request.interview_id]
    question = interview["questions"][request.question_index]
    
    job_name = JOB_TYPE_NAMES_CN.get(interview.get("job_type", ""), "技术岗位")
    
    prompt = f"""你是一位资深面试官，正在面试「{job_name}」岗位的候选人。

面试问题：{question}
候选人回答：{request.answer}

请从以下维度评估这个回答（注意：这是文字面试，只能评估内容本身，不要评价眼神、语速等无法从文字判断的方面）：

评分维度（每项 0-10 分）：
1. 内容完整性：是否完整回答了问题，有没有遗漏关键点
2. 逻辑清晰度：回答是否有清晰的逻辑结构（如总分总、STAR法则等）
3. 专业深度：是否展现了足够的专业知识和理解深度
4. 表达结构化：语言是否简洁有条理，是否用了具体例子
5. 岗位匹配度：回答是否体现了与{job_name}岗位的匹配

请输出一个 JSON 对象：
{{
  "score": 综合评分(0-10的整数),
  "dimensions": [
    {{"label": "内容完整性", "score": 分数, "comment": "一句话评价"}},
    {{"label": "逻辑清晰度", "score": 分数, "comment": "一句话评价"}},
    {{"label": "专业深度", "score": 分数, "comment": "一句话评价"}},
    {{"label": "表达结构化", "score": 分数, "comment": "一句话评价"}},
    {{"label": "岗位匹配度", "score": 分数, "comment": "一句话评价"}}
  ],
  "suggestion": "综合改进建议，1-2句话"
}}

只输出 JSON，不要输出其他内容。"""

    prompt = f"""你是一位严格但友好的面试教练，正在分析「{job_name}」岗位候选人的文字回答。

面试问题：{question}
候选人回答：{request.answer}

请不要给分，不要输出 0-10 分，不要做抽象等级评价。请只分析：
1. 候选人切中了哪些点
2. 候选人没有切中哪些点
3. 下一版应该怎么改

输出 JSON：
{{
  "hit_points": ["切中的点1", "切中的点2"],
  "missed_points": ["没有切中的点1", "没有切中的点2"],
  "rewrite_advice": ["具体改法1", "具体改法2", "具体改法3"],
  "summary": "一句话总结这版回答的主要问题和改进方向"
}}

只输出 JSON，不要输出其他内容。"""

    prompt = build_interview_prompt(job_name, question, request.answer)
    if os.getenv("INTERVIEW_AI_SCORING", "true").lower() == "true":
        result = call_fast_interview_api(prompt)
        
        if result:
            try:
                data = parse_model_json_response(result)
                hit_points = data.get("hit_points", [])
                missed_points = data.get("missed_points", [])
                rewrite_advice = data.get("rewrite_advice", [])
                sample_rewrite = data.get("sample_rewrite", "")
                summary = data.get("summary", "")
                feedback = {
                    "score": 0,
                    "dimensions": [
                        {"label": "切中点", "score": 0, "comment": "；".join(hit_points) if hit_points else "暂未识别到明确切中点。"},
                        {"label": "未切中点", "score": 0, "comment": "；".join(missed_points) if missed_points else "没有明显跑题，但还需要补充证据。"},
                        {"label": "修改方向", "score": 0, "comment": "；".join(rewrite_advice) if rewrite_advice else "建议补充具体项目、个人动作和结果。"},
                    ],
                    "suggestion": summary,
                    "hit_points": hit_points,
                    "missed_points": missed_points,
                    "rewrite_advice": rewrite_advice,
                    "sample_rewrite": sample_rewrite,
                    "summary": summary,
                }
            except Exception as parse_error:
                logger.warning(f"面试 AI 反馈 JSON 解析失败，使用规则兜底: {parse_error}")
                feedback = generate_rule_based_interview_feedback(question, request.answer, interview.get("job_type", "ai"))
        else:
            feedback = generate_rule_based_interview_feedback(question, request.answer, interview.get("job_type", "ai"))
    else:
        feedback = generate_rule_based_interview_feedback(question, request.answer, interview.get("job_type", "ai"))
    
    interview["answers"].append(request.answer)
    interview["scores"].append(feedback["score"])
    interview["feedbacks"].append(feedback)

    next_question = None
    if len(interview["answers"]) < 5:
        next_question = generate_interview_follow_up(
            interview.get("job_type", "ai"),
            question,
            request.answer,
            len(interview["answers"]) + 1,
            interview
        )
        interview["questions"].append(next_question)
    
    return InterviewAnswerResponse(score=feedback["score"], feedback=feedback, next_question=next_question)

def generate_mock_feedback():
    """
    生成 mock 反馈（DeepSeek 不可用时的降级方案）。
    
    使用基于内容质量的真实维度，而非虚假的微表情分析。
    """
    import random
    base_score = random.randint(5, 8)
    
    # 五维度评分，模拟真实评估
    dims = [
        {"label": "内容完整性", "score": random.randint(5, 9), "comment": "基本覆盖了问题的核心要点" if random.random() > 0.3 else "可以补充更多关键细节"},
        {"label": "逻辑清晰度", "score": random.randint(5, 9), "comment": "逻辑结构较清晰" if random.random() > 0.3 else "可以用STAR法则让结构更清晰"},
        {"label": "专业深度", "score": random.randint(4, 8), "comment": "展现了基础专业素养" if random.random() > 0.3 else "可以深入展开技术细节"},
        {"label": "表达结构化", "score": random.randint(5, 9), "comment": "表达较有条理" if random.random() > 0.3 else "建议多用具体案例支撑观点"},
        {"label": "岗位匹配度", "score": random.randint(4, 8), "comment": "能看出与岗位的基本匹配" if random.random() > 0.3 else "可以更好地展示与岗位的契合点"},
    ]
    
    suggestions = [
        "回答整体不错，建议在专业深度和具体案例上进一步加强。",
        "结构比较清晰，可以尝试用STAR法则组织回答，让面试官更容易抓住重点。",
        "基础内容覆盖了，建议补充更多行业理解和项目经验来增强竞争力。",
        "表达通顺，但可以在专业术语和深度上多下功夫，体现专业素养。",
        "思路清楚，建议将抽象观点落地到具体场景和案例中，更有说服力。",
        "回答有一定质量，可以从岗位需求出发更有针对性地展示自己的能力。"
    ]
    
    return {
        "score": base_score,
        "dimensions": dims,
        "suggestion": suggestions[random.randint(0, len(suggestions)-1)]
    }

def build_interview_advice(interview: dict, avg_score: float) -> str:
    """生成可执行的面试修改建议，避免只给空泛评价。"""
    job_type = interview.get("job_type", "ai")
    job_names = {
        "robot": "机器人工程师",
        "ai": "AI算法工程师",
        "lowAltitude": "低空经济运营",
        "material": "新材料研发",
        "pm": "产品经理",
    }
    job_focus = {
        "robot": "真实设备调试、传感器/控制链路、稳定性与安全边界",
        "ai": "数据闭环、评测指标、模型迭代、工程部署和业务效果验证",
        "lowAltitude": "场景运营、合规安全、航线/资源调度和异常预案",
        "material": "实验设计、表征验证、数据复现和放大应用风险",
        "pm": "用户问题、指标拆解、方案取舍、上线验证和跨团队推动",
    }
    feedbacks = interview.get("feedbacks", [])
    scores = interview.get("scores", [])
    answers = interview.get("answers", [])
    questions = interview.get("questions", [])

    dimension_totals = {}
    dimension_counts = {}
    for feedback in feedbacks:
        for dim in feedback.get("dimensions", []):
            label = dim.get("label", "能力维度")
            dimension_totals[label] = dimension_totals.get(label, 0) + float(dim.get("score", 0) or 0)
            dimension_counts[label] = dimension_counts.get(label, 0) + 1

    weak_dimensions = sorted(
        ((label, dimension_totals[label] / dimension_counts[label]) for label in dimension_totals),
        key=lambda item: item[1]
    )[:2]
    weak_text = "、".join([f"{label}（均分{score:.1f}）" for label, score in weak_dimensions]) or "结构化表达、案例支撑"
    dimension_avgs = {
        label: dimension_totals[label] / dimension_counts[label]
        for label in dimension_totals
    }

    weakest_index = min(range(len(scores)), key=lambda i: scores[i]) if scores else 0
    weak_question = questions[weakest_index] if weakest_index < len(questions) else "得分最低的一题"
    weak_answer = answers[weakest_index] if weakest_index < len(answers) else ""
    answer_hint = "先补充一个真实项目案例" if len(weak_answer) < 80 else "把已有案例压缩成更清楚的业务链路"

    if avg_score >= 8:
        summary = "整体表现优秀，已经能体现岗位相关能力；下一步重点是把亮点讲得更有证据、更像真实业务判断。"
    elif avg_score >= 6:
        summary = "整体表现良好，但答案还需要从“能回答”升级到“能证明你胜任这个岗位”。"
    else:
        summary = "当前回答偏概括，需要先把项目经历、岗位能力和量化结果补齐，再追求表达流畅。"

    def risk_level(score: float) -> str:
        if score >= 7.5:
            return "低"
        if score >= 5.5:
            return "中"
        return "高"

    dimension_metaphors = {
        "硬性能力": "像能跑通链路的执行者，但还要证明能看见业务瓶颈。",
        "细节与迭代能力": "像有经验的项目参与者，关键是把问题定位和改法讲到动作级。",
        "公司认知与求职动机": "像主动型候选人，但要继续补公司业务和岗位匹配证据。",
        "成长与自知之明": "像可培养的新人，成熟度取决于能否主动补课和反馈问题。",
        "离职动机与价值观": "像需要继续观察稳定性的候选人，表达要客观、少情绪。",
        "情商与压力管理": "像能协作的人，但压力场景下要展示共情、边界和解决方案。",
    }
    report_lines = []
    for label in ["硬性能力", "细节与迭代能力", "公司认知与求职动机", "成长与自知之明", "离职动机与价值观", "情商与压力管理"]:
        score = dimension_avgs.get(label, avg_score)
        report_lines.append(
            f"{label}：{score:.1f}/10，风险{risk_level(score)}。证据：结合本轮回答中对应维度的表现评估；形象比喻：{dimension_metaphors[label]}"
        )
    recommendation = "强烈建议录用" if avg_score >= 8 else "建议进入下一轮/补充考察" if avg_score >= 6 else "暂不建议录用，建议继续训练后再面试"

    return "\n".join([
        f"总结：{summary}",
        "六维评估：" + " | ".join(report_lines),
        f"综合推荐度与录用建议：{avg_score:.1f}/10，{recommendation}。核心判断来自价值感、信任感、匹配度三项乘积，而不是单看某一道题得分。",
        f"建议1：围绕{job_names.get(job_type, '目标岗位')}的真实考察点重构答案，重点补上{job_focus.get(job_type, job_focus['ai'])}。每个答案至少包含“业务背景/任务目标/你的动作/量化结果/下一步改法”五个信息块。",
        f"建议2：优先补强{weak_text}。具体改法：回答前先给一句结论，再用STAR展开；每个观点后面必须接一个项目证据，例如指标提升、成本下降、时延变化、准确率变化、用户反馈或上线结果。",
        f"建议3：针对低分题「{weak_question}」，建议你{answer_hint}：先说明问题为什么重要，再说你负责了哪一环，最后用2-3个数字证明结果。不要只说“做了优化”，要说“优化前是什么、怎么改、优化后验证了什么”。",
        "建议4：准备一版可直接背诵的60秒项目介绍模板：我做的是____场景，目标是____；我负责____；关键难点是____；我用了____方法；最终____指标从____变到____；如果重做一次我会____。",
        "建议5：下一次练习时，把每道题回答控制在90-120秒。答完后自查三件事：有没有具体项目名、有没有量化指标、有没有说明和岗位需求的关系。缺一项就补一轮。"
    ])

def build_interview_advice(interview: dict, avg_score: float) -> str:
    """Build a qualitative interview review without exposing scores to candidates."""
    job_type = interview.get("job_type", "ai")
    job_names = {
        "robot": "机器人工程师",
        "ai": "AI算法工程师",
        "lowAltitude": "低空经济运营",
        "material": "新材料研发",
        "pm": "产品经理",
    }
    feedbacks = interview.get("feedbacks", [])
    hit_points = []
    missed_points = []
    rewrite_advice = []
    for feedback in feedbacks:
        hit_points.extend(feedback.get("hit_points") or [])
        missed_points.extend(feedback.get("missed_points") or [])
        rewrite_advice.extend(feedback.get("rewrite_advice") or [])

    def unique(items):
        result = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result

    hit_points = unique(hit_points)[:4]
    missed_points = unique(missed_points)[:4]
    rewrite_advice = unique(rewrite_advice)[:5]

    return "\n".join([
        f"总结：这轮面试已经围绕{job_names.get(job_type, '目标岗位')}完成分析，下一步重点是把岗位理解、个人经历和可验证结果连接得更紧。",
        "切中的点：" + ("；".join(hit_points) if hit_points else "已经完成了基本回答，可以继续补充更具体的岗位证据。"),
        "没有切中的点：" + ("；".join(missed_points) if missed_points else "没有明显跑题，但还可以补充更具体的项目、数据和修改依据。"),
        "建议1：" + (rewrite_advice[0] if len(rewrite_advice) > 0 else "每道题开头先用一句话直接回答问题。"),
        "建议2：" + (rewrite_advice[1] if len(rewrite_advice) > 1 else "中间补充真实项目或真实经历，说明你负责的动作。"),
        "建议3：" + (rewrite_advice[2] if len(rewrite_advice) > 2 else "结尾把经历扣回岗位要求，说明它证明了哪项能力。"),
    ])


@app.post("/api/interview/complete", response_model=InterviewCompleteResponse)
async def complete_interview(request: InterviewCompleteRequest, current_user: Optional[User] = Depends(get_optional_user)):
    if request.interview_id not in active_interviews:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = active_interviews[request.interview_id]
    total_score = sum(interview["scores"])
    avg_score = total_score / len(interview["questions"])
    
    details = [{
        "question": q,
        "answer": interview["answers"][i] if i < len(interview["answers"]) else "",
        "score": interview["scores"][i] if i < len(interview["scores"]) else 0,
        "feedback": interview.get("feedbacks", [])[i] if i < len(interview.get("feedbacks", [])) else None
    } for i, q in enumerate(interview["questions"])]
    advice = build_interview_advice(interview, avg_score)
    
    # 持久化到数据库（登录用户才保存）
    if current_user:
        try:
            supabase = get_supabase()
            interview_history_payload = {
                "user_phone": current_user.phone,
                "job_type": interview["job_type"],
                "questions": interview["questions"],
                "answers": interview["answers"],
                "scores": interview["scores"],
                "feedbacks": interview.get("feedbacks", []),
                "total_score": total_score,
                "avg_score": avg_score,
                "advice": advice
            }
            try:
                supabase.table("interview_history").insert(interview_history_payload).execute()
            except Exception as feedbacks_error:
                if "feedbacks" not in str(feedbacks_error):
                    raise
                interview_history_payload.pop("feedbacks", None)
                interview_history_payload["scores"] = [
                    {
                        "score": interview["scores"][index] if index < len(interview["scores"]) else 0,
                        "feedback": interview.get("feedbacks", [])[index] if index < len(interview.get("feedbacks", [])) else None
                    }
                    for index in range(len(interview["questions"]))
                ]
                supabase.table("interview_history").insert(interview_history_payload).execute()
        except Exception as e:
            logger.warning(f"保存面试历史失败: {e}")
    
    del active_interviews[request.interview_id]
    
    return InterviewCompleteResponse(
        total_score=total_score,
        avg_score=avg_score,
        advice=advice,
        details=details
    )

@app.get("/api/interview/history")
async def get_interview_history(current_user: Optional[User] = Depends(get_optional_user)):
    if not current_user:
        return []
    try:
        supabase = get_supabase()
        result = supabase.table("interview_history")\
            .select("id, job_type, total_score, avg_score, created_at")\
            .eq("user_phone", current_user.phone)\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        return result.data
    except Exception as e:
        logger.warning(f"查询面试历史失败: {e}")
        return []

@app.get("/api/interview/{id}")
async def get_interview_by_id(id: str, current_user: User = Depends(get_current_active_user)):
    try:
        supabase = get_supabase()
        try:
            result = supabase.table("interview_history")\
                .select("id, job_type, questions, answers, scores, feedbacks, total_score, avg_score, advice, created_at")\
                .eq("id", id)\
                .eq("user_phone", current_user.phone)\
                .limit(1)\
                .execute()
        except Exception as feedbacks_error:
            if "feedbacks" not in str(feedbacks_error):
                raise
            result = supabase.table("interview_history")\
                .select("id, job_type, questions, answers, scores, total_score, avg_score, advice, created_at")\
                .eq("id", id)\
                .eq("user_phone", current_user.phone)\
                .limit(1)\
                .execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Interview history not found")

        item = result.data[0]
        questions = item.get("questions") or []
        answers = item.get("answers") or []
        scores = item.get("scores") or []
        feedbacks = item.get("feedbacks") or []
        packed_score_feedbacks = scores if isinstance(scores, list) else []
        item["details"] = [{
            "question": question,
            "answer": answers[index] if index < len(answers) else "",
            "score": (
                packed_score_feedbacks[index].get("score", 0)
                if index < len(packed_score_feedbacks) and isinstance(packed_score_feedbacks[index], dict)
                else scores[index] if index < len(scores) else 0
            ),
            "feedback": (
                feedbacks[index] if index < len(feedbacks)
                else packed_score_feedbacks[index].get("feedback")
                if index < len(packed_score_feedbacks) and isinstance(packed_score_feedbacks[index], dict)
                else None
            )
        } for index, question in enumerate(questions)]
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"查询面试历史详情失败: {e}")
        raise HTTPException(status_code=500, detail="查询面试历史详情失败")

@app.get("/api/jobs", response_model=List[Job])
async def get_jobs(category: str = "all", education: str = "all"):
    """
    获取岗位列表
    
    从 Supabase 数据库查询岗位数据，支持按分类筛选
    """
    jobs = JobService.get_jobs(category=category, education=education)
    return jobs

@app.get("/api/jobs/{id}", response_model=Job)
async def get_job_by_id(id: int):
    """
    获取单个岗位详情
    
    从 Supabase 数据库查询指定 ID 的岗位
    """
    job = JobService.get_job_by_id(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

TIPS_DATA = [
    # 📋 面试场景攻略
    "🔰 面试开场：「请做个自我介绍」→ 用「我是谁 + 我为什么适合 + 我为什么想来」三段式，60秒搞定，别背简历。",
    "💬 遇到不会的问题：别硬编！先说「这个问题我目前经验有限」，然后展示你的学习思路——面试官更看重思考过程。",
    "🎯 面试官问「你有什么缺点」：选一个真实但可改进的，比如「公开演讲时容易语速过快，最近在刻意练习控制节奏」。",
    "📊 被问期望薪资：先反问「这个岗位的薪资范围是多少」，或用行业平均数据做锚点，报一个区间而非固定数字。",
    "🔍 技术面遇到陌生概念：坦诚说没接触过，但马上关联你熟悉的类似技术，展示迁移学习能力。",
    "🗣️ 群面/无领导小组：别急着抢话。前3分钟先观察，第4分钟提出一个整合大家观点的框架，你就是自然leader。",

    # 🧠 面试心态与放松
    "😌 面试前紧张？试试「4-7-8呼吸法」：吸气4秒 → 屏息7秒 → 缓慢呼气8秒，重复3次，心率会明显下降。",
    "💪 面试前5分钟：不要疯狂复习，站起来走走、做几个拉伸。身体放松了，大脑才清晰。",
    "🪞 「超人姿势」：面试前对着镜子站直、双手叉腰、抬头挺胸30秒，身体语言会反向影响你的自信水平。",
    "🎮 把面试当成一场游戏副本：你是主角，面试官是NPC，你的目标是解锁对话选项、收集情报，不是接受审判。",
    "⚡ 面试中突然大脑空白？停下来喝口水，说「让我想一想」，3秒的停顿在听者感受里其实很短，但能让你重新组织语言。",

    # 💡 简历与投递技巧
    "📄 简历不是经历清单，是「能力证据链」：每个经历用 STAR 法则 → 情境 → 任务 → 行动 → 结果，结果用数字说话。",
    "🎯 投递前做一件小事：把JD里的3-5个核心关键词，自然地嵌入你的简历。关键词匹配度是AI筛选的第一关。",
    "📬 投递时间有讲究：周二到周四上午9-11点投递，HR打开率最高。周末投的简历容易沉到收件箱底部。",
    "📧 面试后24小时内发一封简短感谢信：不是客套，而是补充面试中没机会说的一个亮点，这是最后的加分机会。",
]

@app.get("/api/tips/today", response_model=TipResponse)
async def get_today_tip():
    day_of_month = datetime.now().day
    tip = TIPS_DATA[day_of_month % len(TIPS_DATA)]
    return TipResponse(content=tip)

@app.get("/api/tips", response_model=TipsResponse)
async def get_tips():
    return TipsResponse(tips=TIPS_DATA)

@app.get("/api/stats/mine", response_model=StatsResponse)
async def get_my_stats(current_user: Optional[User] = Depends(get_optional_user)):
    """
    获取当前用户的求职统计数据。

    数据来源：Supabase 数据库
    - resume: resume_history 表中该用户的记录数
    - interview: interview_history 表中该用户的记录数
    - browse: 暂时由前端 localStorage 管理（浏览岗位是轻量操作，不需要入库）
    """
    if not current_user:
        return StatsResponse(resume=0, interview=0, browse=0)

    try:
        phone = current_user.phone
        cached = stats_cache.get(phone)
        if cached and time.time() < cached["expires_at"]:
            return StatsResponse(**cached["data"])

        supabase = get_supabase()

        # 查简历分析次数
        resume_result = supabase.table("resume_history") \
            .select("id", count="exact") \
            .eq("user_phone", phone) \
            .execute()
        resume_count = resume_result.count if resume_result.count else 0

        # 查面试次数
        interview_result = supabase.table("interview_history") \
            .select("id", count="exact") \
            .eq("user_phone", phone) \
            .execute()
        interview_count = interview_result.count if interview_result.count else 0

        data = {
            "resume": resume_count,
            "interview": interview_count,
            "browse": 0
        }
        stats_cache[phone] = {
            "data": data,
            "expires_at": time.time() + 30
        }

        return StatsResponse(
            resume=resume_count,
            interview=interview_count,
            browse=0  # 浏览数由前端 localStorage 管理
        )
    except Exception as e:
        logger.warning(f"查询统计数据失败: {e}")
        return StatsResponse(resume=0, interview=0, browse=0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
