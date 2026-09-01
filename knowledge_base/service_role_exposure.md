id: service_role_exposure
title: A privileged key referenced from client-facing code
source_url: https://supabase.com/docs/guides/database/postgres/row-level-security

A service_role (or its future sb_secret_ equivalent) referenced from
code that runs in the browser or gets bundled into a client build is a
distinct problem from the key migration itself: it means Row Level
Security - the only authorization boundary Supabase relies on for
client-facing traffic - is effectively bypassed for anyone who inspects
the shipped JS bundle. This should be fixed immediately regardless of
the migration timeline: move the privileged call behind a server-side
route or edge function, and only ever send the publishable key to the
client.
