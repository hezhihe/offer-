# Offer Compass（Offer 罗盘）

Offer Compass 是面向 2026 届大学生的求职指导 MVP，覆盖岗位浏览、简历分析、模拟面试、招聘日历、个人中心、意见反馈和登录后修改密码等核心流程。

## 当前交付范围

- 登录 / 注册：手机号 + 密码，密码使用 bcrypt 哈希保存。
- 个人中心：头像上传、使用记录、意见反馈、登录后修改密码。
- 简历分析：支持粘贴文本和上传 PDF / Word，分析结果写入 Supabase。
- 模拟面试：按岗位生成问题、提交回答、生成反馈并保存历史。
- 招聘日历：岗位列表、日历视图、岗位详情和更完整的 JD 描述。
- 首页 Tips：求职提示展示和切换。

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

- 前端：http://127.0.0.1:5173
- 后端文档：http://127.0.0.1:8005/docs

## 环境变量

后端环境变量在 `backend/.env`，不要提交真实密钥。

| 变量 | 说明 |
| --- | --- |
| `SUPABASE_URL` | Supabase 项目地址 |
| `SUPABASE_SERVICE_KEY` | Supabase service role key，只放后端 |
| `API_SECRET_KEY` | JWT 签名密钥，生产环境必须换成长随机值 |
| `CORS_ORIGINS` | 允许访问后端的前端域名，多个用英文逗号分隔 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_API_URL` | DeepSeek API 地址 |

前端环境变量在 `frontend/.env`：

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | API 基础地址。本地开发默认走 Vite 代理 `/api` |

## 数据库脚本

Supabase 表结构和种子数据在 `backend/database/`：

- `create_users_table.sql`
- `create_resume_history.sql`
- `create_interview_history.sql`
- `create_user_feedback.sql`
- `seed_jobs.sql`
- `seed_tips.sql`
- `update_job_requirements_mvp.sql`

上线前需要确认这些脚本已经在目标 Supabase 项目执行完成。

## 上线前检查

```bash
cd frontend
npm run build
```

```bash
cd backend
python -c "import main; print('backend import ok')"
```

上线时不要使用 `127.0.0.1` 作为公网 API 地址。部署后需要把：

- 后端 `CORS_ORIGINS` 改成真实前端域名
- 前端 `VITE_API_BASE_URL` 改成真实后端 API 地址，或由平台反向代理到 `/api`
- `API_SECRET_KEY` 换成生产级随机密钥
- Supabase service role key 只保存在后端环境变量里

## 部署建议

本项目是前后端分离项目，不建议把整个仓库当成一个纯前端项目直接部署。

### Vercel 前端

在 Vercel 导入 GitHub 仓库 `hezhihe/offer-`，设置：

| 配置项 | 值 |
| --- | --- |
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Install Command | `npm install` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

前端环境变量：

| 变量 | 值 |
| --- | --- |
| `VITE_API_BASE_URL` | `https://你的-render-后端域名/api` |

### Render 后端

在 Render 导入同一个 GitHub 仓库，使用 `render.yaml` 或手动创建 Web Service：

| 配置项 | 值 |
| --- | --- |
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

后端环境变量：

| 变量 | 说明 |
| --- | --- |
| `PYTHON_VERSION` | `3.11.11`，避免 Render 默认 Python 版本导致依赖编译失败 |
| `SUPABASE_URL` | Supabase 项目地址 |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `API_SECRET_KEY` | JWT 签名密钥 |
| `CORS_ORIGINS` | Vercel 前端公网地址，例如 `https://offer-xxx.vercel.app` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_API_URL` | `https://api.deepseek.com/v1/chat/completions` |

部署完成后，先拿到 Render 后端域名，再回到 Vercel 更新 `VITE_API_BASE_URL` 并重新部署前端。

## MVP 风险

- 当前用户体系是项目自建登录，不是 Supabase Auth。
- 邮箱 / 短信找回密码还未接入，MVP 只支持登录后修改密码。
- 招聘岗位数据是种子数据，不是实时招聘平台爬取数据。
- 公网交付需要部署前端、后端，并配置 HTTPS 和生产环境变量。

## Current Production Deployment

- Frontend: Netlify
- Backend: Railway, `https://offer-compass-api-production.up.railway.app`
- Frontend API base: `/api`
- Netlify proxy: `/api/*` -> `https://offer-compass-api-production.up.railway.app/api/:splat`
- Render config is historical/fallback only. Do not use Render as the production backend for this MVP.
- Before final acceptance, execute `backend/database/update_job_status_tracking.sql` in Supabase SQL Editor so `public.job_browse_history` exists.
