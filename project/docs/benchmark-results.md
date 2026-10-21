# Benchmark results

The record of the chatbot benchmark (spec 8.2, 14 A3/A4) and the S5 timing check (A10). The 20
questions are in `backend/benchmark/questions.yaml`; the 10 held-out questions, written before
any prompt tuning, are in `backend/benchmark/holdout.yaml`. Run reports go to
`backend/benchmark/reports/` and are not committed; the numbers that matter are copied here.

## Acceptance summary

The status cell is exactly `PASS`, `FAIL` or `PENDING`.

| Acceptance | Status | Evidence |
|---|---|---|
| A3 | PASS | 20/20 on two consecutive runs on prompt 2026-10-29.4 (DeepSeek, deepseek-flash, 2026-10-21 05:03 and 05:04); holdout 10/10 on three runs of the same prompt |
| A4 | PASS | The same benchmark ran against two profiles with no code change: DeepSeek (deepseek, deepseek-flash) 20/20 main and 10/10 holdout, and DeepSeek Pro (deepseek, deepseek-v4-pro) 19/20 main and 10/10 holdout, both on prompt 2026-10-29.4 (2026-10-21) |
| A10 | PASS | Question to downloaded Excel on a cold-started api, profile DeepSeek (deepseek-flash), 2026-10-21 05:59: q01 4.4 s, q04 5.4 s, q14 5.4 s (limit 60 s); see Timings |

## Runs

| Date | Profile (preset, model) | Prompt version | Set | Score | Failing ids |
|---|---|---|---|---|---|
| 2026-10-21 04:54 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.2 | main | 20/20 | none |
| 2026-10-21 04:54 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.2 | holdout | 10/10 | none |
| 2026-10-21 04:54 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.2 | holdout | 10/10 | none |
| 2026-10-21 04:55 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.2 | main | 20/20 | none |
| 2026-10-21 04:55 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.2 | main | 20/20 | none |
| 2026-10-21 04:55 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.2 | holdout | 10/10 | none |
| 2026-10-21 04:57 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.3 | main | 20/20 | none |
| 2026-10-21 04:57 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.3 | holdout | 10/10 | none |
| 2026-10-21 05:01 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | main | 20/20 | none |
| 2026-10-21 05:01 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | holdout | 10/10 | none |
| 2026-10-21 05:03 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | main | 20/20 | none |
| 2026-10-21 05:03 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | holdout | 10/10 | none |
| 2026-10-21 05:03 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | holdout | 10/10 | none |
| 2026-10-21 05:04 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | main | 20/20 | none |
| 2026-10-21 05:04 | DeepSeek (deepseek, deepseek-flash) | 2026-10-29.4 | holdout | 10/10 | none |
| 2026-10-21 05:09 | DeepSeek Pro (deepseek, deepseek-v4-pro) | 2026-10-29.4 | main | 19/20 | q15 |
| 2026-10-21 05:13 | DeepSeek Pro (deepseek, deepseek-v4-pro) | 2026-10-29.4 | holdout | 10/10 | none |

Every run used `--today 2026-11-02` (the default). By prompt version:

- **2026-10-29.2** (the S3 prompt): the baseline, three runs of each set. The last S3 run (2026-10-21
  00:59, the committed report) also scored 20/20.
- **2026-10-29.3**: "students" with no named affiliation and blank groups (no school, department or
  affiliation) are now stated in the assumptions. Kept: neither score dropped. Three extra main
  spot checks of q01, q10 and q20 only (3/3 each, not in the table) stated the "students" reading
  in 8 of 9 answers.
- **2026-10-29.4**: "this term", "last term" and "the most recent term" are read against today and
  the known terms, which are now listed oldest first. Kept: neither score dropped. The two runs at
  05:03 and 05:04 are the stability runs, with three holdout runs on the same prompt. The sample
  data has one term (Fall 2026), so the benchmark does not exercise "last term"; an ad-hoc check
  outside the benchmark gave a clarifying question for "last term" on 2026-11-02 (no earlier
  data) and Fall 2026 for "last quarter" on 2027-01-15.
- **Second profile (A4)**: profile `DeepSeek Pro` (same preset and base URL as DeepSeek, model
  `deepseek-v4-pro`, result sharing off, the same stored key) ran the main and holdout sets once
  each on 2026-10-29.4 with no code change. No timeouts, JSON-mode rejections or unknown-model
  errors. Only the primary profile has to reach 18/20. q15 failed on DeepSeek Pro (see below).

No change was tried and reverted.

## Failure classes

Each failure is classed as a missing domain rule, a controlled-value gap, a few-shot gap, a JSON or
format failure, or question ambiguity.

Only one question failed in any run above, main or holdout: q15 on DeepSeek Pro (below). The
runs on the primary DeepSeek profile (deepseek-flash) never failed a question, so no tuning was aimed at a question; the two prompt
changes are the S3 carry-overs. One holdout answer (h10, 05:03, the second holdout run of that
minute) passed on its second attempt, after one repair. It is not a failure, and holdout answers
are not used to choose prompt wording.

The failure, q15 on DeepSeek Pro (05:09), is question ambiguity: the model counted unique
people (`COUNT(DISTINCT person_key)`) among virtual-event attendees, while the reference counts
attendance records. It returned 1 row in 1 attempt, so it is a different reading, not a
format failure. No prompt change was made for it, since the other profile passes it and the
benchmark is not tuned to one question.

The holdout scoring 10/10 like the main set suggests the rules are not fitted only to the 20
questions, but both sets use one model and the same 293 sample rows from one term.

## Timings

A10 (spec 14): the time from pressing Enter on a question to the `.xlsx` download event, in a new
chat each, on the main stack with the samples loaded. `docker compose restart api` ran first, so
q01 is a cold start. Run with `HUB_E2E_PROFILE="DeepSeek" npm run e2e:timing` (Playwright
`e2e/timing.spec.ts`), 3 passed, 2026-10-21 05:59, profile DeepSeek (deepseek, deepseek-flash).

| Question | Time (ms) | Limit |
|---|---|---|
| q01 | 4367 | 60000 |
| q04 | 5359 | 60000 |
| q14 | 5381 | 60000 |

Two more runs of the same spec, 3 passed each:

| Run | Profile | q01 (ms) | q04 (ms) | q14 (ms) |
|---|---|---|---|---|
| 2026-10-21 06:00, controller's re-run | DeepSeek (deepseek, deepseek-flash) | 4377 | 6374 | 4865 |
| 2026-10-21 06:01 | DeepSeek Pro (deepseek, deepseek-v4-pro) | 10488 | 5395 | 16398 |

All are under the 60000 ms limit. The slowest, q14 on DeepSeek Pro at 16.4 s, is about three times
the flash model's time for the same question (about 5 s).

Log scan after the first run: `docker compose logs api nginx db | grep -E "sk-|@uci\.edu" | wc -l` gave 0
(also 0 when scoped with `--since` the start of the run).
