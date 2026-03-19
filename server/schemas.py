"""Request/response schemas and status enums for the API."""

from enum import StrEnum

from pydantic import BaseModel, Field


class RequestStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    RECOMMENDED_REJECT = "RECOMMENDED_REJECT"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


# --- Request bodies ---


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class ApprovalRequest(BaseModel):
    decision: ApprovalDecision
    reason: str | None = Field(default=None, max_length=500)
    reviewer: str | None = Field(default=None, max_length=100)


# --- Response bodies ---


class QuerySubmitResponse(BaseModel):
    request_id: str
    status: RequestStatus
    result: str | None = None
    approval_id: str | None = None
    review_verdict: str | None = None


class QueryStatusResponse(BaseModel):
    request_id: str
    query: str
    status: RequestStatus
    result: str | None = None
    review_verdict: str | None = None
    approval_id: str | None = None


class ApprovalResponse(BaseModel):
    request_id: str
    status: RequestStatus
    result: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
