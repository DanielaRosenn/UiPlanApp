# Tasks: Test UiPlan Integration

> **Grounding:** `[skill:uipath-planner]`
> **Input**: `./spec.md`, `./plan.md`

**Format**: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [x] T001 [P] [US1] Create test bundle with .meta.yaml, spec.md, plan.md, tasks.md

## Phase 2: Tests

- [x] T010 [US1] Write pytest test for /health endpoint
- [x] T011 [US1] Write pytest test for /bundle/load endpoint
- [ ] T012 [US1] Write integration test for full stack (API + frontend)

## Phase 3: Verification

- [ ] T030 Run `uv run pytest` and verify all tests pass
- [ ] T031 Start API and frontend, verify bundle loads in browser

## Dependencies & Execution Order

T001 -> T010 -> T011 -> T012 -> T030 -> T031
