# Offer罗盘 - AI驱动的2026届毕业生求职助手

## 项目简介

Offer罗盘是一款面向2026届毕业生的AI驱动求职助手，致力于帮助大学生提升求职竞争力。

## 核心功能

- 📄 **简历重构**: AI分析JD，智能匹配关键词，优化简历内容
- 🎯 **面试模拟**: 智能评分，微表情分析，面试报告
- 📅 **招聘日历**: 新质生产力岗位精准推送，双视图展示
- 👤 **个人中心**: 用户统计，使用记录，意见反馈

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ 首页    │ │ 简历    │ │ 面试    │ │ 日历    │  │
│  │ Home    │ │ Resume  │ │ Interview││ Calendar│  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│  │ Profile │ │ Auth    │ │ 公共组件 │             │
│  └─────────┘ └─────────┘ └─────────┘             │
└─────────────────┬─────────────────────────────────┘
                  │ HTTP API
                  ▼
┌─────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                   │
│  ┌─────────────────┐ ┌─────────────────────────┐   │
│  │ /api/auth       │ │ 认证模块 (JWT)         │   │
│  │ /api/resume     │ │ 简历分析模块           │   │
│  │ /api/interview  │ │ 面试模拟模块           │   │
│  │ /api/jobs       │ │ 岗位管理模块           │   │
│  │ /api/tips       │ │ 求职提示模块           │   │
│  └─────────────────┘ └─────────────────────────┘   │
│                         │                         │
│                         ▼                         │
│              ┌─────────────────┐                  │
│              │ DeepSeek API    │                  │
│              └─────────────────┘                  │
└─────────────────────────────────────────────────────┘
```

## 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue | 3.4+ |
| 路由 | Vue Router | 4.3+ |
| 状态管理 | Pinia | 2.1+ |
| HTTP客户端 | Axios | 1.6+ |
| 构建工具 | Vite | 5.1+ |
| 后端框架 | FastAPI | 0.110+ |
| AI模型 | DeepSeek V4 | API |

## 快速开始

### 前置条件

- Node.js >= 20.x
- Python >= 3.10

### 安装依赖

```bash
# 前端依赖
cd frontend
npm install

# 后端依赖
cd ../backend
pip install -r requirements.txt
```

### 配置环境变量

编辑 `backend/.env` 文件：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
API_SECRET_KEY=your-secret-key-here-keep-it-safe
```

### 启动服务

```bash
# 启动后端 (端口 8000)
cd backend
python main.py

# 启动前端 (端口 5173)
cd frontend
npm run dev
```

### 访问地址

- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 项目结构

```
.
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── api/                 # API接口
│   │   ├── components/          # 公共组件
│   │   ├── composables/         # 组合式函数
│   │   ├── stores/              # Pinia状态管理
│   │   ├── views/               # 页面视图
│   │   ├── assets/styles/       # 全局样式
│   │   ├── router/              # 路由配置
│   │   ├── App.vue              # 根组件
│   │   └── main.js              # 入口文件
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/                     # 后端应用
│   ├── main.py                  # FastAPI入口
│   ├── requirements.txt         # Python依赖
│   └── .env                     # 环境变量
└── README.md
```

## API接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/signup` | POST | 用户注册 |
| `/api/resume/analyze` | POST | 简历分析 |
| `/api/interview/start` | POST | 开始面试 |
| `/api/interview/answer` | POST | 提交答案 |
| `/api/interview/complete` | POST | 完成面试 |
| `/api/jobs` | GET | 获取岗位列表 |
| `/api/tips/today` | GET | 获取今日提示 |

## 开发说明

### 前端开发

```bash
cd frontend
npm run dev      # 开发模式
npm run build    # 生产构建
npm run preview  # 预览构建结果
```

### 后端开发

```bash
cd backend
python main.py       # 启动开发服务器
uvicorn main:app     # 使用uvicorn启动
```

## 注意事项

1. **DeepSeek API Key**: 需要在硅基流动平台申请API Key
2. **安全性**: 生产环境请使用HTTPS，API密钥请勿提交到代码仓库
3. **Mock数据**: 未配置API Key时，系统自动使用Mock数据

## License

MIT License