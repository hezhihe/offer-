-- 面试历史记录表
CREATE TABLE IF NOT EXISTS public.interview_history (
    id SERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL,
    job_type TEXT NOT NULL,
    questions JSONB NOT NULL DEFAULT '[]',
    answers JSONB NOT NULL DEFAULT '[]',
    scores JSONB NOT NULL DEFAULT '[]',
    total_score INTEGER NOT NULL,
    avg_score REAL NOT NULL,
    advice TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_interview_history_user_phone ON public.interview_history(user_phone);
CREATE INDEX IF NOT EXISTS idx_interview_history_created_at ON public.interview_history(created_at DESC);

-- 启用 RLS
ALTER TABLE public.interview_history ENABLE ROW LEVEL SECURITY;

-- 策略：允许查看和插入
CREATE POLICY "Users can view own interview history" ON public.interview_history
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own interview history" ON public.interview_history
    FOR INSERT WITH CHECK (true);

COMMENT ON TABLE public.interview_history IS '用户面试模拟历史记录';
