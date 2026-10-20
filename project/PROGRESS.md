# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Session:** S1 of 5 (2026-10-20) is complete. The user has not reviewed the plans line by line; raise any plan concern at the start of S2.
- **Phase:** design done. No application code yet.

## Done

- Spec: `docs/specs/2026-10-20-data-hub-design.md`, approved by the user.
- Plans, one per session:
  - `docs/plans/2026-10-20-s2-foundation-import.md` (11 tasks)
  - `docs/plans/2026-10-20-s3-chatbot.md` (11 tasks)
  - `docs/plans/2026-10-20-s4-frontend.md` (8 tasks)
  - `docs/plans/2026-10-20-s5-benchmark-handoff.md` (6 tasks)
- `CLAUDE.md` is updated with the spec decisions and the session workflow (Rule #2).

## State of the code

Nothing to run yet. Local tooling is present: Docker 29.8 and Compose v5.6, Node 24.21, npm 11.19, Python 3.14 (the backend pins 3.12 through uv), uv 0.13.

## Next session: S2

- **Start:** open a new Claude Code conversation in the repo root (`SWE277P/`, where `.claude/settings.json` enables the plugins) and say: "Read project/CLAUDE.md, then follow Rule #2 and start S2."
- **Read:** `CLAUDE.md`, this file, the spec, and `docs/plans/2026-10-20-s2-foundation-import.md`. Don't read the other plans.
- **Do:** execute the S2 plan task by task with `superpowers:subagent-driven-development` (see "Decisions").
- **First step:** S2 Task 1 (backend skeleton). Before Task 2, the user must create `project/.env` from `.env.example`: Postgres passwords and a generated `HUB_SECRET_KEY`.
- **Exit:** A1, A2, A9 and the role tests pass, and `docker compose up` serves the placeholder UI.

## Open issues and blockers

- D1 (the LLM sees query results) is provisional and must be confirmed with the sponsor.
- ZotGPT Gateway base URL, JSON-mode support, and model names are unknown. Verify by 10/28. This is needed in S3.
- The sponsor's two separate dummy export files have not arrived. When they do, add them as extra import fixtures.
- The midterm is due 10/26. S4 Task 7 produces the screenshots. If S4 isn't done by then, take screenshots of the S2 import and API results instead.

## Decisions

- Spec D1–D10 (spec Section 2).
- The plans are split per session. Sample exports are copied into `backend/sample_data/` (synthetic), so the team repo is self-contained.
- Execution method for S2–S5: Subagent-driven (`superpowers:subagent-driven-development`). Each task gets a fresh implementer subagent and a fresh reviewer, so the session's main context holds only dispatches and reports. Recommended at the end of S1; the user can switch to Native (`superpowers:executing-plans`) at the start of any session.

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, wrote and got approval for the spec, wrote the S2–S5 plans, and chose subagent-driven execution.
