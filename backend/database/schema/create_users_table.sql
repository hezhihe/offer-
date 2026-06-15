-- 用户表（支持手机号登录）
CREATE TABLE IF NOT EXISTS public.users_data (
    id SERIAL PRIMARY KEY,
    phone TEXT UNIQUE NOT NULL,
    email TEXT,
    avatar TEXT,
    hashed_password TEXT NOT NULL,
    nickname TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_data_phone ON public.users_data(phone);

-- 启用 RLS
ALTER TABLE public.users_data ENABLE ROW LEVEL SECURITY;

-- 创建策略：当前后端使用服务端权限控制访问，这里暂时允许查询。
CREATE POLICY "Users can view own data" ON public.users_data
    FOR SELECT USING (true);

-- 创建策略：允许注册插入用户数据。
CREATE POLICY "Allow registration" ON public.users_data
    FOR INSERT WITH CHECK (true);

COMMENT ON TABLE public.users_data IS '手机号登录用户表';
