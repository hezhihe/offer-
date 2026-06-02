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

CREATE TABLE IF NOT EXISTS public.job_browse_history (
  user_phone TEXT NOT NULL,
  job_id BIGINT NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
  viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_phone, job_id)
);

CREATE INDEX IF NOT EXISTS idx_job_browse_history_user_viewed
ON public.job_browse_history(user_phone, viewed_at DESC);
