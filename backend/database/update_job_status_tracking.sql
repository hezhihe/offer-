-- Add lightweight lifecycle tracking for recruitment jobs.
-- active: visible by default
-- closed: removed/down from the source but kept for history
-- expired: optional explicit expired state; backend can also derive this from deadline

ALTER TABLE public.jobs
ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active'
CHECK (status IN ('active', 'closed', 'expired'));

ALTER TABLE public.jobs
ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE public.jobs
ADD COLUMN IF NOT EXISTS source_url TEXT;

CREATE INDEX IF NOT EXISTS idx_jobs_status_deadline
ON public.jobs(status, deadline);
