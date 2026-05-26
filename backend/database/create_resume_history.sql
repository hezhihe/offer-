-- 简历分析历史记录表
CREATE TABLE IF NOT EXISTS public.resume_history (
    id SERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL REFERENCES public.users_phone(phone) ON DELETE CASCADE,
    job_title TEXT NOT NULL,
    company TEXT,
    original_jd TEXT NOT NULL,
    original_resume TEXT NOT NULL,
    match_score INTEGER NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    keywords JSONB NOT NULL DEFAULT '[]',
    reconstructed_resume TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_resume_history_user_phone ON public.resume_history(user_phone);
CREATE INDEX IF NOT EXISTS idx_resume_history_created_at ON public.resume_history(created_at DESC);

-- 启用 RLS
ALTER TABLE public.resume_history ENABLE ROW LEVEL SECURITY;

-- 策略：用户只能查看自己的历史记录
CREATE POLICY "Users can view own resume history" ON public.resume_history
    FOR SELECT USING (user_phone = current_setting('app.current_user_phone', true));

-- 策略：用户只能插入自己的记录
CREATE POLICY "Users can insert own resume history" ON public.resume_history
    FOR INSERT WITH CHECK (user_phone = current_setting('app.current_user_phone', true));

COMMENT ON TABLE public.resume_history IS '用户简历分析历史记录';
