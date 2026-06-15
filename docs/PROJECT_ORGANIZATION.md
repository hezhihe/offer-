# 项目文件整理说明

更新时间：2026-06-05

本次整理只移动和归类文件，不删除文件，不修改业务逻辑。

## 根目录保留内容

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | Codex / AI 助手协作说明 |
| `CLAUDE.md` | 兼容 Claude 等 AI 助手的项目上下文 |
| `README.md` | 项目入口说明 |
| `.gitignore` | Git 忽略规则 |
| `backend/` | FastAPI 后端 |
| `frontend/` | Vue 前端 |
| `docs/` | 项目文档 |
| `experiments/` | 隔离实验区 |
| `archive/` | 历史配置和备份归档 |
| `artifacts/` | 日志、截图、构建产物、演示素材等非源码资产 |
| `tests/` | 测试脚本 |

## docs 文档分组

| 路径 | 用途 |
| --- | --- |
| `docs/architecture/` | 生产架构和部署事实源 |
| `docs/acceptance/` | 线上验收清单和交付检查 |
| `docs/alignment/` | 项目目标、范围和共识 |
| `docs/design/` | 产品和技术设计 |
| `docs/knowledge/` | 简历、面试等知识库 |
| `docs/supabase/` | Supabase 集成文档 |
| `docs/tasks/` | 任务拆解 |
| `docs/archive/` | AI 上下文归档 |
| `docs/legacy/` | 旧技术方案 |

## 数据库脚本分组

| 路径 | 用途 |
| --- | --- |
| `backend/database/schema/` | 建表脚本 |
| `backend/database/migrations/` | 增量变更脚本 |
| `backend/database/seed/` | 种子和测试数据 |
| `backend/database/manual/` | 可直接复制到 Supabase SQL Editor 的手动执行脚本 |

## 归档和产物分组

| 路径 | 用途 |
| --- | --- |
| `archive/backups/` | 历史备份 |
| `artifacts/logs/backend/` | 后端运行日志 |
| `artifacts/logs/frontend/` | 前端运行日志 |
| `artifacts/screenshots/` | 截图 |

## 本次整理记录

| 原位置 | 新位置 | 原因 |
| --- | --- | --- |
| `docs/PRODUCTION_ARCHITECTURE.md` | `docs/architecture/PRODUCTION_ARCHITECTURE.md` | 生产架构归类 |
| `docs/ONLINE_ACCEPTANCE_CHECKLIST.md` | `docs/acceptance/ONLINE_ACCEPTANCE_CHECKLIST.md` | 线上验收归类 |
| `docs/ALIGNMENT_offer-compass.md` | `docs/alignment/ALIGNMENT_offer-compass.md` | 项目对齐文档归类 |
| `docs/DESIGN_offer-compass.md` | `docs/design/DESIGN_offer-compass.md` | 设计文档归类 |
| `docs/*supabase*.md` | `docs/supabase/` | Supabase 文档归类 |
| `docs/*KNOWLEDGE*.md` | `docs/knowledge/` | 知识库归类 |
| `docs/TASK_offer-compass.md` | `docs/tasks/TASK_offer-compass.md` | 任务文档归类 |
| `backend/database/*.sql` | `backend/database/schema/`、`migrations/`、`seed/`、`manual/` | 数据库脚本按用途归类 |
| `render.yaml` | 已删除 | Render 不是当前生产后端，继续保留会误导部署 |
| `backend/2.0.0` | 已删除 | 一次性 pip 安装输出，对项目运行无价值 |
| 空运行日志 | 已删除 | 日志可由本地运行重新生成，不进入仓库 |

## 约定

- 不移动 `backend/main.py`、`backend/railway.toml`、`frontend/netlify.toml`、`frontend/vite.config.js` 等运行和部署入口。
- 不删除文件；不确认用途的文件先归档。
- 新增上线文档优先放 `docs/architecture/` 或 `docs/acceptance/`。
- 新增数据库脚本必须放入 `schema/`、`migrations/`、`seed/`、`manual/` 之一。
- 日志、截图、安装输出等非源码产物放 `artifacts/`。
