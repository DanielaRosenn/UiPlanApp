# UiPlan Studio

A local-first visual builder for exploring and planning UiPath automation projects. UiPlan Studio indexes your project files, renders an interactive graph, and surfaces planning documents, skills, and review gates -- all from your browser.

## Architecture

```
api/          Python (FastAPI) backend -- project indexer, review engine, generation contracts
web/          React + Vite frontend -- interactive canvas, inspector, planning views
```

The **API** runs on `localhost:8000` and serves the project graph, context sources, CopilotKit actions, and generation package management. A `LocalOnlyMiddleware` rejects requests from non-loopback clients.

The **Web** frontend connects to the API and renders two main views:

- **Project Map** -- layered graph of files, skills, integrations, and Orchestrator resources
- **UiPlan Flow** -- planning-specific view with AS-IS / TO-BE canvases and task progress

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Quick start

### 1. Start the API

```bash
cd api
pip install -e ".[dev]"      # or: uv sync
uvicorn app.main:app --reload --port 8000
```

Verify it's running:

```bash
curl http://127.0.0.1:8000/health
```

### 2. Start the Web UI

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### 3. Map a project

1. Enter a folder path in the **source folder** input at the top bar.
2. Click **MAP** (or press Enter).
3. The indexer scans the folder for `.py`, `.xaml`, `.cs`, `.ts`, `.bpmn`, and other project files, then renders the graph.

## Views

### Project Map

Shows every indexed node grouped into columns by layer (RPA, Agent, App, Orchestrator, External, Skills). Use the toolbar to switch between:

- **FOCUS** mode -- starts from entry points; double-click to expand children.
- **FULL** mode -- shows all nodes at once.

Keyboard shortcuts:

| Key | Action |
|---|---|
| `/` | Focus the search bar |
| Arrow keys | Navigate between connected nodes |
| Enter | Drill into selected node's children |
| Escape | Deselect, or back out one level |

### UiPlan Flow

When the indexer finds a UiPlan bundle (a folder with `spec.md`, `plan.md`, and `tasks.md`), it appears in the left rail. Click it to enter the planning view:

- **AS-IS canvas** -- current-state business process flow with manual handoffs
- **TO-BE canvas** -- target-state architecture with workflow contracts, integration contracts, Orchestrator resources, and human-task gates
- **Task board** -- phase-based checklist with progress tracking

### Inspector (right panel)

Select any node or edge to see details:

- File path, code snippet, and language
- Connected nodes and edges
- Skill metadata (triggers, capabilities, guardrails)
- Library context search results

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Status and route listing |
| `/explorer/graph` | GET | Project graph for a worktree path |
| `/explorer/worktrees` | GET | Available worktrees / projects |
| `/explorer/knowledge` | GET | Ranked library + skill citations for a node |
| `/mapping/map-folder` | POST | Index a source folder |
| `/bundle/load` | POST | Load a UiPlan bundle (spec, plan, tasks) |
| `/diagram/load` | GET | Load saved diagram state |
| `/diagram/save` | POST | Save diagram state |
| `/review/run` | POST | Run acceptance review checks |
| `/context/sources` | GET | Available context sources (skills, library, documents) |
| `/generation/packages` | POST | Create a generation approval package |
| `/copilotkit/info` | GET | CopilotKit runtime metadata |

## Running tests

### API tests

```bash
cd api
pip install -e ".[dev]"
pytest tests/ -v
```

The `test_standalone_isolation.py` suite verifies the API starts and serves all endpoints without any external dependencies.

### Web tests

```bash
cd web
npm install
npm test
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `UIPLAN_PLANS_ROOT` | `<repo>/.cursor/plans` | Override the root directory for plan bundles |
| `UIPLAN_REPO_ROOT` | Auto-detected | Override the repo root for skill availability checks |

## Project structure

```
api/
  app/
    main.py                          FastAPI composition root
    explorer.py                      Project graph endpoints
    explorer_config.py               YAML config loader
    explorer_indexer.py              File-system indexer
    explorer_skills.py               Skill aggregation
    library_service.py               Library search (graceful degradation)
    review_service.py                Review engine (graceful degradation)
    copilot_runtime.py               CopilotKit actions
    diagram_service.py               Diagram persistence
    context_sources.py               Context source registry
    security.py                      Loopback-only middleware
    state.py                         Shared state and helpers
    schemas.py                       Pydantic models
    routers/                         Route handlers
    generation_contracts/            Approval package system
    project_graph/                   Typed graph models
  tests/                             Pytest suite
  pyproject.toml

web/
  src/
    App.tsx                          Root component
    components/
      Canvas.tsx                     SVG graph renderer
      UiplanCanvas.tsx               Planning-specific canvas
      AsIsCanvas.tsx                 Current-state view
      ToBeCanvas.tsx                 Target-state view
      Inspector.tsx                  Right-panel detail viewer
      LeftRail.tsx                   Left sidebar with filters
      Breadcrumb.tsx                 Drill-down navigation
    projectGraph/                    API client and types
    layout.ts                        Graph layout engine
    theme.ts                         Color palette and layer config
    telemetry.ts                     UX event tracking
  tests/                             Vitest + Playwright suites
  package.json
  vite.config.ts
```

## License

Internal use.
