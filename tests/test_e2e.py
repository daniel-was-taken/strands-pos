"""End-to-end test: submit → check status → approve → verify completion."""

from unittest.mock import patch


def test_full_destructive_query_flow(client):
    """Full lifecycle: submit destructive query → check status → approve → completed."""
    # 1. Submit a destructive query
    with patch(
        "server.orchestrator.review_delete_request",
        return_value=(True, "APPROVE: targeted delete"),
    ):
        submit_resp = client.post(
            "/query", json={"query": "Delete employee with id 99"},
        )
    assert submit_resp.status_code == 201
    submit_data = submit_resp.json()
    assert submit_data["status"] == "PENDING_APPROVAL"

    request_id = submit_data["request_id"]
    approval_id = submit_data["approval_id"]

    # 2. Check status — should still be pending
    status_resp = client.get(f"/query/{request_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "PENDING_APPROVAL"

    # 3. Approve the request
    approve_resp = client.post(
        f"/approval/{approval_id}",
        json={
            "decision": "approve",
            "reviewer": "ops-admin",
            "reason": "Confirmed with team lead",
        },
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "COMPLETED"

    # 4. Verify final status
    final_resp = client.get(f"/query/{request_id}")
    assert final_resp.status_code == 200
    assert final_resp.json()["status"] == "COMPLETED"
    assert final_resp.json()["result"]
