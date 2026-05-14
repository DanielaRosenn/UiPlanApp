# UiPlan Studio

A local-first visual builder for exploring and planning UiPath automation projects. UiPlan Studio indexes your project files, renders an interactive graph, and surfaces planning documents, skills, and review gates -- all from your browser.

## Architecture

```
api/          Python (FastAPI) backend -- project indexer, review engine, generation contracts
web/          React + Vite frontend -- interactive canvas, inspector, planning views
skills/       Git submodule -> github.com/UiPath/skills (shared skill catalog)
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

### 0. Clone with submodules

```bash
git clone --recurse-submodules https://github.com/DanielaRosenn/UiPlanApp.git
cd UiPlanApp
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init
```

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
api/                                   FastAPI backend
  app/
    main.py                            Composition root
    explorer.py                        Project graph endpoints
    explorer_indexer.py                File-system indexer
    explorer_skills.py                 Skill aggregation
    library_service.py                 Library search (graceful degradation)
    review_service.py                  Review engine (graceful degradation)
    copilot_runtime.py                 CopilotKit actions
    context_sources.py                 Context source registry
    routers/                           Route handlers
    generation_contracts/              Approval package system
    project_graph/                     Typed graph models
  tests/                               Pytest suite
  pyproject.toml

web/                                   React + Vite frontend
  src/
    App.tsx                            Root component
    components/                        Canvas, Inspector, UiPlan views
    projectGraph/                      API client and types
    layout.ts                          Graph layout engine
  package.json
  vite.config.ts

tools/uiplan/                          CLI toolkit
  cli.py                               Entry point (python -m tools.uiplan ...)
  paradigms.py                         Paradigm detection and task block generation
  config.py                            Shared configuration
  scaffold/                            Project scaffolding adapters (RPA, coded agent)
  validators/                          Mermaid extraction, visual density checks
  generators/                          Docs bundle generator
  integrations/                        Skills bridge

.cursor/skills/                        Cursor agent skills (subagents)
  uiplan/                              Main UiPlan skill
  uiplan-ground/                       Grounding: discover project context before planning
  uiplan-spec/                         Spec authoring (user stories, FRs, success criteria)
  uiplan-plan/                         Plan authoring (architecture, component design)
  uiplan-tasks/                        Task authoring (atomic implementation steps)
  uiplan-review/                       Structured review gate
  uiplan-implement/                    Implementation execution from accepted plan
  uiplan-full/                         End-to-end orchestrator (ground -> implement)

extensions/skills/uiplan/              Skill extension overlay

templates/uiplan/                      Spec/plan/tasks templates and diagram patterns
examples/uiplan-demo/                  Example plan bundle (spec + plan + tasks)
test-fixtures/project-graph/           Golden fixtures for graph tests
docs/uiplan/                           Full documentation set
```

## CLI tooling

The `tools/uiplan/` package provides a local CLI for generating and validating UiPlan bundles outside of the Cursor/MCP workflow.

```bash
# Generate a plan bundle from templates
python -m tools.uiplan generate-docs my-project-slug

# With paradigm and strict validation
python -m tools.uiplan generate-docs my-project-slug --paradigm coded-agent --strict
```

The CLI detects project paradigm (RPA, coded agent, Maestro, etc.) and applies paradigm-specific task blocks, build loops, and deployment gates to the generated bundle.

## Subagents (Cursor skills)

The `.cursor/skills/uiplan*/` directories define agent skills that Cursor uses as specialized subagents in the planning workflow:

| Skill | Purpose |
|---|---|
| `uiplan` | Main entry -- routing and lifecycle orchestration |
| `uiplan-ground` | Discover project context, dependencies, and constraints before planning |
| `uiplan-spec` | Author spec.md: user stories, functional requirements, success criteria |
| `uiplan-plan` | Author plan.md: architecture, component design, integration contracts |
| `uiplan-tasks` | Author tasks.md: atomic implementation steps with checkboxes |
| `uiplan-review` | Structured review gate (spec coverage, citation resolution, constitution checks) |
| `uiplan-implement` | Execute accepted plan task-by-task |
| `uiplan-full` | End-to-end orchestrator: ground through implement in one pass |

The default flow: `ground -> spec -> plan -> tasks -> review -> accept -> implement`

## Skills (submodule)

The `skills/` directory is a git submodule pointing to [github.com/UiPath/skills](https://github.com/UiPath/skills) -- the shared UiPath skill catalog. After cloning, initialize it with:

```bash
git submodule update --init
```

The skill catalog includes UiPlan skills (`skills/skills/uiplan-*`) as well as skills for RPA, agents, Maestro, and other UiPath paradigms. The API's explorer and context-source endpoints use this catalog for skill aggregation and coverage mapping.

## License

Internal use.
