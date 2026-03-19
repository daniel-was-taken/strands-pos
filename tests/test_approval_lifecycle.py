"""Tests for the approval lifecycle (destructive queries)."""

from unittest.mock import patch


def test_destructive_query_requires_approval(client):
    """Queries with destructive keywords should go to approval flow."""
    with patch(
        "server.core.orchestrator.review_delete_request",
        return_value=(True, "APPROVE: scoped delete"),
    ):
        resp = client.post(
            "/query", json={"query": "Delete employee with id 42"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PENDING_APPROVAL"
    assert data["approval_id"]
    assert data["review_verdict"]


def test_approve_executes_query(client):
    """Approving a pending request should execute and complete it."""
    with patch(
        "server.core.orchestrator.review_delete_request",
        return_value=(True, "APPROVE: scoped delete"),
    ):
        submit = client.post(
            "/query", json={"query": "Delete employee with id 42"},
        )
    approval_id = submit.json()["approval_id"]
    request_id = submit.json()["request_id"]

    resp = client.post(
        f"/approval/{approval_id}",
        json={"decision": "approve", "reviewer": "admin", "reason": "Verified"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_id"] == request_id
    assert data["status"] == "COMPLETED"


def test_reject_blocks_query(client):
    """Rejecting a pending request should mark it REJECTED."""
    with patch(
        "server.core.orchestrator.review_delete_request",
        return_value=(True, "APPROVE: scoped delete"),
    ):
        submit = client.post(
            "/query", json={"query": "Delete employee with id 42"},
        )
    approval_id = submit.json()["approval_id"]

    resp = client.post(
        f"/approval/{approval_id}",
        json={"decision": "reject", "reviewer": "admin", "reason": "Too risky"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"


def test_unknown_approval_returns_404(client):
    resp = client.post(
        "/approval/nonexistent",
        json={"decision": "approve"},
    )
    assert resp.status_code == 404


def test_safety_reviewer_reject_sets_recommended_reject(client):
    """When the AI safety reviewer rejects, status should be RECOMMENDED_REJECT."""
    with patch(
        "server.core.orchestrator.review_delete_request",
        return_value=(False, "REJECT: too broad"),
    ):
        resp = client.post(
            "/query", json={"query": "Delete all employees"},
        )
    assert resp.status_code == 201
    assert resp.json()["status"] == "RECOMMENDED_REJECT"
