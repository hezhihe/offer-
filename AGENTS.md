# Offer Compass（Offer 罗盘）

2026 届大学生就业指导平台 MVP。目标是帮助学生完成求职过程中的几个核心动作：管理岗位信息、分析简历、准备模拟面试、查看个人使用记录。

## AI 协作要求

当用户提出项目问题、改进建议或指出错误时，先按下面四点解释，再决定是否修改代码：

1. **错误根源**：说明问题本质，不只看表面现象。
2. **涉及的技术栈**：明确说明用到 Vue、Pinia、FastAPI、Supabase、JWT、File API、FormData、CSS 等哪些技术。
3. **为什么这样做**：解释方案选择和取舍，不只说“已修改”。
4. **对应的功能是什么**：把代码修改映射回产品功能和用户路径。

补充要求：

- 不要盲目迎合用户。判断成立就说明原因；判断有风险就指出风险。
- 按“从 Demo 到真实上线”的学习方式协作：先讲原理，再做小步修改，最后验证。
- 每次修改前尽量隔离影响范围，不做无关重构。
- 不删除用户文件，不擅自清空数据库，不泄露 `.env` 和密钥。
- 改完后说明验证结果，并在回复底部附前端预览地址。

## 技术栈

- **前端**：Vue 3、Vite、Pinia、Vue Router、Axios、原生 CSS。
- **后端**：Python FastAPI、Pydantic、JWT、passlib/bcrypt、uvicorn。
- **数据库**：Supabase PostgreSQL，通过 `supabase-py` 连接。
- **文件解析**：PDF 使用 `pypdf`，Word 使用 `python-docx`。
- **AI 能力**：DeepSeek 主模型，失败时走备用/降级逻辑。
- **文件存储**：头像使用 Supabase Storage，数据库保存头像 URL。

## 项目结构

```text
backend/
  main.py                 FastAPI 应用入口，包含主要 API 路由
  app/services/           业务服务层：用户、岗位、Supabase、头像、AI 知识规则
  database/               SQL 建表和种子数据脚本
  requirements.txt        Python 依赖
  .env                    本地密钥配置，不允许提交

frontend/
  src/api/                Axios API 客户端
  src/components/         可复用 Vue 组件
  src/composables/        组合式函数，例如 useToast
  src/router/             Vue Router 路由
  src/stores/             Pinia 状态管理
  src/views/              页面：Auth、Home、Resume、Interview、Calendar、Profile
  src/assets/styles/      全局 CSS
  package.json            前端依赖和脚本

docs/                     项目设计、上下文归档、知识库
experiments/              隔离实验区
AGENTS.md                 当前 AI 协作说明
CLAUDE.md                 兼容其他 AI 助手的项目上下文
README.md                 项目说明
```

## 常用命令

```bash
# 后端，端口 8005
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload

# 前端，端口 5173
cd frontend
npm run dev

# 前端构建验证
cd frontend
npm run build
```

## 关键约定

- 前端页面使用 Vue 单文件组件和 `<script setup>`。
- 状态管理按业务域放在 Pinia store：`auth`、`jobs`、`resume`、`interview`。
- API 调用集中在 `frontend/src/api/`，不要在组件里散写请求。
- 后端目前主要路由集中在 `backend/main.py`，复杂逻辑逐步下沉到 `app/services/`。
- 登录使用手机号 + 密码，用户数据存在 Supabase `users_data` 表。
- 未登录用户不能访问核心功能页，应跳转到 `/auth`。
- 图片、PDF、Word 这类文件不要直接塞入普通数据库字段；图片类资产优先放对象存储，数据库保存 URL 或路径。

## Supabase 表

| 表名 | 用途 | 关键字段 |
| --- | --- | --- |
| `users_data` | 用户数据 | `phone`, `nickname`, `email`, `avatar`, `hashed_password`, `last_login_at` |
| `resume_history` | 简历分析历史 | `user_phone`, `job_title`, `match_score`, `keywords`, `reconstructed_resume` |
| `interview_history` | 模拟面试历史 | `user_phone`, `job_type`, `questions`, `answers`, `scores`, `advice` |
| `jobs` | 岗位数据 | `title`, `company`, `deadline`, `category`, `education`, `url` |
| `daily_tips` / tips 数据 | 首页提示 | `content` |

## 当前功能状态

- 注册 / 登录：已接入 `users_data`，注册后回到登录页。
- 用户头像：上传到 Supabase Storage `avatars` bucket，`users_data.avatar` 保存 URL。
- 简历分析：支持粘贴文本和上传 PDF/Word；分析结果会写入 `resume_history`。
- 模拟面试：支持按岗位出题、回答、定性反馈；历史写入 `interview_history`。
- 使用记录：我的页面可查看简历、面试、浏览岗位记录；面试记录可查看总结详情。
- 招聘日历：目前主要展示岗位列表和日期视图，未来可演进为求职待办和招聘事件管理。
- 首页 Tips：支持手动“换一个”和定时轮播。

## 待办与风险

- 2026-05-30 前进入交付模式：优先稳定核心流程，不再扩大型新功能。
- 项目公网交付不能使用 `127.0.0.1`，需要部署前端和后端。
- GitHub 提交前必须确认 `.env`、Service Role Key、API Key 不被提交。
- UI 需要做交付级统一，但不做大规模重设计。
- 日历完整待办、提醒、自动招聘信息整合属于后续版本，不建议塞进当前 MVP。

