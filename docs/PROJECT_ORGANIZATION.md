# 项目文件整理说明

更新时间：2026-05-27

本次整理只移动文件，不删除文件，不修改业务逻辑。

## 根目录保留内容

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | Codex / AI 助手协作说明 |
| `CLAUDE.md` | 兼容 Claude 等 AI 助手的项目上下文 |
| `README.md` | 项目说明 |
| `.gitignore` | Git 忽略规则 |
| `backend/` | FastAPI 后端 |
| `frontend/` | Vue 前端 |
| `docs/` | 项目文档 |
| `experiments/` | 隔离实验区 |
| `archive/` | 备份归档 |
| `artifacts/` | 截图、构建产物、演示素材等非源码资产 |
| `tests/` | 测试脚本 |

## 本次移动记录

| 原位置 | 新位置 | 原因 |
| --- | --- | --- |
| `AGENTS.md.bak-encoding-fix-20260527` | `archive/backups/encoding-fix-20260527/AGENTS.md.bak` | 编码修复前备份，移入归档 |
| `CLAUDE.md.bak-encoding-fix-20260527` | `archive/backups/encoding-fix-20260527/CLAUDE.md.bak` | 编码修复前备份，移入归档 |
| `backend/database/create_users_table.sql.bak-encoding-fix-20260527` | `archive/backups/encoding-fix-20260527/create_users_table.sql.bak` | 编码修复前备份，移入归档 |
| `test_*.png` | `artifacts/screenshots/initial-ui-20260508/` | 旧 UI 截图，不应堆在根目录 |
| `test_app.py` | `tests/test_app.py` | 测试脚本归入测试目录 |
| `seed_test_data.sql` | `backend/database/seed_test_data.sql` | SQL 种子数据归入数据库目录 |
| `26.5.8  2026年大学生就业指导平台 MVP 技术方案文档.txt` | `docs/legacy/2026大学生就业指导平台_MVP_技术方案文档_20260508.txt` | 旧技术方案归入历史文档 |

## 约定

- 根目录只放项目入口、说明和一级功能目录。
- 备份文件放 `archive/backups/`。
- 截图和演示素材放 `artifacts/`。
- 数据库脚本放 `backend/database/`。
- 测试脚本放 `tests/`。
- 不确认用途的文件先归档，不删除。

