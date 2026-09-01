id: new_key_format
title: The new sb_publishable_ / sb_secret_ key format
source_url: https://supabase.com/docs/guides/api/api-keys

Supabase is replacing the old JWT-based anon and service_role keys with
two new, non-expiring key types: publishable keys (prefixed sb_publishable_)
which are safe to expose in client-side code, and secret keys (prefixed
sb_secret_) which behave like the old service_role key and must never be
exposed to a browser or mobile client. Unlike the legacy keys, the new
ones are not JWTs, so they can be rotated individually without needing to
rotate your project's JWT signing secret, and rotating one key no longer
invalidates every other key on the project.
