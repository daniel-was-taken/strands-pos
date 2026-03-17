import logging
from uuid import uuid4

from strands import Agent
from strands.tools.executors import SequentialToolExecutor

from server.model import create_model
from server.neon_mcp import create_neon_mcp_client
from server.repository import (
    get_request_by_id,
    get_request_id_by_approval,
    insert_audit_record,
    upsert_request,
)
from server.schemas import RequestStatus
from server.tools.delete_assistant import create_delete_tool
from server.tools.insert_assistant import create_insert_tool
from server.tools.safety_reviewer import (
    create_safety_reviewer,
    request_human_decision,
    review_delete_request,
)
from server.tools.schema_assistant import create_schema_tool

logger = logging.getLogger(__name__)

DESTRUCTIVE_KEYWORDS = {"delete", "remove", "drop", "truncate", "destroy"}

DATABASE_SYSTEM_PROMPT = """
You are DBControl, a database management orchestrator.

You are responsible for calling the necessary tools to handle database-related requests.
Use these tools:
- schema_assistant for read-only schema and SELECT queries
- insert_assistant for insert requests
- delete_assistant for delete requests

Keep responses clear and actionable.
"""


class DatabaseOrchestrator:
    def __init__(self) -> None:
        model = create_model()
        mcp_client = create_neon_mcp_client()
        self.database_agent = Agent(
            model=model,
            system_prompt=DATABASE_SYSTEM_PROMPT,
            tool_executor=SequentialToolExecutor(),
            tools=[
                create_schema_tool(mcp_client),
                create_insert_tool(mcp_client),
                create_delete_tool(mcp_client),
            ],
        )
        self.safety_reviewer = create_safety_reviewer()

    @staticmethod
    def needs_safety_review(user_input: str) -> bool:
        words = set(user_input.lower().split())
        return bool(words & DESTRUCTIVE_KEYWORDS)

    def submit_query(self, query: str) -> dict:
        request_id = str(uuid4())

        if self.needs_safety_review(query):
            is_approved, verdict = review_delete_request(self.safety_reviewer, query)
            approval_id = str(uuid4())
            status = (
                RequestStatus.PENDING_APPROVAL
                if is_approved
                else RequestStatus.RECOMMENDED_REJECT
            )
            upsert_request(
                request_id=request_id,
                query=query,
                status=status,
                review_verdict=verdict,
                approval_id=approval_id,
            )
            return {
                "request_id": request_id,
                "status": status,
                "approval_id": approval_id,
                "review_verdict": verdict,
            }

        return self._execute_and_store(request_id=request_id, query=query)

    def _execute_and_store(self, request_id: str, query: str) -> dict:
        try:
            response = str(self.database_agent(query))
            upsert_request(
                request_id=request_id,
                query=query,
                status=RequestStatus.COMPLETED,
                result=response,
            )
            return {
                "request_id": request_id,
                "status": RequestStatus.COMPLETED,
                "result": response,
            }
        except Exception:
            logger.exception("Query execution failed for request %s", request_id)
            error_msg = "Request failed. Please try again."
            upsert_request(
                request_id=request_id,
                query=query,
                status=RequestStatus.FAILED,
                result=error_msg,
            )
            return {
                "request_id": request_id,
                "status": RequestStatus.FAILED,
                "result": error_msg,
            }

    def decide_approval(
        self,
        approval_id: str,
        decision: str,
        reviewer: str | None = None,
        reason: str | None = None,
    ) -> dict:
        decision = decision.strip().lower()

        request_id = get_request_id_by_approval(approval_id)
        if request_id is None:
            return {"error": "approval_id not found"}

        row = get_request_by_id(request_id)
        if row is None:
            return {"error": "request_id not found"}

        if decision == "reject":
            upsert_request(
                request_id=request_id,
                query=row["query"],
                status=RequestStatus.REJECTED,
                result="Rejected by human reviewer.",
                review_verdict=row["review_verdict"],
                approval_id=approval_id,
            )
            insert_audit_record(
                approval_id=approval_id,
                request_id=request_id,
                decision="reject",
                reviewer=reviewer,
                reason=reason,
            )
            return {
                "request_id": request_id,
                "status": RequestStatus.REJECTED,
                "result": "Rejected by human reviewer.",
            }

        if decision == "approve":
            insert_audit_record(
                approval_id=approval_id,
                request_id=request_id,
                decision="approve",
                reviewer=reviewer,
                reason=reason,
            )
            return self._execute_and_store(
                request_id=request_id, query=row["query"],
            )

        return {"error": "decision must be 'approve' or 'reject'"}

    def get_request(self, request_id: str) -> dict:
        row = get_request_by_id(request_id)
        if row is None:
            return {"error": "request_id not found"}

        return {
            "request_id": row["request_id"],
            "query": row["query"],
            "status": row["status"],
            "result": row["result"],
            "review_verdict": row["review_verdict"],
            "approval_id": row["approval_id"],
        }

    def handle_cli_query(self, query: str) -> str:
        if self.needs_safety_review(query):
            is_approved, verdict = review_delete_request(self.safety_reviewer, query)
            human_approved, human_message = request_human_decision(verdict)
            if not human_approved:
                return f"Blocked. {human_message} {verdict}"
            if not is_approved:
                return f"Blocked by Safety Reviewer. {verdict}"

        return str(self.database_agent(query))
