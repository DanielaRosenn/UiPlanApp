# UiPlan App

A local-first visual builder for exploring and planning UiPath automation projects. Indexes project files, renders an interactive graph, and surfaces planning documents, skills, and review gates -- all from your browser.

## Prerequisites

- Python 3.11+
- Node.js 18+

## Quick start

```bash
git clone --recurse-submodules https://github.com/DanielaRosenn/UiPlanApp.git
cd UiPlanApp
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init
```

### Start the API

```bash
cd api
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Start the Web UI

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Testing

### Run API tests

```bash
cd api
uv sync  # Install dependencies
uv run pytest tests/test_uiplan_integration.py -v
```

### Run full stack test

```bash
cd api
uv run python ../scripts/test_full_stack.py
```

This script:
1. Verifies templates are present and valid
2. Checks test bundle structure
3. Starts the API server
4. Tests health and bundle loading endpoints
5. Reports pass/fail status

## What it does

**Project Map** -- point at any folder and get a layered graph of files, skills, integrations, and Orchestrator resources grouped by layer (RPA, Agent, App, Orchestrator, External, Skills). Focus mode starts from entry points; Full mode shows everything.

**UiPlan Flow** -- when the indexer finds a plan bundle (`spec.md` + `plan.md` + `tasks.md`), you get AS-IS / TO-BE canvases and a phase-based task board.

**Inspector** -- select any node to see file path, code snippet, connected nodes, skill metadata, and library search results.

## Project structure

```
api/                        FastAPI backend (project indexer, review engine, generation contracts)
  app/                      Application code
  tests/                    Pytest suite
  pyproject.toml

web/                        React + Vite frontend (canvas, inspector, planning views)
  src/
  package.json

tools/uiplan/               CLI toolkit
  cli.py                    Entry point: python -m tools.uiplan ...
  paradigms.py              Paradigm detection and task blocks
  scaffold/                 Project scaffolding adapters (RPA, coded agent)
  validators/               Mermaid extraction, visual density checks
  generators/               Docs bundle generator

.cursor/skills/             Cursor agent skills (subagents)
  uiplan/                   Main skill -- routing and lifecycle
  uiplan-ground/            Discover project context before planning
  uiplan-spec/              Author spec.md (user stories, FRs, success criteria)
  uiplan-plan/              Author plan.md (architecture, component design)
  uiplan-tasks/             Author tasks.md (atomic implementation steps)
  uiplan-review/            Structured review gate
  uiplan-implement/         Execute accepted plan task-by-task
  uiplan-full/              End-to-end: ground through implement

templates/uiplan/           Spec/plan/tasks markdown templates
examples/uiplan-demo/       Example plan bundle
test-fixtures/              Golden fixtures for graph tests
skills/                     Git submodule -> github.com/UiPath/skills
docs/                       Documentation
```

## CLI tooling

Generate and validate UiPlan bundles from the terminal:

```bash
python -m tools.uiplan generate-docs my-project-slug
python -m tools.uiplan generate-docs my-project-slug --paradigm coded-agent --strict
python -m tools.uiplan validate-mermaid templates/uiplan/_spec-template.md
```

## Subagents

The `.cursor/skills/uiplan*/` directories define Cursor agent skills for the planning workflow:

| Skill | Purpose |
|---|---|
| `uiplan` | Routing and lifecycle orchestration |
| `uiplan-ground` | Discover project context, dependencies, constraints |
| `uiplan-spec` | Author spec.md |
| `uiplan-plan` | Author plan.md |
| `uiplan-tasks` | Author tasks.md |
| `uiplan-review` | Structured review gate |
| `uiplan-implement` | Execute accepted plan task-by-task |
| `uiplan-full` | End-to-end orchestrator |

Default flow: `ground -> spec -> plan -> tasks -> review -> accept -> implement`

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Status check |
| `/explorer/graph` | GET | Project graph for a worktree path |
| `/mapping/map-folder` | POST | Index a source folder |
| `/bundle/load` | POST | Load a UiPlan bundle |
| `/review/run` | POST | Run acceptance review checks |
| `/context/sources` | GET | Available context sources |
| `/generation/packages` | POST | Create a generation approval package |

## Tests

```bash
cd api && pip install -e ".[dev]" && pytest tests/ -v
cd web && npm install && npm test
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `UIPLAN_PLANS_ROOT` | `<repo>/.cursor/plans` | Root directory for plan bundles |
| `UIPLAN_REPO_ROOT` | Auto-detected | Repo root for skill availability checks |

## License

Internal use.
