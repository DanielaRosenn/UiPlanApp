"""End-to-end tests for UiPlan app with templates.

This test suite verifies:
1. API health and core endpoints work
2. Bundle loading works with UiPlan template structure
3. Templates contain expected sections and structure
4. The app can serve bundles to the frontend
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Test fixtures path relative to api/tests
TEST_FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "test-fixtures"
# Bundle must be under .cursor/plans for security constraints
REPO_ROOT = Path(__file__).resolve().parents[2]
UIPLAN_BUNDLE_PATH = REPO_ROOT / ".cursor" / "plans" / "test-bundle"
TEMPLATES_PATH = REPO_ROOT / "templates" / "uiplan"

# Set UIPLAN_PLANS_ROOT to the correct location for tests
os.environ["UIPLAN_PLANS_ROOT"] = str(REPO_ROOT / ".cursor" / "plans")

# Now import app after setting the env var
from app.main import app


@pytest.fixture
def client():
    """Create a test client with proper localhost headers."""
    return TestClient(app, headers={"host": "127.0.0.1:8000"})


class TestHealthEndpoint:
    """Test the health endpoint works correctly."""

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    def test_health_lists_required_routes(self, client):
        resp = client.get("/health")
        body = resp.json()
        routes = body["routes"]
        # Core bundle routes must be present
        assert "/bundle/load" in routes
        assert "/context/sources" in routes


class TestBundleLoading:
    """Test bundle loading with UiPlan template structure."""

    def test_bundle_load_returns_all_documents(self, client):
        """Verify /bundle/load returns spec, plan, and tasks."""
        # Use relative path (bundle_root is resolved relative to .cursor/plans)
        resp = client.get("/bundle/load", params={"bundle_root": "test-bundle"})
        assert resp.status_code == 200
        body = resp.json()
        
        assert body["slug"] == "test-uiplan-bundle"
        assert body["status"] == "draft"
        assert "documents" in body
        
        docs = body["documents"]
        assert "spec.md" in docs
        assert "plan.md" in docs
        assert "tasks.md" in docs

    def test_bundle_spec_has_required_sections(self, client):
        """Verify spec.md contains expected UiPlan template sections."""
        resp = client.get("/bundle/load", params={"bundle_root": "test-bundle"})
        body = resp.json()
        spec = body["documents"]["spec.md"]
        
        # Check for key spec sections
        assert "# Feature Specification:" in spec
        assert "## User Scenarios" in spec or "## Summary" in spec
        assert "## Requirements" in spec
        assert "**FR-001**" in spec  # Functional requirement marker

    def test_bundle_plan_has_required_sections(self, client):
        """Verify plan.md contains expected UiPlan template sections."""
        resp = client.get("/bundle/load", params={"bundle_root": "test-bundle"})
        body = resp.json()
        plan = body["documents"]["plan.md"]
        
        # Check for key plan sections
        assert "# Implementation Plan:" in plan
        assert "## Project Inventory" in plan or "## Summary" in plan
        assert "## CLI Command Matrix" in plan or "## Workflow Catalog" in plan

    def test_bundle_tasks_has_required_sections(self, client):
        """Verify tasks.md contains expected UiPlan template sections."""
        resp = client.get("/bundle/load", params={"bundle_root": "test-bundle"})
        body = resp.json()
        tasks = body["documents"]["tasks.md"]
        
        # Check for key tasks sections
        assert "# Tasks:" in tasks
        assert "## Phase" in tasks
        assert "- [" in tasks  # Task checkbox markers

    def test_bundle_load_nonexistent_returns_error(self, client):
        """Verify loading a nonexistent bundle returns an error (403 or 404)."""
        # Relative path (within allowed root) that doesn't exist -> 404
        resp = client.get("/bundle/load", params={"bundle_root": "nonexistent-bundle"})
        assert resp.status_code == 404


class TestTemplatesPresence:
    """Test that UiPlan templates exist and have expected structure."""

    def test_spec_template_exists(self):
        """Verify _spec-template.md exists."""
        spec_template = TEMPLATES_PATH / "_spec-template.md"
        assert spec_template.exists(), f"Missing: {spec_template}"

    def test_plan_template_exists(self):
        """Verify _plan-template.md exists."""
        plan_template = TEMPLATES_PATH / "_plan-template.md"
        assert plan_template.exists(), f"Missing: {plan_template}"

    def test_tasks_template_exists(self):
        """Verify _tasks-template.md exists."""
        tasks_template = TEMPLATES_PATH / "_tasks-template.md"
        assert tasks_template.exists(), f"Missing: {tasks_template}"

    def test_spec_template_has_placeholders(self):
        """Verify spec template contains expected placeholders."""
        content = (TEMPLATES_PATH / "_spec-template.md").read_text(encoding="utf-8")
        # Key placeholders from the template
        assert "{{TITLE}}" in content
        assert "{{GROUNDING_CITATIONS}}" in content
        assert "## User Scenarios" in content
        assert "## Requirements" in content

    def test_plan_template_has_placeholders(self):
        """Verify plan template contains expected placeholders."""
        content = (TEMPLATES_PATH / "_plan-template.md").read_text(encoding="utf-8")
        assert "{{TITLE}}" in content
        assert "{{GROUNDING_CITATIONS}}" in content
        assert "## Project Inventory" in content
        assert "## CLI Command Matrix" in content

    def test_tasks_template_has_placeholders(self):
        """Verify tasks template contains expected placeholders."""
        content = (TEMPLATES_PATH / "_tasks-template.md").read_text(encoding="utf-8")
        assert "{{TITLE}}" in content
        assert "{{GROUNDING_CITATIONS}}" in content
        assert "## Phase 1" in content
        assert "[skill:" in content  # Skill routing tags


class TestContextSources:
    """Test context sources endpoint for Copilot integration."""

    def test_context_sources_returns_categories(self, client):
        resp = client.get("/context/sources")
        assert resp.status_code == 200
        body = resp.json()
        assert "categories" in body


class TestExplorerEndpoints:
    """Test explorer endpoints for project graph visualization."""

    def test_explorer_graph_requires_worktree(self, client):
        """Verify /explorer/graph requires a worktree parameter."""
        resp = client.get("/explorer/graph")
        # Should return 422 for missing required param
        assert resp.status_code == 422

    def test_explorer_graph_with_valid_worktree(self, client):
        """Test loading project graph with a valid worktree."""
        # Use the test-fixtures directory as a simple worktree
        resp = client.get("/explorer/graph", params={"worktree": str(TEST_FIXTURES_ROOT)})
        # Should either succeed or return a handled error (not 500)
        assert resp.status_code != 500


class TestCopilotKitEndpoints:
    """Test CopilotKit runtime endpoints."""

    def test_copilotkit_info(self, client):
        resp = client.get("/copilotkit/info")
        assert resp.status_code == 200


class TestDiagramEndpoints:
    """Test diagram loading endpoints."""

    def test_diagram_load_with_bundle(self, client):
        """Test loading diagrams from a bundle."""
        resp = client.get(
            "/diagram/load",
            params={
                "bundle_root": "test-bundle",
                "document_name": "plan.md",
            },
        )
        # Should return 200 with diagram data (nodes/edges structure)
        assert resp.status_code == 200
        body = resp.json()
        # Diagram endpoint returns nodes/edges structure or diagrams list
        assert "nodes" in body or "diagrams" in body


# Integration test that requires running servers
class TestFullStackIntegration:
    """Integration tests that verify the full stack works together.
    
    These tests are marked as slow and may be skipped in CI unless explicitly run.
    """

    @pytest.mark.slow
    def test_api_server_starts_and_responds(self):
        """Test that the API server can start and respond to health checks.
        
        This test actually starts a uvicorn server subprocess.
        """
        import socket
        
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        
        # Start the server
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "127.0.0.1",
                "--port", str(port),
            ],
            cwd=Path(__file__).resolve().parents[1],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Test health endpoint
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                assert resp.status == 200
                data = resp.read().decode("utf-8")
                assert '"status":"ok"' in data or '"status": "ok"' in data
        finally:
            proc.terminate()
            proc.wait(timeout=5)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
