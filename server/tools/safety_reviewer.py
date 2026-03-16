from strands import Agent
from strands.models.gemini import GeminiModel


SAFETY_REVIEWER_SYSTEM_PROMPT = """
You are SafetyReviewer, responsible for reviewing destructive database requests.

Approve only clearly scoped requests that target specific rows.
Reject requests that are broad, ambiguous, or likely to affect many rows.

Output exactly one of:
- APPROVE: <short reason>
- REJECT: <short reason>
"""


def create_safety_reviewer(model: GeminiModel) -> Agent:
    return Agent(model=model, system_prompt=SAFETY_REVIEWER_SYSTEM_PROMPT)


def review_delete_request(reviewer: Agent, query: str) -> tuple[bool, str]:
    response = str(
        reviewer(
            f"""Review this delete request for safety:

{query}

Remember to output exactly one line:
APPROVE: <short reason>
or
REJECT: <short reason>"""
        )
    ).strip()

    upper_response = response.upper()
    if upper_response.startswith("APPROVE:"):
        return True, response

    if upper_response.startswith("REJECT:"):
        return False, response

    return False, f"REJECT: Could not determine safety. Raw reviewer output: {response}"


def request_human_decision(review_verdict: str) -> tuple[bool, str]:
    print("Safety Reviewer verdict:", review_verdict)

    while True:
        decision = input("Human decision required [approve/reject]: ").strip().lower()
        if decision == "approve":
            return True, "Approved by human reviewer."
        if decision == "reject":
            return False, "Rejected by human reviewer."

        print("Please type 'approve' or 'reject'.")
