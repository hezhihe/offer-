# Offer Compass 线上验收清单

更新时间：2026-06-03

本清单用于判断线上 MVP 是否可以进入功能完善阶段。

## 本次验收环境

- 前端：`https://bejewelled-lamington-a93247.netlify.app`
- 后端：`https://offer-compass-api-production.up.railway.app`
- 测试账号：`19906030001`

## 本次验收结果

- 通过：Railway `/api/jobs` 返回 `200`。
- 通过：Railway `/docs` 返回 FastAPI 文档页。
- 通过：本地前端 `npm run build` 构建成功。
- 通过：Netlify `/api/jobs` 重新部署后返回 `200`。
- 通过：线上登录返回 `200`。
- 通过：测试账号线上 `stats/mine` 返回 `resume=1`、`interview=1`、`browse=1`。
- 通过：线上岗位浏览返回 `success=true`。
- 通过：Supabase 中 `public.job_browse_history` 已存在，并支持后端 upsert。
- 观察：之前合理面试回答出现过 `score=0`，接口可用，但评分质量需要复查。
- 观察：PowerShell 显示中文 API 内容时可能出现乱码，浏览器渲染仍需人工确认。

## 部署事实源

- [x] 后端生产平台是 Railway。
- [x] 前端生产平台是 Netlify。
- [x] `frontend/netlify.toml` 将 `/api/*` 代理到 Railway 后端。
- [x] `frontend/.env.production` 设置 `VITE_API_BASE_URL=/api`。
- [x] 生产前端不指向 Render、`localhost` 或 `127.0.0.1`。

## Railway 后端

- [x] Railway 服务使用 `backend/railway.toml`。
- [x] 启动命令使用 Railway `$PORT`。
- [x] `/api/jobs` 返回成功。
- [ ] `/docs` 是否允许公开，需要演示前确认。
- [ ] `CORS_ORIGINS` 包含准确的 Netlify 生产域名。
- [ ] Railway 环境变量已配置：`SUPABASE_URL`、`SUPABASE_SERVICE_KEY`、`API_SECRET_KEY`、`DEEPSEEK_API_KEY`、`DEEPSEEK_API_URL`。
- [ ] GitHub、Netlify 前端环境变量、浏览器 Console、网络响应中不暴露 API Key 或 service role key。

## Netlify 前端

- [x] Netlify base directory 是 `frontend`。
- [x] Build command 是 `npm run build`。
- [x] Publish directory 是 `dist`。
- [ ] Netlify 构建日志显示 `VITE_API_BASE_URL=/api`。
- [ ] 刷新嵌套路由不出现 404。
- [x] 浏览器请求走 `https://<netlify-site>/api/...`，不直接请求 Render 或本地地址。

## 核心用户路径

- [ ] 注册新账号。
- [x] 登录已有账号。
- [ ] 刷新页面后保持登录态。
- [ ] 首页 Tips 正常加载。
- [ ] 招聘日历岗位数据正常加载。
- [ ] 粘贴文本进行简历分析。
- [ ] 上传 PDF / Word 简历并收到分析结果。
- [ ] 开始模拟面试。
- [ ] 提交至少一个面试回答并收到反馈。
- [ ] 完成面试并保存历史。
- [ ] 个人中心可查看简历 / 面试历史。
- [ ] 上传头像并刷新后保持显示。

## 生产质量检查

- [x] 前端本地构建 `npm run build` 通过。
- [ ] 核心流程浏览器 Console 无明显红错。
- [ ] 无失败的 CORS preflight 请求。
- [ ] AI 调用超时表现可接受。
- [ ] Railway 日志无缺失环境变量错误。
- [x] Supabase 简历和面试历史表有预期测试记录。
- [x] Supabase `public.job_browse_history` 存在，并可由 Railway 后端 upsert。
- [ ] 移动端视口可完成登录、简历分析、面试、日历和个人中心流程。

## 发布判断

以下阻塞项通过后，才可以进入功能完善阶段：

- [x] 只有一个生产后端：Railway。
- [x] 只有一个前端 API 入口：`/api`。
- [x] 线上登录可用。
- [x] 简历和面试数据可写入 Supabase。
- [x] 岗位浏览历史表存在，浏览记录可写入。
- [ ] 没有密钥暴露。
