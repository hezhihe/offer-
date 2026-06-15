# Offer Compass 前端

本目录是 Offer Compass 的 Vue 3 前端应用。

## 技术栈

- Vue 3
- Vite
- Pinia
- Vue Router
- Axios
- 原生 CSS

## 本地启动

```bash
npm install
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

## API 配置

本地开发默认使用 Vite 代理：

```text
/api -> http://localhost:8005
```

生产环境使用 Netlify 代理：

```text
/api/* -> https://offer-compass-api-production.up.railway.app/api/:splat
```

生产环境变量：

```text
VITE_API_BASE_URL=/api
```

不要在前端代码或前端环境变量中写入 Supabase service role key、DeepSeek API Key 或后端密钥。

## 构建验证

```bash
npm run build
```

构建通过后，输出目录为：

```text
dist/
```
