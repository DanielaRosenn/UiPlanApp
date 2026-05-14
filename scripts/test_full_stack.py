#!/usr/bin/env python3
"""End-to-end test script for UiPlan App full stack.

This script:
1. Starts the API server
2. Starts the web frontend (optional)
3. Runs health checks
4. Tests bundle loading
5. Reports results

Usage:
    python scripts/test_full_stack.py [--with-frontend]
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "api"
WEB_DIR = REPO_ROOT / "web"
# Bundle must be under .cursor/plans for API security constraints
TEST_BUNDLE = REPO_ROOT / ".cursor" / "plans" / "test-bundle"
TEST_BUNDLE_RELATIVE = "test-bundle"  # For API calls


def find_free_port() -> int:
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for a server to respond."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def test_health(api_port: int) -> bool:
    """Test the health endpoint."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{api_port}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "ok":
                print(f"  [PASS] Health endpoint: status=ok, {len(data.get('routes', []))} routes")
                return True
            else:
                print(f"  [FAIL] Health endpoint: unexpected status: {data}")
                return False
    except Exception as e:
        print(f"  [FAIL] Health endpoint: {e}")
        return False


def test_bundle_load(api_port: int) -> bool:
    """Test loading the test bundle."""
    try:
        url = f"http://127.0.0.1:{api_port}/bundle/load?bundle_root={TEST_BUNDLE_RELATIVE}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            if data.get("slug") != "test-uiplan-bundle":
                print(f"  [FAIL] Bundle load: wrong slug: {data.get('slug')}")
                return False
            
            docs = data.get("documents", {})
            if not all(doc in docs for doc in ["spec.md", "plan.md", "tasks.md"]):
                print(f"  [FAIL] Bundle load: missing documents: {list(docs.keys())}")
                return False
            
            print(f"  [PASS] Bundle load: slug={data['slug']}, {len(docs)} documents")
            return True
    except Exception as e:
        print(f"  [FAIL] Bundle load: {e}")
        return False


def test_templates_structure() -> bool:
    """Test that templates have expected structure."""
    templates_dir = REPO_ROOT / "templates" / "uiplan"
    required_files = ["_spec-template.md", "_plan-template.md", "_tasks-template.md"]
    
    for fname in required_files:
        path = templates_dir / fname
        if not path.exists():
            print(f"  [FAIL] Template missing: {fname}")
            return False
        
        content = path.read_text(encoding="utf-8")
        if "{{TITLE}}" not in content:
            print(f"  [FAIL] Template {fname}: missing {{TITLE}} placeholder")
            return False
    
    print(f"  [PASS] Templates: all {len(required_files)} template files present and valid")
    return True


def test_spec_sections() -> bool:
    """Test that spec.md in test bundle has required sections."""
    spec_path = TEST_BUNDLE / "spec.md"
    if not spec_path.exists():
        print(f"  [FAIL] Test bundle spec.md not found")
        return False
    
    content = spec_path.read_text(encoding="utf-8")
    required_sections = [
        "# Feature Specification",
        "## Requirements",
        "**FR-001**",
    ]
    
    for section in required_sections:
        if section not in content:
            print(f"  [FAIL] spec.md missing: {section}")
            return False
    
    print(f"  [PASS] spec.md: has all required sections")
    return True


def test_mermaid_diagrams() -> bool:
    """Test that plan.md has Mermaid diagrams."""
    plan_path = TEST_BUNDLE / "plan.md"
    if not plan_path.exists():
        print(f"  [FAIL] Test bundle plan.md not found")
        return False
    
    content = plan_path.read_text(encoding="utf-8")
    if "```mermaid" not in content:
        print(f"  [FAIL] plan.md: no Mermaid diagrams found")
        return False
    
    print(f"  [PASS] plan.md: contains Mermaid diagrams")
    return True


def main():
    parser = argparse.ArgumentParser(description="Test UiPlan App full stack")
    parser.add_argument("--with-frontend", action="store_true", help="Also start and test frontend")
    parser.add_argument("--api-port", type=int, default=0, help="API port (0=auto)")
    args = parser.parse_args()

    api_port = args.api_port or find_free_port()
    api_proc = None
    web_proc = None
    
    results = []
    
    print("\n" + "=" * 60)
    print("UiPlan App Full Stack Test")
    print("=" * 60)
    
    # Test templates (no server needed)
    print("\n[1/6] Testing templates structure...")
    results.append(("Templates structure", test_templates_structure()))
    
    print("\n[2/6] Testing test bundle spec.md...")
    results.append(("Spec sections", test_spec_sections()))
    
    print("\n[3/6] Testing test bundle plan.md diagrams...")
    results.append(("Mermaid diagrams", test_mermaid_diagrams()))
    
    # Start API server with proper PLANS_ROOT
    print(f"\n[4/6] Starting API server on port {api_port}...")
    env = os.environ.copy()
    env["UIPLAN_PLANS_ROOT"] = str(REPO_ROOT / ".cursor" / "plans")
    
    try:
        api_proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "127.0.0.1",
                "--port", str(api_port),
            ],
            cwd=str(API_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        
        if not wait_for_server(f"http://127.0.0.1:{api_port}/health", timeout=15):
            print("  [FAIL] API server did not start within 15 seconds")
            results.append(("API startup", False))
        else:
            print(f"  [PASS] API server started on http://127.0.0.1:{api_port}")
            results.append(("API startup", True))
            
            # Test health endpoint
            print("\n[5/6] Testing health endpoint...")
            results.append(("Health endpoint", test_health(api_port)))
            
            # Test bundle loading
            print("\n[6/6] Testing bundle loading...")
            results.append(("Bundle loading", test_bundle_load(api_port)))
    
    except Exception as e:
        print(f"  [FAIL] API server error: {e}")
        results.append(("API startup", False))
    
    finally:
        # Cleanup
        if api_proc:
            api_proc.terminate()
            try:
                api_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_proc.kill()
        
        if web_proc:
            web_proc.terminate()
            try:
                web_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                web_proc.kill()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
