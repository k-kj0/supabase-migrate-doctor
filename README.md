# supabase-migrate-doctor

A CLI that scans a codebase for legacy Supabase API key usage, tells you
exactly how risky each usage is, and explains what to do about it -
grounded in Supabase's own migration docs, with a citation on every
explanation.

## Why this exists

Supabase is retiring its legacy JWT-based `anon` / `service_role` keys in
favor of new `sb_publishable_` / `sb_secret_` keys. New projects created
after November 2025 no longer get legacy keys at all, and Supabase's own
docs state the legacy keys are planned for deprecation and removal by
the end of 2026. That means every existing project - and every tutorial,
Stack Overflow answer, and copy-pasted `.env.example` referencing the
old key names - is on a clock.

Two problems compound this:
1. **It's not just a find-and-replace.** The same pattern (a legacy key
   reference) can mean "safe, just needs migrating" or "privileged key
   is one bundler config away from shipping to the browser," and only
   the second one is an emergency.
2. **Generic AI assistance is a bad fit here.** A model's training data
   almost certainly reflects the *old* key system as the "correct" one,
   which means asking a general chatbot for help can produce confidently
   wrong migration advice. Any explanation this tool gives is grounded
   in a small, explicit knowledge base (see `knowledge_base/`) with a
   source URL attached - not the model's memory.

## What it does
