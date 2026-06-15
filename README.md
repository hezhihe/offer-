# Offer Compass（Offer 罗盘）

Offer Compass 是面向 2026 届大学生的就业指导平台 MVP。当前目标不是继续堆新功能，而是保证核心求职流程稳定、可部署、可验收。

## 当前生产部署

| 项目 | 配置 |
| --- | --- |
| 前端平台 | Netlify |
| 后端平台 | Railway |
| 后端地址 | `https://offer-compass-api-production.up.railway.app` |
| 前端 API 基址 | `/api` |
| Netlify API 代理 | `/api/*` -> `https://offer-compass-api-production.up.railway.app/api/:splat` |

说明：

- Render 已不再作为当前 MVP 的生产后端。
- 生产环境不要使用 `127.0.0.1`、`localhost` 或 Render 地址作为前端 API 目标。
- Supabase 已创建 `public.job_browse_history`，岗位浏览记录和我的页面 browse 统计已通过线上验收。

## 当前功能范围

- 登录 / 注册：手机号 + 密码，密码使用 bcrypt 哈希保存。
- 个人中心：头像上传、使用记录、意见反馈、登录后修改密码。
- 简历分析：支持粘贴文本和上传 PDF / Word，分析结果写入 Supabase。
- 模拟面试：按岗位生成问题、提交回答、生成反馈并保存历史。
- 招聘日历：岗位列表、日期视图、岗位详情和 JD 描述。
- 首页 Tips：求职提示展示、手动切换和定时轮播。
- 岗位浏览记录：浏览岗位后写入 Supabase，并在我的页面统计。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Pinia、Vue Router、Axios、原生 CSS |
| 后端 | FastAPI、Pydantic、JWT、passlib / bcrypt、uvicorn |
| 数据库 | Supabase PostgreSQL |
| 文件存储 | Supabase Storage |
| 文件解析 | pypdf、python-docx |
| AI 能力 | DeepSeek 主模型 + 降级逻辑 |

## 目录结构

```text
backend/
  main.py
  app/services/
  database/
    schema/
    migrations/
    seed/
    manual/
  requirements.txt
  .env.example

frontend/
  src/api/
  src/components/
  src/composables/
  src/router/
  src/stores/
  src/views/
  package.json
  .env.example

docs/
  architecture/
  acceptance/
  alignment/
  design/
  knowledge/
  supabase/
  tasks/
  archive/
experiments/
tests/
```

## 本地启动

后端：

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端文档：`http://127.0.0.1:8005/docs`

## 环境变量

后端环境变量放在 `backend/.env`，不要提交真实密钥。

| 变量 | 说明 |
| --- | --- |
| `SUPABASE_URL` | Supabase 项目地址 |
| `SUPABASE_SERVICE_KEY` | Supabase service role key，只能放后端 |
| `API_SECRET_KEY` | JWT 签名密钥，生产环境必须使用长随机值 |
| `CORS_ORIGINS` | 允许访问后端的前端域名，多个域名用英文逗号分隔 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_API_URL` | DeepSeek API 地址 |

前端生产环境变量：

| 变量 | 值 |
| --- | --- |
| `VITE_API_BASE_URL` | `/api` |

## 数据库脚本

Supabase 表结构和种子数据在 `backend/database/`。

上线前必须确认这些脚本已经在目标 Supabase 项目执行完成：

- `backend/database/schema/create_users_table.sql`
- `backend/database/schema/create_resume_history.sql`
- `backend/database/schema/create_interview_history.sql`
- `backend/database/schema/create_user_feedback.sql`
- `backend/database/seed/seed_jobs.sql`
- `backend/database/seed/seed_tips.sql`
- `backend/database/migrations/update_job_requirements_mvp.sql`
- `backend/database/migrations/update_job_status_tracking.sql`

## 构建验证

前端：

```bash
cd frontend
npm run build
```

后端：

```bash
cd backend
python -c "import main; print('backend import ok')"
```

## 上线验收

上线验收标准见：

- `docs/architecture/PRODUCTION_ARCHITECTURE.md`
- `docs/acceptance/ONLINE_ACCEPTANCE_CHECKLIST.md`

当前已验证：

- Railway `/api/jobs` 返回 `200`。
- Netlify `/api/jobs` 返回 `200`。
- 线上登录成功。
- 岗位浏览写入成功。
- `stats/mine` 返回 `resume=1`、`interview=1`、`browse=1`。

## MVP 风险

- 当前用户体系是项目自建登录，不是 Supabase Auth。
- 邮箱 / 短信找回密码未接入，MVP 只支持登录后修改密码。
- 招聘岗位数据是种子数据，不是实时招聘平台爬取数据。
- 面试评分质量仍需复查，之前合理回答出现过 `score=0`。
- 后续新增功能必须先隔离验证，再接入主流程。
