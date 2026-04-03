from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.commander import run_commander

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
    return f"""EXECUTIVE SUMMARY
=================
Status: YELLOW
Red Flags:
- Live Gemini quota is currently exhausted, so the full AI reasoning path could not complete.
- The requested scenario still needs manual review once quota is restored.
Actions Taken:
- Accepted the user goal: {goal}
- Switched to fallback response mode so the system remains available for testing.
Recommendations:
- Restore Vertex AI / Gemini quota and rerun this scenario.
- Continue local UI and backend testing using fallback mode.
- Keep SQLite-backed data and internal action logging enabled.
"""


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
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze", response_model=SummaryResponse)
async def analyze(request: GoalRequest):
    if not request.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")

    try:
        result = await run_commander(request.goal)
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