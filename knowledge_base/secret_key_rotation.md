id: secret_key_rotation
title: Migrating and rotating the service_role / secret key
source_url: https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys

The legacy service_role key is a long-lived JWT that grants full,
row-level-security-bypassing access to your database - it should only
ever live in server-side environments (backend services, edge functions,
CI secrets), never in anything shipped to a client. When migrating,
replace it with the new sb_secret_ key in every server-side location it
appears, then treat the old value as compromised and rotate it from the
project's API settings rather than leaving it active "just in case." A
key that only exists as an unused legacy credential is still a live
credential until it's explicitly revoked.
