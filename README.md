## Real-world testing

Beyond the hand-labeled fixture (see "Checking the tool against ground truth" above),
I had three people run the scanner against real, unmodified public repositories in
their own GitHub Codespaces, independent of my own environment. This is informal
manual testing, not a benchmark or a formal user study, but it's real usage against
code none of us wrote.

**6 scans, 5 distinct public repos, 3 testers:**

| Repo | Files | Critical | High | Medium | Info |
|---|---|---|---|---|---|
| permitio/supabase-fine-grained-authorization | 27 | 0 | 0 | 4 | 0 |
| John-Weeks-Dev/ebay-clone | 51 | 0 | 0 | 1 | 0 |
| supabase-community/nextjs-subscription-payments | 67 | 1 | 4 | 4 | 0 |
| salmandotweb/nextjs-supabase-boilerplate | 43 | 1 | 1 | 1 | 0 |
| KolbySisk/next-supabase-stripe-starter (2 runs) | 64 | 2 | 1 | 3 | 0 |

Across the 5 distinct repos, the tool found legacy-key references ranging from
minor (a `.env.example` placeholder) to CRITICAL (a privileged key reachable from
client-side code), which matches the range the classifier is designed to catch.
The stripe-starter repo was scanned twice by the same tester and returned identical
counts both times — a small but real reproducibility check.

Full JSON output for every run is in `scan_logs/`; `scan_logs/summary.csv` has one
row per scan with a timestamp.

### Problems found and fixed during testing

Testing against three independent environments surfaced real setup issues that
didn't show up when I was the only person running the tool:

1. **`ModuleNotFoundError: No module named 'supabase_migrate.cost_tracker'`**
   A tester's Codespace had cloned the repo before `cost_tracker.py` was pushed to
   `main`. Fixed by pushing the file and having testers run `git pull` before
   re-installing.
2. **`bash: run_and_log.sh: No such file or directory`**
   The logging script is created via a pasted heredoc block; if the paste is
   interrupted partway, the file never gets written. Fixed by having testers
   re-paste the full block in one go and confirm with `ls` before running it.
3. **`fatal: destination path '/tmp/testrepoX' already exists and is not an empty
   directory`**
   A tester re-ran the setup commands, including `git clone`, into a folder that
   already held a previous clone. Fixed by reusing the existing folder instead of
   re-cloning — which is how the reproducibility check above happened.

None of these were bugs in the scanner or classifier logic itself — all three were
environment/setup friction, which is exactly the kind of thing that's invisible
until someone other than the author runs the tool.

**Honest limitations of this round of testing:** 5 repos is a small, non-random
sample, all Next.js/JS-ecosystem projects. It doesn't cover other frameworks
(Flutter, plain Python backends, etc.), and testers followed a script I wrote
rather than exploring freely. I'm treating this as a first real-world pass, not
a validation study.
