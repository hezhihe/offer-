-- Store per-question interview feedback for history detail review.
ALTER TABLE public.interview_history
ADD COLUMN IF NOT EXISTS feedbacks JSONB NOT NULL DEFAULT '[]';
