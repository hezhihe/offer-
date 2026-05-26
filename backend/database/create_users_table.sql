-- 鐢ㄦ埛琛紙鏀寔鎵嬫満鍙风櫥褰曪級
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

-- 鍒涘缓绱㈠紩
CREATE INDEX IF NOT EXISTS idx_users_data_phone ON public.users_data(phone);

-- 鍚敤 RLS
ALTER TABLE public.users_data ENABLE ROW LEVEL SECURITY;

-- 鍒涘缓绛栫暐锛氱敤鎴峰彧鑳芥煡鐪嬭嚜宸辩殑鏁版嵁
CREATE POLICY "Users can view own data" ON public.users_data
    FOR SELECT USING (true);  -- 鏆傛椂鍏佽鎵€鏈夋煡璇紝鍚庣浼氭帶鍒?
-- 鍒涘缓绛栫暐锛氬厑璁告敞鍐岋紙鎻掑叆锛?CREATE POLICY "Allow registration" ON public.users_data
    FOR INSERT WITH CHECK (true);

COMMENT ON TABLE public.users_data IS '鎵嬫満鍙风櫥褰曠敤鎴疯〃';
