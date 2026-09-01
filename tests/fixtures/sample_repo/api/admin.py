import os
from supabase import create_client

# Correct usage: server-side only, but still on the legacy key name -
# still needs migrating before the deprecation deadline.
supabase_admin = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)
