import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.commander import run_commander
from agents.mcp_ops_agent import run_mcp_ops_agent
from agents.tool_operator import create_real_calendar_huddle, DEFAULT_HUDDLE_EMAIL
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
- Classified the situation as production-impacting and high urgency.
- Returned a safe fallback briefing while the full agent path was unavailable.
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
- Classified the situation as a delivery-risk event.
- Returned a safe fallback briefing while the full agent path was unavailable.
Recommendations:
- Reconfirm the task owner immediately.
- Schedule an emergency huddle.
- Reassign the task to the most relevant available developer if needed.
"""

    return """EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- The full AI reasoning path could not complete in time.
Actions Taken:
- Preserved the request and returned a safe operational fallback.
- Kept the service responsive while the model path was unavailable.
Recommendations:
- Re-run the analysis after model quota, credentials, or latency recovers.
- Assign a human owner to review active blockers while automation is degraded.
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


def needs_calendar_huddle(goal: str) -> bool:
    goal_lower = goal.lower()
    triggers = [
        "critical",
        "delivery is at risk",
        "delivery risk",
        "production",
        "unstable",
        "emergency huddle",
        "calendar",
        "immediate coordination",
    ]
    return any(trigger in goal_lower for trigger in triggers)


def calendar_status_summary(goal: str, calendar_result: dict) -> str:
    reason = calendar_result.get("reason", "Calendar did not return a reason.")
    status = calendar_result.get("status", "unknown")
    event_link = calendar_result.get("event_link", "")

    calendar_action = f"Google Calendar huddle attempt returned status={status}."
    if event_link:
        calendar_action += f" Event: {event_link}"
    elif reason:
        calendar_action += f" Reason: {reason}"

    return f"""EXECUTIVE SUMMARY
=================
Status: RED
Red Flags:
- The situation is urgent and delivery coordination is at risk.
- Google Calendar could not create the emergency huddle automatically.
- Manual coordination is needed until Calendar OAuth is repaired.
Actions Taken:
- Classified the request as a critical coordination issue.
- Attempted to create a Google Calendar emergency huddle with the configured default attendee.
- {calendar_action}
Recommendations:
- Start the emergency huddle manually with the project owner and available team.
- Re-enable or replace the Google OAuth client, then refresh the Calendar token.
- Re-run Critical Bug analysis after Calendar credentials are repaired.
"""


def run_calendar_preflight(goal: str) -> dict | None:
    if not needs_calendar_huddle(goal):
        return None

    return create_real_calendar_huddle(
        title="Project War-Room Emergency Huddle",
        attendees=DEFAULT_HUDDLE_EMAIL,
        duration_minutes=15,
        description=f"Auto-created by Project War-Room for: {goal[:500]}",
    )


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
        calendar_preflight = run_calendar_preflight(goal)
        goal_with_preflight = goal
        if calendar_preflight:
            goal_with_preflight = (
                f"{goal}\n\nPre-executed Google Calendar huddle result: {calendar_preflight}\n"
                "Use this pre-executed Calendar result in Actions Taken. "
                "This preflight counts as the real Tool Operator Calendar attempt. "
                "Do not retry Calendar and do not claim Calendar is awaiting attendee emails if the result includes a default attendee."
            )

        contextual_goal = build_chat_context(session_id, goal_with_preflight)
        result = await asyncio.wait_for(run_commander(contextual_goal), timeout=45)
        if not result:
            result = calendar_status_summary(goal, calendar_preflight) if calendar_preflight else fallback_summary(goal)
        save_message(session_id, "user", goal)
        save_message(session_id, "assistant", result)
        return SummaryResponse(status="success", summary=result)
    except asyncio.TimeoutError:
        if "calendar_preflight" in locals() and calendar_preflight:
            fallback = calendar_status_summary(goal, calendar_preflight)
        else:
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
