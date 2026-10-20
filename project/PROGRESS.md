# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Session:** S1 of 5 (2026-10-20), in progress
- **Phase:** design. No application code yet.

## Done

- The design spec is written and committed: `docs/specs/2026-10-20-data-hub-design.md`. It is waiting for the user's review.
- `CLAUDE.md` is updated with the spec decisions (stack, LLM profiles, provisional privacy rule, P1 extension points) and the session workflow.

## State of the code

Nothing to run yet. Local tooling is checked and present: Docker 29.8 and Compose v5.6, Node 24.21, npm 11.19, Python 3.14 (the backend will pin 3.12 through uv), uv 0.13.

## Next steps

1. **S1 (rest):** the user reviews the spec. Then write the implementation plan in `docs/plans/` and commit it.
2. **S2:** scaffold, DB schema and roles, import pipeline, identity linking, and dataset export (spec Section 15).

## Open issues and blockers

- D1 (the LLM sees query results) is provisional and must be confirmed with the sponsor.
- ZotGPT Gateway base URL, JSON-mode support, and model names are still unknown. Verify by 10/28.
- The sponsor's two separate dummy export files have not arrived. When they do, add them as extra import fixtures.

## Decisions this session

All are recorded in spec Section 2 (D1–D10).

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, and wrote the spec.
