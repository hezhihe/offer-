-- Track the latest successful login time for each account.
ALTER TABLE public.users_data
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;

-- Keep this available for older tables that may have been created before updated_at existed.
ALTER TABLE public.users_data
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
