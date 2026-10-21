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
| A4 | PENDING | |
| A10 | PENDING | |

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

No change was tried and reverted.

## Failure classes

Each failure is classed as a missing domain rule, a controlled-value gap, a few-shot gap, a JSON or
format failure, or question ambiguity.

No question failed in any run above, main or holdout, so there was nothing to class and no
tuning was aimed at a question; the two prompt changes are the S3 carry-overs. One holdout answer
(h10, 05:03, the second holdout run of that minute) passed on its second attempt, after one
repair. It is not a failure, and holdout answers are not used to choose prompt wording.

The holdout scoring 10/10 like the main set suggests the rules are not fitted only to the 20
questions, but both sets use one model and the same 293 sample rows from one term.

## Timings
