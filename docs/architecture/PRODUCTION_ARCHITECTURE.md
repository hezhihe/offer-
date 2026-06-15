# Offer Compass 生产架构

更新时间：2026-06-03

## 最终部署决策

当前生产后端使用 Railway。

原因：MVP 上线阶段曾遇到 Render 免费版冷启动时间过长，导致系统响应慢，不适合演示和交付，因此后端迁移到 Railway。

当前证据：

- `backend/railway.toml` 定义了 Railway 的 FastAPI 启动命令和健康检查路径。
- `frontend/netlify.toml` 将 `/api/*` 代理到 `https://offer-compass-api-production.up.railway.app/api/:splat`。
- `https://offer-compass-api-production.up.railway.app/api/jobs` 返回 `200`。
- `https://offer-compass-api-production.up.railway.app/docs` 返回 FastAPI 文档页。
- Render 配置已从项目中移除，不是当前生产事实源。

不要让 Render 和 Railway 同时作为同一个前端的生产后端。这样会导致日志分散、环境变量分散、部署结果误判。

## 生产拓扑

```text
浏览器
  |
  | https://<netlify-site>/api/*
  v
Netlify 前端
  |
  | redirects 代理
  v
Railway 后端
  |
  | supabase-py
  v
Supabase PostgreSQL / Storage

Railway 后端
  |
  | requests
  v
DeepSeek API
```

## 前端

平台：Netlify

构建配置：

| 配置项 | 值 |
| --- | --- |
| Base directory | `frontend` |
| Build command | `npm run build` |
| Publish directory | `dist` |
| Production API base | `/api` |

生产环境变量：

| 变量 | 值 |
| --- | --- |
| `VITE_API_BASE_URL` | `/api` |

原因：构建后的 Vue 应用只请求同源 `/api`，再由 Netlify 转发到 Railway 后端。这样后端域名变更时只需要修改 Netlify 配置，不需要重新散改前端业务代码。

## 后端

平台：Railway

`backend/railway.toml` 中的服务配置：

| 配置项 | 值 |
| --- | --- |
| Builder | `RAILPACK` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/api/jobs` |
| Restart policy | `on_failure` |

生产后端地址：

```text
https://offer-compass-api-production.up.railway.app
```

后端必需环境变量：

| 变量 | 用途 |
| --- | --- |
| `SUPABASE_URL` | Supabase 项目地址 |
| `SUPABASE_SERVICE_KEY` | Supabase service role key，只能放后端 |
| `API_SECRET_KEY` | JWT 签名密钥 |
| `CORS_ORIGINS` | Netlify 前端生产域名 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_API_URL` | `https://api.deepseek.com/v1/chat/completions` |

## 规则

- 生产环境浏览器不能请求 Render。
- 生产环境浏览器不能请求 `127.0.0.1` 或 `localhost`。
- 密钥只能放在 Railway 或 Supabase 设置里，不能放进前端环境变量。
- 前端代码使用 `VITE_API_BASE_URL=/api`。
- 如果 Railway 后端域名变化，只修改 `frontend/netlify.toml` 和本架构文档。
