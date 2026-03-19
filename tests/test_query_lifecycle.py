"""Tests for the query submission and status lifecycle."""


def test_submit_non_destructive_query(client):
    """Non-destructive query should complete immediately."""
    resp = client.post("/query", json={"query": "Show all tables"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["request_id"]
    assert data["result"]


def test_get_query_status(client):
    """Submitted query should be retrievable by request_id."""
    submit = client.post("/query", json={"query": "Show all tables"})
    request_id = submit.json()["request_id"]

    resp = client.get(f"/query/{request_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_id"] == request_id
    assert data["status"] == "COMPLETED"


def test_get_unknown_request_returns_404(client):
    resp = client.get("/query/nonexistent-id")
    assert resp.status_code == 404


def test_submit_empty_query_returns_422(client):
    resp = client.post("/query", json={"query": ""})
    assert resp.status_code == 422
