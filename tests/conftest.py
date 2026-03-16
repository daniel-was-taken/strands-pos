"""Configuration and fixtures for tests."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Ensure required env vars are set for tests."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("NEON_API_KEY", "test-key")
    monkeypatch.setenv("NEON_PROJECT_ID", "test-project")
    monkeypatch.setenv("NEON_DATABASE", "test-db")
    monkeypatch.setenv("NEON_BRANCH", "main")
    # GCP / Gemini — use a dummy key so the model provider doesn't attempt ADC
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_REGION", "us-central1")


@pytest.fixture()
def mock_repository():
    """Patch repository functions with in-memory storage for testing."""
    store = {}
    audit = []

    def fake_upsert(request_id, query, status, result=None,
                    review_verdict=None, approval_id=None, created_at=None):
        store[request_id] = {
            "request_id": request_id,
            "query": query,
            "status": status,
            "result": result,
            "review_verdict": review_verdict,
            "approval_id": approval_id,
        }

    def fake_get_by_id(request_id):
        return store.get(request_id)

    def fake_get_by_approval(approval_id):
        for row in store.values():
            if row.get("approval_id") == approval_id:
                return row["request_id"]
        return None

    def fake_audit(approval_id, request_id, decision,
                   reviewer=None, reason=None):
        audit.append({
            "approval_id": approval_id,
            "request_id": request_id,
            "decision": decision,
            "reviewer": reviewer,
            "reason": reason,
        })

    with (
        patch("server.orchestrator.upsert_request", side_effect=fake_upsert),
        patch("server.orchestrator.get_request_by_id", side_effect=fake_get_by_id),
        patch("server.orchestrator.get_request_id_by_approval", side_effect=fake_get_by_approval),
        patch("server.orchestrator.insert_audit_record", side_effect=fake_audit),
    ):
        yield {"store": store, "audit": audit}


@pytest.fixture()
def mock_agents():
    """Patch Agent constructors and Gemini model so no real LLM/GCP calls are made."""
    mock_agent = MagicMock()
    mock_agent.return_value = "Test agent response"

    mock_mcp = MagicMock()
    mock_model = MagicMock()

    with (
        patch("server.orchestrator.create_model", return_value=mock_model),
        patch("server.orchestrator.create_neon_mcp_client", return_value=mock_mcp),
        patch("server.orchestrator.create_safety_reviewer", return_value=mock_agent),
        patch("strands.Agent", return_value=mock_agent),
    ):
        yield mock_agent


@pytest.fixture()
def orchestrator(mock_repository, mock_agents):
    """Build an orchestrator with mocked deps."""
    from server.orchestrator import DatabaseOrchestrator
    return DatabaseOrchestrator()


@pytest.fixture()
def client(mock_repository, mock_agents):
    """TestClient with fully mocked backend."""
    with (
        patch("server.repository.run_migrations"),
        patch("server.repository.get_connection"),
    ):
        from server.api import app
        yield TestClient(app)
