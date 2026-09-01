id: anon_key_migration
title: Migrating anon key usage
source_url: https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys

Any place your code reads the legacy anon key - typically an env var such
as SUPABASE_ANON_KEY or a framework-prefixed variant like
NEXT_PUBLIC_SUPABASE_ANON_KEY - should be pointed at the new
sb_publishable_ key instead. The client library call itself does not
change; only the value being passed to createClient() changes. Both key
types will work side by side during the transition window, but Supabase
has stated legacy keys will stop working once the deprecation period
ends, so a project left unmigrated will break outright rather than
degrade gracefully.
