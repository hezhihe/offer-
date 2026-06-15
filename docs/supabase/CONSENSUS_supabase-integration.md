# CONSENSUS 文档: Supabase 数据库集成

## 1. 需求描述

将 Offer 罗盘项目从内存假数据迁移到 Supabase 真实数据库，实现数据的持久化存储和查询。

## 2. 验收标准

### 2.1 功能验收
- [ ] 后端成功连接 Supabase 并创建客户端
- [ ] 数据库表结构按 DESIGN 文档创建（users, resumes, interviews, jobs, daily_tips）
- [ ] 后端 API 从内存数据切换到 Supabase 真实数据查询
- [ ] 用户认证接入 Supabase Auth
- [ ] 前端环境变量配置完成
- [ ] 数据流端到端验证通过

### 2.2 质量验收
- [ ] API 响应格式保持不变（向后兼容）
- [ ] 错误处理完善（数据库连接失败、查询失败等）
- [ ] 敏感信息（API Key）不泄露在前端代码中
- [ ] 代码通过类型检查

## 3. 技术实现方案

### 3.1 技术栈
| 组件 | 技术 | 版本 |
|------|------|------|
| 后端数据库客户端 | supabase-py | 2.x |
| 认证 | Supabase Auth | - |
| 环境变量 | python-dotenv | - |

### 3.2 集成架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Vue 3 前端     │────▶│  FastAPI 后端   │────▶│   Supabase      │
│                 │     │                 │     │  PostgreSQL     │
│ - 调用 API      │     │ - supabase-py   │     │  + Auth         │
│ - 处理 Token    │◄────│ - 业务逻辑      │◄────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 3.3 环境变量配置

**后端 `.env`**:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
```

**前端 `.env`**:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-publishable-key
```

## 4. 任务边界

### 4.1 本次要做
- Supabase 客户端集成
- 数据库表创建（提供 SQL 脚本）
- 后端路由切换到真实数据
- Supabase Auth 集成
- 环境变量配置

### 4.2 本次不做
- 数据迁移工具开发
- 数据库备份策略
- 性能优化
- 多环境配置

## 5. 关键假设

1. Supabase 项目已创建且可访问
2. service_role key 拥有完整数据库操作权限
3. 现有 API 接口格式保持不变
4. 用户接受短暂的服务中断（部署期间）

## 6. 风险与应对

| 风险 | 可能性 | 应对措施 |
|------|--------|----------|
| Supabase 连接失败 | 中 | 检查网络、Key 权限、URL 正确性 |
| 数据结构不兼容 | 低 | 严格按 DESIGN 文档执行 |
| 认证流程改动大 | 中 | 保持现有 JWT 结构，仅替换验证逻辑 |

---

**确认日期**: 2026-05-19
**所有不确定性已解决**: ✅
