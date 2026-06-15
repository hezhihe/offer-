-- User feedback submitted from the profile page.
CREATE TABLE IF NOT EXISTS public.user_feedback (
    id BIGSERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL,
    content TEXT NOT NULL CHECK (char_length(trim(content)) > 0 AND char_length(content) <= 2000),
    contact TEXT,
    page_url TEXT,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'closed')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_feedback_user_phone ON public.user_feedback(user_phone);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON public.user_feedback(created_at DESC);

ALTER TABLE public.user_feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "No direct client access to user feedback" ON public.user_feedback;
CREATE POLICY "No direct client access to user feedback" ON public.user_feedback
    FOR ALL
    USING (false)
    WITH CHECK (false);

COMMENT ON TABLE public.user_feedback IS 'User-submitted product feedback from Offer Compass profile page.';
COMMENT ON COLUMN public.user_feedback.user_phone IS 'Phone number from Offer Compass JWT user identity.';
COMMENT ON COLUMN public.user_feedback.content IS 'Feedback content submitted by the user.';
COMMENT ON COLUMN public.user_feedback.contact IS 'Optional contact information supplied by the user.';
COMMENT ON COLUMN public.user_feedback.page_url IS 'Client page URL where the feedback was submitted.';
COMMENT ON COLUMN public.user_feedback.status IS 'Internal handling status for feedback triage.';
