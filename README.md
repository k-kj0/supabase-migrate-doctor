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

supabase-migrate scan ./my-project


- Walks the repo for legacy key literals, legacy env-var names, and
  already-migrated new-format keys
- Classifies each finding: CRITICAL (privileged key reachable from
  client code) / HIGH (privileged key, server-side) / MEDIUM (anon key)
  / INFO (already migrated)
- Explains each finding, citing the specific migration doc it's grounded in
- Exits non-zero on HIGH+ findings by default, so it can gate CI

Works with **zero API keys and zero required dependencies** - explanations
come from a deterministic, cited template by default. Set `GEMINI_API_KEY`
to upgrade explanations to Gemini-generated ones (still constrained to
only use the retrieved doc as context - see `supabase_migrate/rag.py`).

## Quickstart

```bash
pip install -e .
supabase-migrate scan ./path/to/repo
supabase-migrate scan ./path/to/repo --json --fail-on CRITICAL   # for CI
```

Try it against the bundled fixture repo first:

```bash
supabase-migrate scan tests/fixtures/sample_repo
```

Sample output:

Scanned 4 files.

CRITICAL: 1 HIGH: 2 MEDIUM: 1 INFO: 1

[CRITICAL] src/supabaseClient.js:6
process.env.SUPABASE_SERVICE_ROLE_KEY
-> A service_role-style identifier is referenced from what looks like client/frontend code...
-> A service_role (or its future sb_secret_ equivalent) referenced from code that runs in the
browser... (source: A privileged key referenced from client-facing code, https://supabase.com/...)


## Checking the tool against ground truth

`tests/fixtures/sample_repo` is a small hand-built repo with a known,
labeled set of findings (`tests/fixtures/expected.json`). Run:

```bash
python -m tests.eval
```

This is the piece I'd point to first in an interview: it's not "trust
that the tool works," it's a checkable precision/recall number.

Expected: 5 Found: 5 Matched: 5
Precision: 1.00 Recall: 1.00
All findings match expected ground truth exactly.


## Project layout

supabase_migrate/
scanner.py # finds legacy key literals / env-var names / new-format keys
classifier.py # risk-scores each finding
rag.py # retrieval + grounded explanation (offline or Gemini)
cli.py # supabase-migrate scan ...
knowledge_base/ # small, explicit, cited docs the explanations are grounded in
tests/
fixtures/ # hand-labeled sample repo + expected findings
eval.py # precision/recall check against the fixtures


## Sources for the migration timeline claims in this README

- https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys
- https://supabase.com/docs/guides/api/api-keys
- https://github.com/orgs/supabase/discussions/29260
