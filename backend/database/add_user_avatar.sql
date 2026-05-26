-- Add avatar storage for profile pictures.
-- Run this once in the Supabase SQL editor if the column does not exist yet.
ALTER TABLE public.users_data
ADD COLUMN IF NOT EXISTS avatar TEXT;
