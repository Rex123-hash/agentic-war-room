from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.commander import run_commander
from agents.mcp_ops_agent import run_mcp_ops_agent

app = FastAPI(
    title="Agentic Project War-Room",
    version="1.0.0",
    description="Local MVP for multi-agent project operations",
)


class GoalRequest(BaseModel):
    goal: str


class SummaryResponse(BaseModel):
    status: str
    summary: str


def fallback_summary(goal: str) -> str:
    goal_lower = goal.lower()

    if "production" in goal_lower:
        return """EXECUTIVE SUMMARY
=================
Status: RED
Red Flags:
- Production instability is affecting users.
- The on-call lead is currently unavailable, creating escalation risk.
- Immediate coordination is needed to avoid extended impact.
Actions Taken:
- Accepted the production-risk scenario for emergency handling.
- Switched to fallback response mode so the system remains available during model quota exhaustion.
- Preserved access to local database state and internal action logging.
Recommendations:
- Create an emergency engineering huddle immediately.
- Assign one developer to incident triage and one to stakeholder communication.
- Review blocked tasks and any pending deployment dependencies before making changes.
"""

    if "critical" in goal_lower or "bug" in goal_lower or "sick" in goal_lower:
        return """EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- A critical delivery issue is active.
- Team availability is reduced due to developer absence.
- Delay risk is elevated if ownership is not clarified quickly.
Actions Taken:
- Accepted the critical-risk scenario for structured handling.
- Switched to fallback response mode so the system remains available during model quota exhaustion.
- Preserved access to local database state, internal action logging, and external action capability.
Recommendations:
- Reconfirm the task owner for the critical item immediately.
- Schedule an emergency huddle and review current blockers.
- Reassign the task to the most relevant available developer if needed.
"""

    if "sprint" in goal_lower or "deadline" in goal_lower:
        return """EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- Delivery deadlines are at risk.
- Open and blocked tasks may affect sprint completion.
- Team coordination is required to reduce schedule slippage.
Actions Taken:
- Accepted the schedule-risk scenario for structured handling.
- Switched to fallback response mode so the system remains available during model quota exhaustion.
- Preserved access to local database state and action logging.
Recommendations:
- Prioritize blocked and high-priority work first.
- Rebalance assignments across available team members.
- Run a focused risk review before the next milestone.
"""

    return f"""EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- Live Gemini quota is currently exhausted, so the full AI reasoning path could not complete.
- The requested scenario still needs manual review once quota is restored.
Actions Taken:
- Accepted the user goal: {goal}
- Switched to fallback response mode so the system remains available for testing.
- Preserved local database access and internal action logging.
Recommendations:
- Restore Vertex AI / Gemini quota and rerun this scenario.
- Continue local and backend testing using fallback mode.
- Keep SQLite-backed data and internal action logging enabled.
"""


async def safe_run(goal: str) -> SummaryResponse:
    try:
        result = await run_commander(goal)
        return SummaryResponse(status="success", summary=result)
    except Exception as exc:
        error_text = str(exc)

        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text or "quota" in error_text.lower():
            return SummaryResponse(
                status="fallback",
                summary=fallback_summary(goal),
            )

        raise HTTPException(status_code=500, detail=error_text)


@app.get("/")
def root():
    return {
        "system": "Agentic Project War-Room",
        "status": "running",
        "agents": [
            "CommanderAgent",
            "DataMinerAgent",
            "ContextAgent",
            "ToolOperatorAgent",
            "MCPOpsAgent",
        ],
        "modes": ["interactive", "proactive", "mcp"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze", response_model=SummaryResponse)
async def analyze(request: GoalRequest):
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    return await safe_run(request.goal)


@app.post("/analyze-daily", response_model=SummaryResponse)
async def analyze_daily():
    daily_goal = (
        "Run the daily autonomous project health check. "
        "Review open tasks, blocked tasks, critical priorities, team availability, "
        "relevant SOPs, and take necessary internal actions if there is project risk. "
        "Return a full executive summary."
    )
    return await safe_run(daily_goal)


@app.post("/analyze-mcp", response_model=SummaryResponse)
async def analyze_mcp(request: GoalRequest):
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")

    try:
        result = await run_mcp_ops_agent(request.goal)
        return SummaryResponse(status="success", summary=result)
    except Exception as exc:
        error_text = str(exc)

        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text or "quota" in error_text.lower():
            return SummaryResponse(
                status="fallback",
                summary=fallback_summary(request.goal),
            )

        raise HTTPException(status_code=500, detail=error_text)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
