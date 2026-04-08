import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.commander import run_commander
from agents.mcp_ops_agent import run_mcp_ops_agent
from database.chat_memory import save_message, get_recent_messages
from database.db_setup import setup_database

setup_database()

app = FastAPI(
    title="Agentic Project War-Room",
    version="1.0.0",
    description="Local MVP for multi-agent project operations",
)


class GoalRequest(BaseModel):
    goal: str
    session_id: str = "default-session"


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
- The on-call lead is currently unavailable.
- Immediate coordination is required.
Actions Taken:
- Accepted the production-risk scenario.
- Switched to fallback mode to keep the system responsive.
Recommendations:
- Create an emergency engineering huddle immediately.
- Assign one owner for triage and one for stakeholder communication.
- Review blocked work and deployment dependencies.
"""

    if "critical" in goal_lower or "bug" in goal_lower or "sick" in goal_lower:
        return """EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- A critical delivery issue is active.
- Team availability is reduced.
- Delay risk is elevated if ownership is unclear.
Actions Taken:
- Accepted the critical-risk scenario.
- Switched to fallback mode to avoid UI delay.
Recommendations:
- Reconfirm the task owner immediately.
- Schedule an emergency huddle.
- Reassign the task to the most relevant available developer if needed.
"""

    return f"""EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- The full AI reasoning path could not complete in time.
Actions Taken:
- Accepted the user goal: {goal}
- Switched to fallback mode to keep the system responsive.
Recommendations:
- Retry the request when model quota or latency improves.
"""


def build_chat_context(session_id: str, latest_goal: str) -> str:
    history = get_recent_messages(session_id, limit=8)

    if not history:
        return latest_goal

    lines = ["Conversation context:"]
    for msg in history:
        lines.append(f"{msg['role'].upper()}: {msg['message']}")

    lines.append(f"USER: {latest_goal}")
    lines.append("Use the above conversation context while responding.")
    return "\n".join(lines)

def is_small_talk(goal: str) -> bool:
    cleaned = goal.strip().lower()
    return cleaned in {
        "hi", "hello", "hey", "hii", "hiii",
        "good morning", "good evening", "good afternoon",
        "how are you", "who are you"
    }


async def safe_run(goal: str, session_id: str) -> SummaryResponse:
    if is_small_talk(goal):
        return SummaryResponse(
        status="success",
        summary=(
            "Hi! I’m Project War-Room, your project operations assistant. "
            "Tell me about a project issue like a blocked task, critical bug, "
            "team availability problem, sprint delay, or production incident, "
            "and I’ll help analyze it."
        ),
    )
    try:
        contextual_goal = build_chat_context(session_id, goal)
        result = await asyncio.wait_for(run_commander(contextual_goal), timeout=45)
        save_message(session_id, "user", goal)
        save_message(session_id, "assistant", result)
        return SummaryResponse(status="success", summary=result)
    except asyncio.TimeoutError:
        fallback = fallback_summary(goal)
        save_message(session_id, "user", goal)
        save_message(session_id, "assistant", fallback)
        return SummaryResponse(status="fallback", summary=fallback)
    except Exception as exc:
        error_text = str(exc)

        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text or "quota" in error_text.lower():
            fallback = fallback_summary(goal)
            save_message(session_id, "user", goal)
            save_message(session_id, "assistant", fallback)
            return SummaryResponse(status="fallback", summary=fallback)

        raise HTTPException(status_code=500, detail=error_text)


async def safe_run_mcp(goal: str, session_id: str) -> SummaryResponse:
    try:
        contextual_goal = build_chat_context(session_id, goal)
        result = await asyncio.wait_for(run_mcp_ops_agent(contextual_goal), timeout=45)
        save_message(session_id, "user", goal)
        save_message(session_id, "assistant", result)
        return SummaryResponse(status="success", summary=result)
    except asyncio.TimeoutError:
        fallback = fallback_summary(goal)
        save_message(session_id, "user", goal)
        save_message(session_id, "assistant", fallback)
        return SummaryResponse(status="fallback", summary=fallback)
    except Exception as exc:
        error_text = str(exc)

        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text or "quota" in error_text.lower():
            fallback = fallback_summary(goal)
            save_message(session_id, "user", goal)
            save_message(session_id, "assistant", fallback)
            return SummaryResponse(status="fallback", summary=fallback)

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
    return await safe_run(request.goal, request.session_id)


@app.post("/analyze-daily", response_model=SummaryResponse)
async def analyze_daily():
    daily_goal = (
        "Run the daily autonomous project health check. "
        "Review open tasks, blocked tasks, critical priorities, team availability, "
        "relevant SOPs, and take necessary internal actions if there is project risk. "
        "Return a full executive summary."
    )
    return await safe_run(daily_goal, "daily-session")


@app.post("/analyze-mcp", response_model=SummaryResponse)
async def analyze_mcp(request: GoalRequest):
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    return await safe_run_mcp(request.goal, request.session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
