import { createClient } from '@supabase/supabase-js'

// Bug: this file ships to the browser, but it reads the service role key.
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)
