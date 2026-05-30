# Offer Compass（Offer 罗盘）

这是 Offer Compass 项目的 AI 助手上下文文件，与 `AGENTS.md` 保持一致。它用于让不同 AI 编程助手快速理解项目结构、技术栈、协作方式和当前交付重点。

## 协作方式

用户希望通过这个项目学习 AI 编程，而不是只让 AI 执行指令。因此每次处理问题时，应按以下结构解释：

1. **错误根源**：这个问题本质是什么。
2. **涉及的技术栈**：用到了哪些前端、后端、数据库、文件、AI 或部署技术。
3. **为什么这样做**：说明方案选择和取舍。
4. **对应的功能是什么**：把技术修改映射回用户功能。

开发时遵守：

- 先解释，再小步修改。
- 先隔离，再验证。
- 不擅自删除文件或数据。
- 不泄露 `.env`、API Key、Supabase Service Key。
- 不做与当前目标无关的大重构。
- 改完要说明验证方式。

## 技术栈

- 前端：Vue 3、Vite、Pinia、Vue Router、Axios、原生 CSS。
- 后端：FastAPI、Pydantic、JWT、passlib/bcrypt、uvicorn。
- 数据库：Supabase PostgreSQL。
- 文件解析：pypdf、python-docx。
- 文件存储：Supabase Storage。
- AI：DeepSeek 主模型 + 降级策略。

## 项目结构

```text
backend/
  main.py
  app/services/
  database/
  requirements.txt

frontend/
  src/api/
  src/components/
  src/composables/
  src/router/
  src/stores/
  src/views/
  src/assets/styles/

docs/
experiments/
AGENTS.md
CLAUDE.md
README.md
```

## 运行命令

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload

cd frontend
npm run dev

cd frontend
npm run build
```

## 核心功能

- 注册 / 登录：手机号 + 密码，数据表为 `users_data`。
- 头像上传：Supabase Storage `avatars`，数据库保存 URL。
- 简历分析：上传 PDF/Word 或粘贴文本，结果保存到 `resume_history`。
- 模拟面试：按岗位动态问题，回答后生成定性反馈，历史保存到 `interview_history`。
- 招聘日历：当前以岗位展示为主，未来可扩展为求职事件和待办提醒。
- 我的页面：头像、用户信息、使用记录、反馈、社群入口、关于页面。
- 首页 Tips：支持轮播和手动切换。

## 数据表

| 表名 | 用途 |
| --- | --- |
| `users_data` | 用户主表 |
| `resume_history` | 简历分析历史 |
| `interview_history` | 面试历史 |
| `jobs` | 岗位数据 |
| `daily_tips` / tips 数据 | 首页提示 |

## 当前交付重点

截止时间为 2026-05-30。当前阶段应进入交付模式：

1. 稳定注册、登录、简历分析、模拟面试、岗位查看、使用记录。
2. 修复阻塞 bug 和明显 UI 问题。
3. 检查密钥，确保 GitHub 不提交 `.env`。
4. 准备 GitHub 代码仓库。
5. 准备公网可访问链接。

不要在交付前临时塞入复杂新模块，例如完整日历待办、提醒系统、自动招聘信息爬取、积分系统、社群商业化等。

