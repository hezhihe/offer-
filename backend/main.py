from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
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

# 鍔犺浇鐜鍙橀噺
load_dotenv()

# 瀵煎叆 Supabase 鏈嶅姟
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
        "nickname": "娴嬭瘯鐢ㄦ埛"
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
    readiness_level: Optional[str] = None
    readiness_label: Optional[str] = None
    readiness_reason: Optional[str] = None
    jd_requirements: List[str] = Field(default_factory=list)
    matched_evidence: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    rewrite_templates: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)

class InterviewStartRequest(BaseModel):
    job_type: str
    jd_content: Optional[str] = None
    resume_content: Optional[str] = None
    analysis_result: Optional[Dict] = None
    source: Optional[str] = None

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
    education: str = "涓嶉檺"
    url: str
    status: str = "active"
    isExpired: bool = False
    daysUntilDeadline: Optional[int] = None

class TipResponse(BaseModel):
    content: str

class TipsResponse(BaseModel):
    tips: List[str]

class StatsResponse(BaseModel):
    resume: int
    interview: int
    browse: int

stats_cache: Dict[str, Dict] = {}
active_interviews: Dict[str, Dict] = {}

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        # bcrypt 鐗堟湰鍏煎锛氬鏋?verify 澶辫触锛屽皾璇曢噸鏂?hash 鍚庢瘮杈?
        import hashlib
        safe_pwd = hashlib.sha256(plain_password.encode()).hexdigest()[:72]
        try:
            return pwd_context.verify(safe_pwd, hashed_password)
        except (ValueError, TypeError):
            return False

def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except (ValueError, TypeError):
        import hashlib
        safe_pwd = hashlib.sha256(password.encode()).hexdigest()[:72]
        return pwd_context.hash(safe_pwd)

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
    """鑾峰彇褰撳墠鐢ㄦ埛锛屾湭鐧诲綍杩斿洖 None 鑰屼笉鏄姏鍑?401"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]  # 鍘绘帀 "Bearer "
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
    """Upload base64 avatar."""
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
        logger.error(f"澶村儚涓婁紶澶辫触: {e}")
        raise HTTPException(status_code=500, detail="澶村儚涓婁紶澶辫触")

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

def _read_model_provider_config(prefix: str) -> Optional[Dict]:
    api_key = os.getenv(f"{prefix}_API_KEY")
    api_url = os.getenv(f"{prefix}_API_URL")
    model = os.getenv(f"{prefix}_MODEL")
    if not api_key or not api_url or not model:
        return None
    return {
        "name": os.getenv(f"{prefix}_NAME", prefix.lower()),
        "api_key": api_key,
        "api_url": api_url,
        "model": model,
        "timeout": int(os.getenv(f"{prefix}_TIMEOUT", "20")),
        "temperature": float(os.getenv(f"{prefix}_TEMPERATURE", "0.35")),
        "max_tokens": int(os.getenv(f"{prefix}_MAX_TOKENS", "1800")),
    }


def _build_model_payload(config: Dict, prompt: str) -> Dict:
    return {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": "你是严谨的中文求职产品 AI 助手，必须按要求输出结构化结果。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.get("temperature", 0.35),
        "max_tokens": config.get("max_tokens", 1800),
    }


def _extract_model_text(config: Dict, data: Dict) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
        return content.strip() if isinstance(content, str) else ""
    except Exception:
        return ""


def _default_model_configs(purpose: str) -> List[Dict]:
    configs: List[Dict] = []
    primary_key = os.getenv("DEEPSEEK_API_KEY")
    primary_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    fallback_key = os.getenv("DEEPSEEK_FLASH_KEY")
    fallback_url = os.getenv("DEEPSEEK_FLASH_URL")

    if primary_key and primary_key != "your-deepseek-api-key":
        configs.append({
            "name": "deepseek official",
            "api_key": primary_key,
            "api_url": primary_url,
            "model": os.getenv(f"DEEPSEEK_{purpose}_MODEL", os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")),
            "timeout": 20,
            "temperature": 0.35,
            "max_tokens": 1800 if purpose == "RESUME" else 1000,
        })

    if fallback_key and fallback_url:
        configs.append({
            "name": "siliconflow fallback",
            "api_key": fallback_key,
            "api_url": fallback_url,
            "model": os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-ai/DeepSeek-V3"),
            "timeout": 12,
            "temperature": 0.35,
            "max_tokens": 1800 if purpose == "RESUME" else 1000,
        })
    return configs


def call_model_api(prompt: str, purpose: str = "RESUME") -> Optional[str]:
    prefixes = [f"{purpose}_MODEL_PRIMARY", f"{purpose}_MODEL_FALLBACK"]
    configs = [config for config in (_read_model_provider_config(prefix) for prefix in prefixes) if config]
    if not configs:
        configs = _default_model_configs(purpose)

    for config in configs:
        try:
            response = requests.post(
                config["api_url"],
                headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
                json=_build_model_payload(config, prompt),
                timeout=config["timeout"],
            )
            response.raise_for_status()
            text = _extract_model_text(config, response.json())
            if text:
                logger.info("%s model success: %s / %s", purpose, config["name"], config["model"])
                return text
            logger.warning("%s model returned empty text: %s / %s", purpose, config["name"], config["model"])
        except Exception as e:
            logger.warning("%s model failed: %s / %s: %s", purpose, config["name"], config["model"], e)
    return None


def call_deepseek_api(prompt: str) -> Optional[str]:
    return call_model_api(prompt, "RESUME")


def call_fast_interview_api(prompt: str) -> Optional[str]:
    return call_model_api(prompt, "INTERVIEW")

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


def _is_garbled_text(value) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    question_count = text.count("?")
    if question_count >= 3 and question_count / max(len(text), 1) > 0.25:
        return True
    mojibake_markers = ["\u9286", "\u951b", "\u20ac", "\u9470", "\u7eef", "\u934b", "\u6155", "\u6d63", "\u6d93", "\ufffd"]
    return sum(marker in text for marker in mojibake_markers) >= 2


def _clean_resume_text(value) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("\\n", "\n").replace("\\t", " ")
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"【\s*(场景|动作|方法|工具|问题|结果|项目/实习场景|你的具体动作|可验证结果)\s*】", "", text)
    text = re.sub(r"\[(场景|动作|方法|工具|问题|结果|your .*?|xxx|XXX)\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^\s*(?:[-*•]+|\d+[.、])\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(" \n；;，,")


def _is_low_value_resume_advice(text: str) -> bool:
    compact = str(text or "").strip()
    if not compact:
        return True
    low_value = ["补充量化结果", "贴合 JD", "突出个人优势", "优化表达", "增强匹配度"]
    return any(compact == item for item in low_value)


def _clean_text_list(items: Optional[List[str]]) -> List[str]:
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        text = _clean_resume_text(item)
        if text and not _is_garbled_text(text) and not _is_low_value_resume_advice(text):
            result.append(text)
    return result


def build_resume_insight_sections(jd_content: str, experience: str, keywords: List[Dict[str, str]]) -> Dict:
    jd = jd_content or ""
    resume = experience or ""
    priority_terms = [
        ("法语能力", ["法语", "法国", "法语区", "翻译", "外语"]),
        ("跨境电商理解", ["跨境电商", "品牌出海", "欧洲市场", "商品", "电商"]),
        ("内容运营与文案", ["内容运营", "文案", "标题", "简介", "社交媒体", "选题", "营销文案"]),
        ("用户反馈整理", ["用户反馈", "评价", "反馈", "竞品", "市场"]),
        ("数据表格维护", ["数据", "表格", "Excel", "发布记录", "信息表"]),
        ("办公与工具能力", ["Word", "Excel", "PPT", "Canva", "剪映", "AI工具"]),
    ]
    detected = []
    for label, terms in priority_terms:
        if any(term.lower() in jd.lower() for term in terms):
            detected.append((label, terms))
    if not detected:
        for item in keywords[:5]:
            word = str(item.get("word", "")).strip()
            if word:
                detected.append((word, [word]))

    jd_requirements = []
    matched_evidence = []
    missing_requirements = []
    for label, terms in detected[:6]:
        jd_requirements.append(f"{label}：JD 明确需要候选人能围绕这一能力完成岗位任务。")
        matched_terms = [term for term in terms if term.lower() in resume.lower()]
        if matched_terms:
            matched_evidence.append(f"{label}：简历中已经出现 {', '.join(matched_terms[:3])}，可以作为匹配证据，但需要写到具体经历里。")
        else:
            missing_requirements.append(f"{label}：当前简历没有看到直接证据，容易让招聘方判断你只是感兴趣但没有准备。")

    if not jd_requirements:
        jd_requirements = ["岗位核心能力：需要先从 JD 中提取更明确的任务、工具、业务对象和交付结果。"]
    if not matched_evidence:
        matched_evidence = ["已有证据：当前简历有基础经历，但还没有把经历和这个 JD 的核心任务直接连接起来。"]
    if not missing_requirements:
        missing_requirements = ["证据表达：已有经历需要补充任务背景、个人动作和交付结果，否则匹配证据不够硬。"]

    rewrite_templates = []
    if "法语" in jd:
        rewrite_templates.append("建议修改外语/课程经历：因为 JD 需要法语资料理解和初步翻译，可写成：在法语课程/练习中完成法语文本阅读、摘要整理和中文转述，能够支持商品资料、用户反馈等基础内容的理解与归纳。")
    if "内容" in jd or "文案" in jd:
        rewrite_templates.append("建议修改校园活动或社团宣传经历：因为 JD 需要内容运营和文案整理，可写成：负责活动通知、推文或宣传文案的信息整理与发布，按主题提炼卖点/亮点，并根据反馈调整表达。")
    if "数据" in jd or "表格" in jd or "Excel" in jd:
        rewrite_templates.append("建议修改学习/活动记录经历：因为 JD 需要维护商品信息表和反馈表，可写成：使用 Excel/表格整理参与名单、资料清单或反馈记录，保证字段完整、分类清晰、便于后续追踪。")
    if not rewrite_templates:
        rewrite_templates.append("建议修改最相关的一段经历：先写岗位需要的能力，再写你做过的相近任务，句式为：为完成某任务，我负责整理/沟通/输出某材料，最终形成可交付文件或反馈记录。")

    next_actions = [
        "先修改：把最相关的课程、社团、活动或语言经历改成 JD 能看懂的岗位证据。",
        "再分析：修改后重新上传当前版本，检查匹配度和能力缺口是否收敛。",
        "后准备：当投递准备度达到建议投递后，再进入模拟面试练岗位表达。",
    ]
    return {
        "jd_requirements": jd_requirements[:6],
        "matched_evidence": matched_evidence[:5],
        "missing_requirements": missing_requirements[:5],
        "rewrite_templates": rewrite_templates[:5],
        "next_actions": next_actions,
    }


def build_resume_readiness(
    match_score: int,
    keywords: List[Dict[str, str]],
    suggestions: Optional[List[str]] = None,
    jd_content: str = "",
    experience: str = ""
) -> Dict:
    """Build application-readiness signals from the resume analysis result."""
    suggestions = _clean_text_list(suggestions)
    unmatched = [
        str(item.get("word", "")).strip()
        for item in keywords
        if item.get("match") is False or item.get("match") == "false"
    ]
    unmatched = [item for item in unmatched if item and not _is_garbled_text(item)][:5]

    if match_score >= 80 and len(unmatched) <= 1:
        level = "ready"
        label = "\u5efa\u8bae\u6295\u9012"
        reason = "\u5f53\u524d\u7b80\u5386\u4e0e JD \u7684\u6838\u5fc3\u8981\u6c42\u5339\u914d\u5ea6\u8f83\u9ad8\uff0c\u4f46\u6295\u9012\u524d\u4ecd\u5efa\u8bae\u6838\u5bf9\u5c97\u4f4d\u5173\u952e\u8bcd\u548c\u91cf\u5316\u7ed3\u679c\u3002"
    elif match_score >= 60:
        level = "revise_first"
        label = "\u5efa\u8bae\u4fee\u6539\u540e\u6295\u9012"
        reason = "\u5f53\u524d\u7b80\u5386\u6709\u4e00\u5b9a\u5339\u914d\u57fa\u7840\uff0c\u4f46\u5173\u952e\u8bc1\u636e\u3001\u5c97\u4f4d\u5173\u952e\u8bcd\u6216\u91cf\u5316\u7ed3\u679c\u8fd8\u4e0d\u591f\u6e05\u695a\uff0c\u5efa\u8bae\u5148\u6539\u518d\u6295\u3002"
    else:
        level = "not_ready"
        label = "\u4e0d\u5efa\u8bae\u76f4\u63a5\u6295\u9012"
        reason = "\u5f53\u524d\u7b80\u5386\u4e0e JD \u7684\u6838\u5fc3\u8981\u6c42\u5dee\u8ddd\u8f83\u660e\u663e\uff0c\u76f4\u63a5\u6295\u9012\u5bb9\u6613\u88ab\u7b5b\u6389\uff0c\u5efa\u8bae\u5148\u8865\u9f50\u5c97\u4f4d\u76f8\u5173\u8bc1\u636e\u3002"

    sections = build_resume_insight_sections(jd_content, experience, keywords)
    missing_requirements = sections["missing_requirements"] or unmatched or suggestions[:3] or ["需要补充更明确的 JD 核心要求匹配证据"]
    rewrite_templates = sections["rewrite_templates"]

    return {
        "readiness_level": level,
        "readiness_label": label,
        "readiness_reason": reason,
        "jd_requirements": sections["jd_requirements"],
        "matched_evidence": sections["matched_evidence"],
        "missing_requirements": missing_requirements[:5],
        "rewrite_templates": rewrite_templates[:5],
        "next_actions": sections["next_actions"],
    }


def normalize_resume_analysis_payload(data: Dict, fallback: Dict) -> Dict:
    """Remove garbled model fields and fill stable Chinese defaults."""
    payload = dict(data or {})
    allowed_levels = {"ready", "revise_first", "not_ready"}
    allowed_labels = {"\u5efa\u8bae\u6295\u9012", "\u5efa\u8bae\u4fee\u6539\u540e\u6295\u9012", "\u4e0d\u5efa\u8bae\u76f4\u63a5\u6295\u9012"}
    if payload.get("readiness_level") not in allowed_levels:
        payload.pop("readiness_level", None)
    if payload.get("readiness_label") not in allowed_labels:
        payload.pop("readiness_label", None)
    for key in ["readiness_reason", "refactored_resume"]:
        if _is_garbled_text(payload.get(key)):
            payload.pop(key, None)
    payload["suggestions"] = _clean_text_list(payload.get("suggestions"))
    payload["jd_requirements"] = _clean_text_list(payload.get("jd_requirements"))
    payload["matched_evidence"] = _clean_text_list(payload.get("matched_evidence"))
    payload["rewrite_templates"] = _clean_text_list(payload.get("rewrite_templates"))
    payload["missing_requirements"] = _clean_text_list(payload.get("missing_requirements"))
    payload["next_actions"] = _clean_text_list(payload.get("next_actions"))
    for key, value in fallback.items():
        if not payload.get(key):
            payload[key] = value
    return payload


@app.post("/api/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(request: ResumeAnalysisRequest, current_user: Optional[User] = Depends(get_optional_user)):

    prompt = build_resume_prompt(request.jd_content, request.experience)
    result = call_deepseek_api(prompt)
    used_ai = False
    readiness_data = {}
    
    if result:
        try:
            # 灏濊瘯鎻愬彇 JSON
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                match_score = data.get("match_score", 70)
                keywords = data.get("keywords", [])
                refactored_resume = data.get("refactored_resume", "")
                suggestions = data.get("suggestions", [])
                readiness_data = {
                    "readiness_level": data.get("readiness_level"),
                    "readiness_label": data.get("readiness_label"),
                    "readiness_reason": data.get("readiness_reason"),
                    "jd_requirements": data.get("jd_requirements", []),
                    "matched_evidence": data.get("matched_evidence", []),
                    "missing_requirements": data.get("missing_requirements", []),
                    "rewrite_templates": data.get("rewrite_templates", []),
                    "next_actions": data.get("next_actions", []),
                }
                used_ai = True
        except Exception as e:
            logger.warning(f"瑙ｆ瀽 AI 绠€鍘嗗垎鏋愮粨鏋滃け璐? {e}")
    
    if not used_ai:
        # 闄嶇骇锛氬熀浜庤緭鍏ュ唴瀹圭敓鎴?mock 鏁版嵁锛堣€岄潪纭紪鐮佹満鍣ㄤ汉鐩稿叧鍐呭锛?
        match_score, keywords, refactored_resume, suggestions = generate_mock_resume_analysis(
            request.jd_content, request.experience
        )
    
    # Clean model/fallback text before rendering to frontend.
    suggestions = _clean_text_list(suggestions)
    refactored_resume = _clean_resume_text(refactored_resume)
    if _is_garbled_text(refactored_resume) or not refactored_resume:
        refactored_resume = "局部改写示例：请优先选择最接近 JD 的课程、社团、活动或语言经历，改成‘任务背景 + 个人动作 + 交付结果’的表达。"

    if suggestions:
        suggestion_text = "\\n\\n\u3010\u4f18\u5316\u5efa\u8bae\u3011\\n" + "\\n".join(f"{i+1}. {item}" for i, item in enumerate(suggestions))
        refactored_resume += suggestion_text
    
    computed_readiness = build_resume_readiness(match_score, keywords, suggestions, request.jd_content, request.experience)
    model_payload = {
        "readiness_level": readiness_data.get("readiness_level"),
        "readiness_label": readiness_data.get("readiness_label"),
        "readiness_reason": readiness_data.get("readiness_reason"),
        "jd_requirements": readiness_data.get("jd_requirements", []),
        "matched_evidence": readiness_data.get("matched_evidence", []),
        "missing_requirements": readiness_data.get("missing_requirements", []),
        "rewrite_templates": readiness_data.get("rewrite_templates", []),
        "next_actions": readiness_data.get("next_actions", []),
        "refactored_resume": refactored_resume,
        "suggestions": suggestions,
    }
    normalized_payload = normalize_resume_analysis_payload(model_payload, computed_readiness)
    refactored_resume = normalized_payload.get("refactored_resume") or refactored_resume
    suggestions = normalized_payload.get("suggestions", suggestions)
    readiness_data = {
        "readiness_level": normalized_payload.get("readiness_level"),
        "readiness_label": normalized_payload.get("readiness_label"),
        "readiness_reason": normalized_payload.get("readiness_reason"),
        "jd_requirements": normalized_payload.get("jd_requirements", []),
        "matched_evidence": normalized_payload.get("matched_evidence", []),
        "missing_requirements": normalized_payload.get("missing_requirements", []),
        "rewrite_templates": normalized_payload.get("rewrite_templates", []),
        "next_actions": normalized_payload.get("next_actions", []),
    }

    response = ResumeAnalysisResponse(
        match_score=match_score,
        keywords=keywords,
        refactored_resume=refactored_resume,
        **readiness_data
    )
    
    # 鎸佷箙鍖栧埌鏁版嵁搴擄紙鐧诲綍鐢ㄦ埛鎵嶄繚瀛橈級
    if current_user:
        try:
            supabase = get_supabase()
            job_title = request.jd_content.split('\n')[0].strip()[:50]
            history_payload = {
                "user_phone": current_user.phone,
                "job_title": job_title,
                "company": "",
                "original_jd": request.jd_content,
                "original_resume": request.experience,
                "match_score": match_score,
                "keywords": keywords,
                "reconstructed_resume": refactored_resume,
            }
            analysis_detail = {
                "readiness_level": readiness_data.get("readiness_level"),
                "readiness_label": readiness_data.get("readiness_label"),
                "readiness_reason": readiness_data.get("readiness_reason"),
                "jd_requirements": readiness_data.get("jd_requirements", []),
                "matched_evidence": readiness_data.get("matched_evidence", []),
                "missing_requirements": readiness_data.get("missing_requirements", []),
                "rewrite_templates": readiness_data.get("rewrite_templates", []),
                "next_actions": readiness_data.get("next_actions", []),
            }
            try:
                supabase.table("resume_history").insert({
                    **history_payload,
                    "analysis_detail": analysis_detail,
                }).execute()
            except Exception as detail_error:
                if "analysis_detail" not in str(detail_error):
                    raise
                supabase.table("resume_history").insert(history_payload).execute()
            stats_cache.pop(current_user.phone, None)
        except Exception as e:
            logger.warning(f"淇濆瓨绠€鍘嗗巻鍙插け璐? {e}")
    
    return response


def generate_mock_resume_analysis(jd_content: str, experience: str):
    """Generate a local fallback resume analysis when model calls fail."""
    import random
    import re as re_module

    english_keywords = re_module.findall(r'\b[A-Z][A-Za-z+#]+\b', jd_content)
    chinese_words = re_module.findall(r'[\u4e00-\u9fa5]{2,6}', jd_content)
    stop_words = {"岗位职责", "任职要求", "优先", "相关", "能力", "负责", "参与", "熟悉", "了解"}
    candidates = []
    for word in english_keywords + chinese_words:
        if word and word not in stop_words and word not in candidates:
            candidates.append(word)

    keywords = []
    for kw in candidates[:6]:
        matched = kw.lower() in experience.lower() or kw in experience
        keywords.append({
            "word": kw,
            "match": "true" if matched else "false",
            "reason": f"简历中{'已体现' if matched else '未明显体现'} {kw} 相关经历"
        })

    if len(keywords) < 3:
        keywords.extend([
            {"word": "项目经验", "match": "true", "reason": "简历包含项目或实践经历"},
            {"word": "岗位关键词", "match": "false", "reason": "需要进一步贴合 JD 表达"},
            {"word": "量化成果", "match": "false", "reason": "建议补充可验证结果或指标"},
        ][:3 - len(keywords)])

    matched_count = sum(1 for item in keywords if item["match"] == "true")
    match_score = min(92, max(45, 48 + matched_count * 9 + random.randint(-3, 6)))

    first_line = next((line.strip() for line in experience.splitlines() if line.strip()), "你的核心经历")
    refactored_resume = "【局部改写示例】\n"
    refactored_resume += f"原经历可围绕“{first_line[:40]}”重写为：\n"
    refactored_resume += "为了解决【目标岗位中的具体问题】，我在【项目/实习场景】中负责【你的具体动作】，使用【工具/方法】完成【交付物】，最终带来【可验证结果】。\n"

    suggestions = [
        "优先把 JD 中最核心的 3 个关键词自然嵌入项目经历。",
        "把“负责/参与”改成具体动作，说明你本人做了什么。",
        "补充量化结果；没有精确数据时，写清交付物、使用人数、迭代次数或上线结果。",
    ]

    return match_score, keywords, refactored_resume, suggestions
@app.post("/api/resume/analyze-upload", response_model=ResumeAnalysisResponse)
async def analyze_resume_upload(
    jd_content: str = Form(...),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Analyze a resume from uploaded PDF/Word file or pasted text."""



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
                # 绾枃鏈枃浠?
                experience = content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"鏂囦欢瑙ｆ瀽澶辫触: {e}")
            raise HTTPException(status_code=400, detail=f"鏂囦欢瑙ｆ瀽澶辫触: {str(e)}")
    elif resume_text:
        experience = resume_text.strip()
    
    if not experience or len(experience) < 10:
        raise HTTPException(status_code=400, detail="绠€鍘嗗唴瀹硅繃鐭紝璇蜂笂浼犲畬鏁寸畝鍘嗘垨绮樿创鏇村鍐呭")
    
    # 澶嶇敤鏂囨湰鍒嗘瀽鎺ュ彛
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
        logger.warning(f"鏌ヨ绠€鍘嗗巻鍙插け璐? {e}")
        return []

@app.get("/api/resume/{id}")
async def get_resume_by_id(id: str, current_user: User = Depends(get_current_active_user)):
    try:
        supabase = get_supabase()
        try:
            result = supabase.table("resume_history")                .select("id, job_title, company, original_jd, original_resume, match_score, keywords, reconstructed_resume, analysis_detail, created_at")                .eq("id", id)                .eq("user_phone", current_user.phone)                .limit(1)                .execute()
        except Exception as detail_column_error:
            if "analysis_detail" not in str(detail_column_error):
                raise
            result = supabase.table("resume_history")                .select("id, job_title, company, original_jd, original_resume, match_score, keywords, reconstructed_resume, created_at")                .eq("id", id)                .eq("user_phone", current_user.phone)                .limit(1)                .execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Resume history not found")
        item = result.data[0]
        detail = item.get("analysis_detail") or {}
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except Exception:
                detail = {}
        if isinstance(detail, dict):
            for key in [
                "readiness_level",
                "readiness_label",
                "readiness_reason",
                "jd_requirements",
                "matched_evidence",
                "missing_requirements",
                "rewrite_templates",
                "next_actions",
            ]:
                if key in detail and key not in item:
                    item[key] = detail[key]
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"鏌ヨ绠€鍘嗗巻鍙茶鎯呭け璐? {e}")
        raise HTTPException(status_code=500, detail="Resume history detail query failed")

# 宀椾綅鍚嶇О鏄犲皠锛堢粰 AI 鐢熸垚棰樼洰鐢ㄧ殑涓枃鍚嶏級
JOB_TYPE_NAMES_CN = {
    "robot": "机器人算法",
    "ai": "AI 算法工程师",
    "lowAltitude": "低空经济运营",
    "material": "新材料研发",
    "pm": "AI 产品经理",
}

JOB_TYPE_QUESTIONS_FALLBACK = {
    "robot": [
        "请用一个项目说明你如何定位机器人系统中的算法或调试问题。",
        "如果机器人在现场运行不稳定，你会按什么顺序排查传感器、控制和算法问题？",
        "请解释一个你熟悉的机器人算法，并说明它在真实场景中的限制。",
        "如果要做一个室内服务机器人导航方案，你会先确认哪些关键条件？",
        "你如何看待人形机器人当前落地的主要瓶颈？",
    ],
    "ai": [
        "请解释 Transformer 中 Self-Attention 的核心原理。",
        "讲一个你做过的 AI 项目，从数据、模型到评估完整说明。",
        "模型过拟合时你会优先尝试哪些解决方案？",
        "如果要做一个简历筛选 AI 系统，你会如何定义评估指标？",
        "你怎么看大模型在垂直行业应用中的价值和风险？",
    ],
    "lowAltitude": [
        "如果你加入低空运营团队，前三个月最想先摸清哪三类数据？",
        "低空经济运营需要重点关注哪些政策、空域和安全约束？",
        "如果规划一条城市低空物流航线，你会先评估哪些因素？",
        "你如何判断一个低空经济场景是否值得商业化落地？",
        "你认为低空运营最大的风险是什么，如何提前控制？",
    ],
    "material": [
        "请介绍一种你熟悉的新材料，并说明它的性能、应用和限制。",
        "讲一个材料测试或研发项目，你负责了哪些实验和分析？",
        "如果新材料从实验室走向量产，你会重点验证哪些环节？",
        "你如何评估一种材料是否适合航空航天或新能源场景？",
        "请谈谈你对新材料行业发展趋势的理解。",
    ],
    "pm": [
        "请描述你从 0 到 1 做产品的一次经历，重点说需求分析。",
        "如何判断一个产品需求是否值得做？你的优先级框架是什么？",
        "你如何理解 AI 产品经理和传统产品经理的区别？",
        "讲一次你根据用户反馈推动产品改进的经历。",
        "如果设计一个大学生求职辅助产品，你会如何规划 MVP？",
    ],
}

INTERVIEW_QUESTION_POOLS = {
    key: {
        "warmup": value[:1],
        "foundation": value[1:2],
        "project": value[2:3],
        "scenario": value[3:4],
        "trend": value[4:5],
    }
    for key, value in JOB_TYPE_QUESTIONS_FALLBACK.items()
}

INTERVIEW_CAPABILITY_FOCUS = {
    "robot": "机器人算法、系统调试、现场问题定位和工程落地能力",
    "ai": "机器学习基础、项目闭环、模型评估和业务落地能力",
    "lowAltitude": "政策空域、安全运营、航线规划和商业化判断能力",
    "material": "材料性能、实验验证、量产转化和应用判断能力",
    "pm": "需求判断、用户洞察、AI 产品设计和落地推进能力",
}

INTERVIEW_DYNAMIC_MODULES = {
    "motivation": "岗位动机",
    "business": "业务理解",
    "business_probe": "业务追问",
    "evidence": "项目证据",
    "self_proof": "能力证明",
    "self_proof_probe": "能力追问",
    "growth": "成长复盘",
    "values": "价值观",
    "pressure": "压力测试",
    "salary": "薪资沟通",
}

INTERVIEW_DYNAMIC_QUESTIONS = {
    "motivation": "请结合一个具体经历说明，你为什么适合这个方向？",
    "business": "你认为这个岗位最核心的业务目标是什么？",
}

INTERVIEW_DYNAMIC_FOCUS = {
    "robot": "算法、硬件、控制、调试和现场落地",
    "ai": "数据、模型、评估、部署和业务价值",
    "lowAltitude": "空域政策、安全运营、航线规划、调度和商业化",
    "material": "材料性能、实验验证、工艺放大和应用场景",
    "pm": "用户需求、业务价值、AI 能力边界和产品落地",
}

def build_dynamic_interview_question_set(job_type: str) -> List[str]:
    return JOB_TYPE_QUESTIONS_FALLBACK.get(job_type, JOB_TYPE_QUESTIONS_FALLBACK["ai"])[:1]

def assess_interview_answer_signal(answer: str) -> dict:
    text = answer.strip()
    evidence_markers = ["%", "??", "??", "??", "??", "??", "??", "??", "??", "??", "???", "??", "??", "ROI", "roi"]
    structure_markers = ["??", "??", "??", "??", "??", "??", "??", "??", "??", "??", "STAR", "star"]
    motivation_markers = ["??", "??", "??", "??", "??", "??", "??", "??", "??", "??", "??"]
    risk_markers = ["???", "???", "??", "???", "??", "??", "??", "??", "??", "??", "???"]
    high_signal = sum(marker in text for marker in evidence_markers) + sum(marker in text for marker in structure_markers)
    match_signal = sum(marker in text for marker in motivation_markers)
    risk_signal = sum(marker in text for marker in risk_markers)
    score = 4 + min(3, len(text) // 90) + min(2, high_signal) + min(1, match_signal // 2) - min(3, risk_signal)
    score = max(2, min(10, score))
    level = "weak" if len(text) < 50 or risk_signal >= 2 else ("strong" if score >= 8 else "normal" if score >= 6 else "weak")
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

INTERVIEW_FOLLOW_UP_RUBRICS = {
    "too_short": {"question": "?????????????????????????????????????????"},
    "personal_contribution": {"trigger_terms": ["??", "??", "??", "??"], "missing_terms": ["???", "???", "???", "???", "???", "???"], "question": "?????????????????????????????"},
    "result_validation": {"trigger_terms": ["??", "??", "??", "??", "??", "??"], "missing_terms": ["??", "??", "??", "%", "???", "??", "??", "??", "??"], "question": "??????????????????????????????"},
    "difficulty_process": {"trigger_terms": ["??", "??", "??", "??", "??"], "missing_terms": ["??", "??", "??", "??", "??", "??"], "question": "??????????????????????????????"},
    "job_match": {"trigger_terms": ["??", "??", "???", "??", "??", "??"], "missing_terms": ["??", "??", "??", "??", "??"], "question": "???????????????????????????????"},
    "reflection": {"trigger_terms": ["??", "??", "??", "??", "??"], "missing_terms": ["??", "??", "??", "????", "??"], "question": "????????????????????????????"},
}

def choose_follow_up_gap(answer: str, answer_signal: dict) -> str:
    text = answer.strip()
    for gap, rule in INTERVIEW_FOLLOW_UP_RUBRICS.items():
        if gap == "too_short":
            continue
        if any(term in text for term in rule.get("trigger_terms", [])) and not any(term in text for term in rule.get("missing_terms", [])):
            return gap
    if len(text) < 50 or answer_signal.get("level") == "weak":
        return "too_short"
    if answer_signal.get("high_signal", 0) <= 1:
        return "result_validation"
    return "reflection"

def build_rule_based_follow_up(job_type: str, answer: str, answer_signal: dict, module: str) -> str:
    gap = choose_follow_up_gap(answer, answer_signal)
    return INTERVIEW_FOLLOW_UP_RUBRICS.get(gap, INTERVIEW_FOLLOW_UP_RUBRICS["too_short"])["question"]

def build_dynamic_fallback_question(job_type: str, module: str, previous_question: str, answer: str, next_turn: int, answer_signal: Optional[dict] = None) -> str:
    answer_signal = answer_signal or assess_interview_answer_signal(answer)
    return build_rule_based_follow_up(job_type, answer, answer_signal, module)

def generate_interview_questions(job_type: str) -> List[str]:
    return build_dynamic_interview_question_set(job_type)

def generate_interview_follow_up(job_type: str, previous_question: str, answer: str, next_turn: int, interview: Optional[dict] = None) -> str:
    interview = interview or {"modules": ["motivation"]}
    answer_signal = assess_interview_answer_signal(answer)
    module = choose_next_interview_module(interview, answer_signal, next_turn)
    job_name = JOB_TYPE_NAMES_CN.get(job_type, "????")
    focus = INTERVIEW_DYNAMIC_FOCUS.get(job_type, INTERVIEW_DYNAMIC_FOCUS["ai"])
    fallback = build_dynamic_fallback_question(job_type, module, previous_question, answer, next_turn, answer_signal)
    prompt = f"""??????????????????{job_name}?????
?????{focus}
????{previous_question}
??????{answer}
??????{INTERVIEW_DYNAMIC_MODULES.get(module, module)}
???????{fallback}
????????????????????????????????? JSON???? 100 ??"""
    result = call_fast_interview_api(prompt)
    if result:
        question = result.strip().strip('"').strip()
        if question:
            return question[:180]
    return fallback


def _compact_interview_text(value: str, limit: int, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    text = text.replace("\n", " ").strip()
    for separator in ["?", ";", "?"]:
        if separator in text:
            first = text.split(separator)[0].strip()
            if first:
                text = first
                break
    return text[:limit]

def _detemplate_interview_rewrite(text: str, rubric: Dict, job_type: str = "") -> str:
    """Keep rewrite advice useful without pretending to write the user's final answer."""
    value = str(text or "").strip()
    placeholder_markers = ["XX", "xx", "\u67d0\u9879\u76ee", "\u67d0\u6750\u6599", "\u67d0\u516c\u53f8", "\u3010", "\u3011", "____", "xxx", "XXX"]
    if not value:
        return rubric.get("rewrite", "\u4e0b\u4e00\u7248\u8bf7\u7528\u4f60\u7684\u771f\u5b9e\u7ecf\u5386\u8865\u5145\u5177\u4f53\u573a\u666f\u3001\u4e2a\u4eba\u52a8\u4f5c\u548c\u9a8c\u8bc1\u7ed3\u679c\u3002")
    if any(marker in value for marker in placeholder_markers):
        if job_type == "material":
            return "\u4e0b\u4e00\u7248\u8bf7\u6362\u6210\u4f60\u7684\u771f\u5b9e\u6750\u6599\u5b9e\u9a8c\u6216\u8bfe\u9898\uff0c\u4e0d\u8981\u7167\u6284\u5360\u4f4d\u7b26\uff1b\u91cd\u70b9\u8865\uff1a\u4f60\u6539\u4e86\u54ea\u4e2a\u5de5\u827a\u53c2\u6570\u3001\u63a7\u5236\u4e86\u54ea\u4e9b\u53d8\u91cf\u3001\u7528\u4e86\u4ec0\u4e48\u8868\u5f81/\u6d4b\u8bd5\u65b9\u6cd5\u3001\u6027\u80fd\u6570\u636e\u5982\u4f55\u9a8c\u8bc1\u3001\u662f\u5426\u8003\u8651\u91cf\u4ea7\u7a33\u5b9a\u6027\u3002"
        if job_type == "pm":
            return "\u4e0b\u4e00\u7248\u8bf7\u6362\u6210\u4f60\u7684\u771f\u5b9e\u4ea7\u54c1\u6848\u4f8b\uff0c\u4e0d\u8981\u7167\u6284\u5360\u4f4d\u7b26\uff1b\u91cd\u70b9\u8865\uff1a\u76ee\u6807\u7528\u6237\u662f\u8c01\u3001\u771f\u9700\u6c42\u600e\u4e48\u9a8c\u8bc1\u3001\u65b9\u6848\u505a\u4e86\u4ec0\u4e48\u53d6\u820d\u3001\u4e0a\u7ebf\u540e\u770b\u54ea\u4e2a\u6307\u6807\u3002"
        if job_type == "lowAltitude":
            return "\u4e0b\u4e00\u7248\u8bf7\u6362\u6210\u771f\u5b9e\u6216\u660e\u786e\u7684\u4f4e\u7a7a\u8fd0\u8425\u573a\u666f\uff0c\u4e0d\u8981\u7167\u6284\u5360\u4f4d\u7b26\uff1b\u91cd\u70b9\u8865\uff1a\u822a\u7ebf/\u7a7a\u57df/\u5408\u89c4\u3001\u73b0\u573a\u8c03\u5ea6\u3001\u5f02\u5e38\u9884\u6848\u548c\u8fd0\u8425\u6570\u636e\u3002"
        if job_type == "ai":
            return "\u4e0b\u4e00\u7248\u8bf7\u6362\u6210\u4f60\u7684\u771f\u5b9e AI \u9879\u76ee\uff0c\u4e0d\u8981\u7167\u6284\u5360\u4f4d\u7b26\uff1b\u91cd\u70b9\u8865\uff1a\u6570\u636e\u6765\u6e90\u3001\u6a21\u578b\u65b9\u6848\u3001\u8bc4\u6d4b\u6307\u6807\u3001\u8fed\u4ee3\u52a8\u4f5c\u548c\u4e0a\u7ebf/\u5b9e\u9a8c\u7ed3\u679c\u3002"
        if job_type == "robot":
            return "\u4e0b\u4e00\u7248\u8bf7\u6362\u6210\u4f60\u7684\u771f\u5b9e\u673a\u5668\u4eba\u9879\u76ee\uff0c\u4e0d\u8981\u7167\u6284\u5360\u4f4d\u7b26\uff1b\u91cd\u70b9\u8865\uff1a\u8d1f\u8d23\u6a21\u5757\u3001\u8c03\u8bd5\u95ee\u9898\u3001\u63a7\u5236/\u611f\u77e5\u94fe\u8def\u548c\u7ed3\u679c\u9a8c\u8bc1\u3002"
        return "\u4e0b\u4e00\u7248\u8bf7\u6362\u6210\u4f60\u7684\u771f\u5b9e\u7ecf\u5386\uff0c\u4e0d\u8981\u7167\u6284\u5360\u4f4d\u7b26\uff1b\u91cd\u70b9\u8865\uff1a\u5177\u4f53\u573a\u666f\u3001\u4e2a\u4eba\u52a8\u4f5c\u3001\u5173\u952e\u96be\u70b9\u548c\u9a8c\u8bc1\u7ed3\u679c\u3002"
    return value

JOB_EVALUATION_RUBRICS = {
    "robot": {
        "role_name": "\u673a\u5668\u4eba\u5de5\u7a0b\u5e08",
        "evidence_terms": ["\u673a\u5668\u4eba", "ROS", "ros", "\u4f20\u611f\u5668", "\u63a7\u5236", "\u8c03\u8bd5", "\u786c\u4ef6", "\u7535\u673a", "\u5b9a\u4f4d", "\u5bfc\u822a", "\u8def\u5f84\u89c4\u5212", "\u8fd0\u52a8\u63a7\u5236", "\u5efa\u56fe", "\u6807\u5b9a", "\u5d4c\u5165\u5f0f", "\u96f7\u8fbe", "\u76f8\u673a", "\u8235\u673a", "\u5c0f\u8f66", "\u5faa\u8ff9", "\u907f\u969c", "\u7a33\u5b9a\u6027"],
        "weak_signal_terms": ["\u7528\u6237", "\u6c42\u804c", "\u4ea7\u54c1", "\u5de5\u4f5c\u6d41", "Demo", "demo", "\u7126\u8651", "\u7b80\u5386", "AI\u80fd\u529b"],
        "weak_judgement": "\u7b54\u975e\u6240\u95ee\uff0c\u5c97\u4f4d\u4e0d\u5339\u914d",
        "fix": "\u8865\u673a\u5668\u4eba\u8c03\u8bd5/\u63a7\u5236/\u843d\u5730\u8bc1\u636e",
        "follow_up": "\u8bf7\u7528\u672c\u5c97\u4f4d\u7ecf\u5386\u91cd\u7b54\u3002",
        "rewrite": "\u4e0b\u4e00\u7248\u7528\u673a\u5668\u4eba\u9879\u76ee\u8bf4\u660e\uff1a\u4f60\u8d1f\u8d23\u7684\u6a21\u5757\u3001\u8c03\u8bd5\u95ee\u9898\u3001\u63a7\u5236\u6216\u611f\u77e5\u94fe\u8def\u3001\u7ed3\u679c\u600e\u4e48\u9a8c\u8bc1\u3002",
        "mode": "off_topic",
    },
    "ai": {
        "role_name": "AI\u7b97\u6cd5\u5de5\u7a0b\u5e08",
        "evidence_terms": ["\u6570\u636e", "\u6a21\u578b", "\u8bc4\u6d4b", "\u8bad\u7ec3", "\u63a8\u7406", "\u4e0a\u7ebf", "\u51c6\u786e\u7387", "\u53ec\u56de\u7387", "\u7cbe\u786e\u7387", "\u65f6\u5ef6", "\u6210\u672c", "\u8bef\u5dee", "\u6807\u6ce8", "\u6837\u672c", "\u7279\u5f81", "\u7b97\u6cd5", "RAG", "rag", "Transformer", "\u5411\u91cf", "embedding", "Embedding", "\u5fae\u8c03", "SFT", "\u8bad\u7ec3\u96c6", "\u9a8c\u8bc1\u96c6", "AUC", "F1"],
        "weak_signal_terms": ["\u7528\u6237", "\u6c42\u804c", "\u4ea7\u54c1", "\u5de5\u4f5c\u6d41", "Demo", "demo", "\u7126\u8651", "\u529f\u80fd", "\u8def\u5f84", "AI\u80fd\u529b"],
        "weak_judgement": "\u504f\u4ea7\u54c1\uff0c\u7b97\u6cd5\u8bc1\u636e\u4e0d\u8db3",
        "fix": "\u8865\u6570\u636e\u3001\u6a21\u578b\u8bc4\u6d4b\u6216\u4e0a\u7ebf\u8bc1\u636e",
        "follow_up": "\u4f60\u600e\u4e48\u9a8c\u8bc1\u6a21\u578b\u6548\u679c\uff1f",
        "rewrite": "\u4e0b\u4e00\u7248\u7528\u4e00\u4e2aAI\u9879\u76ee\u8bf4\u660e\uff1a\u6570\u636e\u6765\u6e90\u3001\u6a21\u578b\u65b9\u6848\u3001\u8bc4\u6d4b\u6307\u6807\u3001\u8fed\u4ee3\u52a8\u4f5c\u3001\u4e0a\u7ebf\u6216\u5b9e\u9a8c\u7ed3\u679c\u3002",
        "mode": "weak_match",
    },
    "lowAltitude": {
        "role_name": "\u4f4e\u7a7a\u7ecf\u6d4e\u8fd0\u8425",
        "evidence_terms": ["\u4f4e\u7a7a", "\u822a\u7ebf", "\u98de\u884c", "\u5408\u89c4", "\u7a7a\u57df", "\u6c14\u8c61", "\u8d77\u964d", "\u8c03\u5ea6", "\u8fd0\u8425", "\u5e94\u6025", "\u98ce\u9669", "\u5b89\u5168", "\u8bd5\u8fd0\u8425", "\u51c6\u70b9\u7387", "\u5f02\u5e38", "\u590d\u76d8", "\u7269\u6d41", "\u65e0\u4eba\u673a", "eVTOL"],
        "weak_signal_terms": ["\u7528\u6237", "\u4ea7\u54c1", "\u5de5\u4f5c\u6d41", "Demo", "demo", "AI\u80fd\u529b", "\u7b80\u5386", "\u6c42\u804c"],
        "weak_judgement": "\u504f\u6982\u5ff5\uff0c\u8fd0\u8425\u8bc1\u636e\u4e0d\u8db3",
        "fix": "\u8865\u5408\u89c4/\u822a\u7ebf/\u73b0\u573a\u8c03\u5ea6\u8bc1\u636e",
        "follow_up": "\u73b0\u573a\u5f02\u5e38\u4f60\u600e\u4e48\u5904\u7406\uff1f",
        "rewrite": "\u4e0b\u4e00\u7248\u7528\u4e00\u4e2a\u4f4e\u7a7a\u8fd0\u8425\u573a\u666f\u8bf4\u660e\uff1a\u822a\u7ebf\u3001\u5408\u89c4\u3001\u73b0\u573a\u8c03\u5ea6\u3001\u98ce\u9669\u9884\u6848\u548c\u8fd0\u8425\u6570\u636e\u3002",
        "mode": "weak_match",
    },
    "material": {
        "role_name": "\u65b0\u6750\u6599\u7814\u53d1",
        "evidence_terms": ["\u6750\u6599", "\u5b9e\u9a8c", "\u8868\u5f81", "\u6027\u80fd", "\u53d8\u91cf", "\u914d\u65b9", "\u5de5\u827a", "\u6837\u54c1", "\u6d4b\u8bd5", "\u5bf9\u7167", "\u7a33\u5b9a\u6027", "\u653e\u5927", "\u91cf\u4ea7", "\u6570\u636e", "\u7ed3\u6784", "\u6210\u5206", "\u8c31", "\u5f3a\u5ea6", "\u5bfc\u7535", "\u5faa\u73af"],
        "weak_signal_terms": ["\u7528\u6237", "\u4ea7\u54c1", "\u5de5\u4f5c\u6d41", "Demo", "demo", "AI\u80fd\u529b", "\u6c42\u804c"],
        "weak_judgement": "\u504f\u6982\u5ff5\uff0c\u5b9e\u9a8c\u8bc1\u636e\u4e0d\u8db3",
        "fix": "\u8865\u5b9e\u9a8c\u8bbe\u8ba1/\u8868\u5f81/\u6027\u80fd\u9a8c\u8bc1",
        "follow_up": "\u4f60\u600e\u4e48\u6392\u9664\u5047\u63d0\u5347\uff1f",
        "rewrite": "\u4e0b\u4e00\u7248\u7528\u4e00\u4e2a\u6750\u6599\u5b9e\u9a8c\u8bf4\u660e\uff1a\u5047\u8bbe\u3001\u53d8\u91cf\u63a7\u5236\u3001\u8868\u5f81\u624b\u6bb5\u3001\u6027\u80fd\u6570\u636e\u548c\u590d\u9a8c\u7ed3\u679c\u3002",
        "mode": "weak_match",
    },
    "pm": {
        "role_name": "\u4ea7\u54c1\u7ecf\u7406",
        "evidence_terms": ["\u7528\u6237", "\u9700\u6c42", "\u75db\u70b9", "\u4ea7\u54c1", "\u6307\u6807", "\u8f6c\u5316", "\u7559\u5b58", "\u53cd\u9988", "\u53d6\u820d", "MVP", "PRD", "\u539f\u578b", "\u4e0a\u7ebf", "\u8fed\u4ee3", "\u4f18\u5148\u7ea7", "\u4e1a\u52a1", "\u9a8c\u8bc1", "\u589e\u957f", "\u6210\u672c"],
        "weak_signal_terms": ["\u7b97\u6cd5", "\u6a21\u578b", "\u673a\u5668\u4eba", "\u6750\u6599", "\u5b9e\u9a8c", "\u4f4e\u7a7a", "\u822a\u7ebf"],
        "weak_judgement": "\u504f\u6280\u672f\uff0c\u4ea7\u54c1\u5224\u65ad\u4e0d\u8db3",
        "fix": "\u8865\u7528\u6237\u95ee\u9898/\u53d6\u820d/\u6307\u6807\u9a8c\u8bc1",
        "follow_up": "\u4f60\u600e\u4e48\u8bc1\u660e\u8fd9\u662f\u771f\u9700\u6c42\uff1f",
        "rewrite": "\u4e0b\u4e00\u7248\u7528\u4e00\u4e2a\u4ea7\u54c1\u6848\u4f8b\u8bf4\u660e\uff1a\u7528\u6237\u95ee\u9898\u3001\u65b9\u6848\u53d6\u820d\u3001\u4e0a\u7ebf\u6307\u6807\u3001\u53cd\u9988\u548c\u8fed\u4ee3\u3002",
        "mode": "weak_match",
    },
}


def _job_rubric(job_type: str) -> Dict:
    return JOB_EVALUATION_RUBRICS.get(job_type, {
        "role_name": JOB_TYPE_NAMES_CN.get(job_type, "\u76ee\u6807\u5c97\u4f4d"),
        "evidence_terms": [],
        "weak_signal_terms": [],
        "weak_judgement": "\u65b9\u5411\u76f8\u5173\uff0c\u8bc1\u636e\u4e0d\u8db3",
        "fix": "\u8865\u5c97\u4f4d\u76f8\u5173\u9879\u76ee\u8bc1\u636e",
        "follow_up": "\u8fd9\u4e2a\u7ed3\u679c\u4f60\u600e\u4e48\u9a8c\u8bc1\uff1f",
        "rewrite": "\u4e0b\u4e00\u7248\u5148\u56de\u7b54\u95ee\u9898\uff0c\u518d\u8865\u4e00\u4e2a\u5c97\u4f4d\u76f8\u5173\u573a\u666f\u3001\u4e2a\u4eba\u52a8\u4f5c\u548c\u9a8c\u8bc1\u7ed3\u679c\u3002",
        "mode": "weak_match",
    })


def _job_specific_fix(job_type: str) -> str:
    return _job_rubric(job_type).get("fix", "\u8865\u5c97\u4f4d\u76f8\u5173\u9879\u76ee\u8bc1\u636e")


def _has_job_evidence(text: str, rubric: Dict) -> bool:
    terms = rubric.get("evidence_terms", [])
    hits = [term for term in terms if term in text]
    # ??????????????????????????/??/??/??/???????????????
    if rubric.get("role_name") == "????":
        strong_terms = ["??", "??", "??", "??", "??", "??", "??", "??", "??", "???", "??", "??", "??", "??"]
        return sum(1 for term in strong_terms if term in text) >= 1 and len(hits) >= 2
    return any(hits)


def _has_weak_signal(text: str, rubric: Dict) -> bool:
    return sum(1 for term in rubric.get("weak_signal_terms", []) if term in text) >= 2


def _force_off_topic_by_job(job_type: str, answer: str) -> bool:
    text = str(answer or "")
    rubric = _job_rubric(job_type)
    return rubric.get("mode") == "off_topic" and _has_weak_signal(text, rubric) and not _has_job_evidence(text, rubric)


def _force_weak_match_by_job(job_type: str, answer: str) -> bool:
    text = str(answer or "")
    rubric = _job_rubric(job_type)
    return rubric.get("mode") != "off_topic" and _has_weak_signal(text, rubric) and not _has_job_evidence(text, rubric)


def normalize_interview_quick_feedback(feedback: Dict, job_type: str, answer: str = "") -> Dict:
    """Normalize four quick feedback fields before frontend rendering."""
    rubric = _job_rubric(job_type)
    missed_points = feedback.get("missed_points") if isinstance(feedback.get("missed_points"), list) else []
    rewrite_advice = feedback.get("rewrite_advice") if isinstance(feedback.get("rewrite_advice"), list) else []
    forced_off_topic = _force_off_topic_by_job(job_type, answer)
    forced_weak_match = _force_weak_match_by_job(job_type, answer)
    model_claims_off_topic = any(
        "\u7b54\u975e\u6240\u95ee" in str(item) or "\u8dd1\u9898" in str(item)
        for item in [feedback.get("quick_judgement"), feedback.get("summary"), feedback.get("most_important_fix"), *missed_points]
    )
    allow_model_off_topic = rubric.get("mode") == "off_topic"
    is_off_topic = forced_off_topic or (allow_model_off_topic and model_claims_off_topic and not forced_weak_match)

    if forced_weak_match or (model_claims_off_topic and not allow_model_off_topic):
        feedback["quick_judgement"] = rubric["weak_judgement"]
        feedback["most_important_fix"] = rubric["fix"]
        feedback["follow_up_question"] = rubric["follow_up"]
        feedback["rewrite_example"] = rubric["rewrite"]
    elif is_off_topic:
        feedback["quick_judgement"] = "\u7b54\u975e\u6240\u95ee\uff0c\u5c97\u4f4d\u4e0d\u5339\u914d"
        feedback["most_important_fix"] = rubric["fix"]
        feedback["follow_up_question"] = "\u8bf7\u7528\u672c\u5c97\u4f4d\u7ecf\u5386\u91cd\u7b54\u3002"
        feedback["rewrite_example"] = rubric["rewrite"]
    else:
        feedback["quick_judgement"] = _compact_interview_text(
            feedback.get("quick_judgement") or feedback.get("summary"),
            24,
            "\u65b9\u5411\u76f8\u5173\uff0c\u8bc1\u636e\u4e0d\u591f"
        )
        feedback["most_important_fix"] = _compact_interview_text(
            feedback.get("most_important_fix") or (missed_points[0] if missed_points else ""),
            32,
            rubric["fix"]
        )
        feedback["follow_up_question"] = _compact_interview_text(
            feedback.get("follow_up_question"),
            32,
            rubric["follow_up"]
        )
        feedback["rewrite_example"] = _compact_interview_text(
            feedback.get("rewrite_example") or feedback.get("sample_rewrite") or (rewrite_advice[0] if rewrite_advice else ""),
            120,
            rubric["rewrite"]
        )

    feedback["rewrite_example"] = _detemplate_interview_rewrite(feedback.get("rewrite_example"), rubric, job_type)
    feedback["suggestion"] = feedback["most_important_fix"]
    feedback["summary"] = feedback["quick_judgement"]
    return feedback


def infer_job_type_from_text(jd_content: str, resume_content: str = "") -> str:
    text = f"{jd_content}\n{resume_content}"
    rules = [
        ("lowAltitude", ["??", "??", "??", "eVTOL", "???", "??", "??"]),
        ("material", ["??", "??", "??", "??", "??", "??", "??", "???", "??", "??"]),
        ("robot", ["???", "ROS", "SLAM", "??", "????", "???", "????"]),
        ("ai", ["??", "??", "??", "??", "RAG", "???", "????", "????", "??"]),
        ("pm", ["??", "??", "??", "PRD", "MVP", "??", "??", "??", "??"]),
    ]
    scores = {job: sum(term in text for term in terms) for job, terms in rules}
    best = max(scores.items(), key=lambda item: item[1])
    return best[0] if best[1] > 0 else "pm"


def extract_resume_focus(jd_content: str, resume_content: str, analysis_result: Optional[Dict] = None) -> Dict:
    analysis_result = analysis_result or {}
    text = resume_content or ""
    project_patterns = [
        r"([^\n??;]{2,30}(?:??|??|??|??|??|??|??))",
        r"([^\n??;]{2,30}(?:????|???|???|??|??|??|??)[^\n??;]{0,20})",
    ]
    projects = []
    for pattern in project_patterns:
        for match in re.findall(pattern, text):
            item = str(match).strip(" -?:?,??;\n\t")
            if item and item not in projects:
                projects.append(item[:40])
    keywords = []
    raw_keywords = analysis_result.get("keywords") if isinstance(analysis_result, dict) else []
    for item in raw_keywords if isinstance(raw_keywords, list) else []:
        word = str(item.get("word", "")).strip() if isinstance(item, dict) else str(item).strip()
        if word and word not in keywords:
            keywords.append(word)
    if not keywords:
        for word in re.findall(r"[A-Za-z][A-Za-z+#]{1,20}|[\u4e00-\u9fa5]{2,8}", jd_content or ""):
            if word not in ["????", "????", "??", "??", "??", "??"] and word not in keywords:
                keywords.append(word)
            if len(keywords) >= 6:
                break
    return {"projects": projects[:3], "keywords": keywords[:6]}


def build_contextual_interview_question(job_type: str, jd_content: str, resume_content: str, analysis_result: Optional[Dict] = None) -> str:
    focus = extract_resume_focus(jd_content, resume_content, analysis_result)
    project = focus["projects"][0] if focus["projects"] else "????????????"
    keywords = "?".join(focus["keywords"][:4]) or "JD ????"
    if job_type == "material":
        return f"????????{project}???? JD ??{keywords}????????????????????????????????????????"
    if job_type == "lowAltitude":
        return f"???? JD ??{keywords}??????????{project}???????????????????????"
    if job_type == "robot":
        return f"??????{project}???? JD ??{keywords}????????????????????????????????"
    if job_type == "ai":
        return f"??????{project}???? JD ??{keywords}??????????????/???????????????"
    return f"???? JD ??{keywords}??????????{project}?????????????????????????????"


@app.post("/api/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    job_type = request.job_type or infer_job_type_from_text(request.jd_content or "", request.resume_content or "")
    if request.jd_content and request.resume_content:
        first_question = build_contextual_interview_question(
            job_type,
            request.jd_content,
            request.resume_content,
            request.analysis_result,
        )
        questions = [first_question]
        source_context = {
            "source": request.source or "resume_analysis",
            "jd_content": request.jd_content,
            "resume_content": request.resume_content,
            "analysis_result": request.analysis_result or {},
        }
    else:
        questions = generate_interview_questions(job_type)
        source_context = {}

    interview_id = f"int-{datetime.utcnow().timestamp()}"
    active_interviews[interview_id] = {
        "job_type": job_type,
        "questions": questions[:1],
        "question_plan": questions,
        "answers": [],
        "scores": [],
        "feedbacks": [],
        "modules": ["motivation"],
        "source_context": source_context,
    }
    return InterviewStartResponse(id=interview_id, questions=questions[:1])

def generate_rule_based_interview_feedback(question: str, answer: str, job_type: str):
    text = str(answer or "").strip()
    rubric = _job_rubric(job_type)
    evidence_hit = _has_job_evidence(text, rubric)
    weak_hit = _has_weak_signal(text, rubric)
    score = 6
    if len(text) < 20:
        score = 3
    elif evidence_hit:
        score = 7
    if weak_hit and not evidence_hit:
        score = 4

    if weak_hit and not evidence_hit:
        summary = rubric.get("weak_judgement", "?????????")
        fix = rubric.get("fix", "?????????")
    else:
        summary = "?????????????"
        fix = rubric.get("fix", "?????????")

    return {
        "score": score,
        "dimensions": [
            {"label": "????", "score": 0, "comment": summary},
            {"label": "????", "score": 0, "comment": fix},
            {"label": "?????", "score": 0, "comment": rubric.get("rewrite", "?????????????????????????")},
        ],
        "suggestion": fix,
        "hit_points": ["????????"] if text else [],
        "missed_points": [fix],
        "rewrite_advice": [rubric.get("rewrite", "?????????????????????????")],
        "summary": summary,
        "quick_judgement": summary,
        "most_important_fix": fix,
        "rewrite_example": rubric.get("rewrite", "?????????????????????????"),
        "follow_up_question": rubric.get("follow_up", "??????????"),
    }


@app.post("/api/interview/answer", response_model=InterviewAnswerResponse)
async def submit_answer(request: InterviewAnswerRequest):
    if request.interview_id not in active_interviews:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = active_interviews[request.interview_id]
    question = interview["questions"][request.question_index]
    
    job_name = JOB_TYPE_NAMES_CN.get(interview.get("job_type", ""), "????")

    prompt = build_interview_prompt(job_name, question, request.answer)
    if os.getenv("INTERVIEW_AI_SCORING", "true").lower() == "true":
        result = call_fast_interview_api(prompt)
        if result:
            try:
                data = parse_model_json_response(result)
                hit_points = data.get("hit_points", []) or []
                missed_points = data.get("missed_points", []) or []
                rewrite_advice = data.get("rewrite_advice", []) or []
                sample_rewrite = data.get("sample_rewrite", "")
                summary = data.get("summary", "")
                quick_judgement = data.get("quick_judgement") or summary or "?????????"
                most_important_fix = data.get("most_important_fix") or (missed_points[0] if missed_points else "??????????")
                rewrite_example = data.get("rewrite_example") or sample_rewrite or (rewrite_advice[0] if rewrite_advice else "??????????????????????????")
                follow_up_question = data.get("follow_up_question") or "??????????"
                score = int(data.get("score", data.get("total_score", 6)) or 6)
                score = max(0, min(10, score))
                feedback = {
                    "score": score,
                    "dimensions": [
                        {"label": "命中点", "score": score, "comment": "；".join(hit_points) if hit_points else "回答有基础信息，但亮点不够集中。"},
                        {"label": "缺口", "score": score, "comment": "；".join(missed_points) if missed_points else "需要补充更具体的岗位相关证据。"},
                        {"label": "改写建议", "score": score, "comment": "；".join(rewrite_advice) if rewrite_advice else "建议按场景、动作、结果重新组织回答。"},
                    ],
                    "suggestion": most_important_fix,
                    "hit_points": hit_points,
                    "missed_points": missed_points,
                    "rewrite_advice": rewrite_advice,
                    "sample_rewrite": sample_rewrite,
                    "summary": quick_judgement,
                    "quick_judgement": quick_judgement,
                    "most_important_fix": most_important_fix,
                    "rewrite_example": rewrite_example,
                    "follow_up_question": follow_up_question,
                }
            except Exception as parse_error:
                logger.warning("Interview AI JSON parse failed, use fallback: %s", parse_error)
                feedback = generate_rule_based_interview_feedback(question, request.answer, interview.get("job_type", "ai"))
        else:
            feedback = generate_rule_based_interview_feedback(question, request.answer, interview.get("job_type", "ai"))
    else:
        feedback = generate_rule_based_interview_feedback(question, request.answer, interview.get("job_type", "ai"))

    feedback = normalize_interview_quick_feedback(feedback, interview.get("job_type", "ai"), request.answer)

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
    """Generate local fallback feedback when model scoring is unavailable."""
    return {
        "score": 6,
        "dimensions": [
            {"label": "内容完整性", "score": 6, "comment": "回答覆盖了问题主干，但还需要补充具体证据。"},
            {"label": "逻辑清晰度", "score": 6, "comment": "表达基本清楚，建议用先结论后证据的结构。"},
            {"label": "岗位匹配度", "score": 6, "comment": "能看到一定匹配点，但还需要扣回岗位要求。"},
        ],
        "overall": "回答具备基础信息，但证据、量化结果和岗位关联还不够。",
        "suggestions": [
            "补充一个真实项目场景。",
            "说明你的个人动作和边界。",
            "加入可验证结果或指标。",
        ],
    }

def build_interview_advice(interview: dict, avg_score: float) -> str:
    job_type = interview.get("job_type", "ai")
    job_name = JOB_TYPE_NAMES_CN.get(job_type, "目标岗位")
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

    hit_points = unique(hit_points)[:3]
    missed_points = unique(missed_points)[:3]
    rewrite_advice = unique(rewrite_advice)[:3]
    return "\n".join([
        f"本次模拟面试方向：{job_name}，平均分：{avg_score:.1f}/10。",
        "已体现亮点：" + ("；".join(hit_points) if hit_points else "回答中已经有基础信息，但亮点还不够集中。"),
        "主要缺口：" + ("；".join(missed_points) if missed_points else "需要继续补充项目证据、量化结果和岗位关联。"),
        "改进建议1：" + (rewrite_advice[0] if len(rewrite_advice) > 0 else "先用一句话给结论，再展开背景、行动和结果。"),
        "改进建议2：" + (rewrite_advice[1] if len(rewrite_advice) > 1 else "把经历中的个人贡献和协作边界说清楚。"),
        "改进建议3：" + (rewrite_advice[2] if len(rewrite_advice) > 2 else "用数据、交付物或业务影响证明结果。"),
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
    
    # 鎸佷箙鍖栧埌鏁版嵁搴擄紙鐧诲綍鐢ㄦ埛鎵嶄繚瀛橈級
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
            stats_cache.pop(current_user.phone, None)
        except Exception as e:
            logger.warning(f"淇濆瓨闈㈣瘯鍘嗗彶澶辫触: {e}")
    
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
        logger.warning(f"鏌ヨ闈㈣瘯鍘嗗彶澶辫触: {e}")
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
        logger.warning(f"鏌ヨ闈㈣瘯鍘嗗彶璇︽儏澶辫触: {e}")
        raise HTTPException(status_code=500, detail="鏌ヨ闈㈣瘯鍘嗗彶璇︽儏澶辫触")

@app.get("/api/jobs", response_model=List[Job])
async def get_jobs(category: str = "all", education: str = "all", include_expired: bool = False):
    """Get jobs from database."""
    jobs = JobService.get_jobs(
        category=category,
        education=education,
        include_expired=include_expired,
    )
    return jobs

@app.get("/api/jobs/browse-history")
async def get_job_browse_history(current_user: Optional[User] = Depends(get_optional_user)):
    if not current_user:
        return []
    try:
        supabase = get_supabase()
        result = supabase.table("job_browse_history") \
            .select("job_id, viewed_at") \
            .eq("user_phone", current_user.phone) \
            .order("viewed_at", desc=True) \
            .limit(20) \
            .execute()

        records = []
        for item in result.data or []:
            job = JobService.get_job_by_id(item.get("job_id"))
            if not job:
                continue
            records.append({**job, "viewedAt": item.get("viewed_at")})
        return records
    except Exception as e:
        logger.warning("鏌ヨ宀椾綅娴忚鍘嗗彶澶辫触: %s", e)
        return []

@app.post("/api/jobs/{id}/browse")
async def record_job_browse(id: int, current_user: Optional[User] = Depends(get_optional_user)):
    if not current_user:
        return {"success": False}
    job = JobService.get_job_by_id(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        supabase = get_supabase()
        supabase.table("job_browse_history").upsert(
            {
                "user_phone": current_user.phone,
                "job_id": id,
                "viewed_at": datetime.utcnow().isoformat()
            },
            on_conflict="user_phone,job_id"
        ).execute()
        stats_cache.pop(current_user.phone, None)
        return {"success": True}
    except Exception as e:
        logger.warning("淇濆瓨宀椾綅娴忚鍘嗗彶澶辫触: %s", e)
        return {"success": False}

@app.get("/api/jobs/{id}", response_model=Job)
async def get_job_by_id(id: int):
    """Get one job from database."""
    job = JobService.get_job_by_id(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

TIPS_DATA = [
    "面试开场先用 30 秒说清：我是谁、我为什么匹配这个岗位、我能带来什么结果。",
    "回答项目经历时不要只说参与，要说清你的动作、工具、产出和可验证结果。",
    "遇到不会的问题不要硬编，先说明当前理解，再给出拆解思路和学习路径。",
    "投递前把 JD 里的 3-5 个核心关键词自然嵌入简历，不要堆砌关键词。",
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
    """Get current user statistics."""







    if not current_user:
        return StatsResponse(resume=0, interview=0, browse=0)

    try:
        phone = current_user.phone
        cached = stats_cache.get(phone)
        if cached and time.time() < cached["expires_at"]:
            return StatsResponse(**cached["data"])

        supabase = get_supabase()

        # 鏌ョ畝鍘嗗垎鏋愭鏁?
        resume_result = supabase.table("resume_history") \
            .select("id", count="exact") \
            .eq("user_phone", phone) \
            .execute()
        resume_count = resume_result.count if resume_result.count else 0

        # 鏌ラ潰璇曟鏁?
        interview_result = supabase.table("interview_history") \
            .select("id", count="exact") \
            .eq("user_phone", phone) \
            .execute()
        interview_count = interview_result.count if interview_result.count else 0

        browse_count = 0
        try:
            browse_result = supabase.table("job_browse_history") \
                .select("job_id", count="exact") \
                .eq("user_phone", phone) \
                .execute()
            browse_count = browse_result.count if browse_result.count else 0
        except Exception as browse_error:
            logger.warning("鏌ヨ宀椾綅娴忚缁熻澶辫触: %s", browse_error)

        data = {
            "resume": resume_count,
            "interview": interview_count,
            "browse": browse_count
        }
        stats_cache[phone] = {
            "data": data,
            "expires_at": time.time() + 30
        }

        return StatsResponse(
            resume=resume_count,
            interview=interview_count,
            browse=browse_count
        )
    except Exception as e:
        logger.warning(f"鏌ヨ缁熻鏁版嵁澶辫触: {e}")
        return StatsResponse(resume=0, interview=0, browse=0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



