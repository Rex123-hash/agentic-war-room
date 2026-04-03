import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.commander import run_commander

app = FastAPI(
    title="Agentic Project War-Room",
    description="Multi-Agent Productivity Assistant — Gen AI Academy APAC 2026",
    version="1.0.0"
)

class GoalRequest(BaseModel):
    goal: str

class SummaryResponse(BaseModel):
    status: str
    summary: str

@app.get("/")
def root():
    return {
        "system": "Agentic Project War-Room",
        "status": "running",
        "agents": ["CommanderAgent", "DataMinerAgent", "ContextAgent", "ToolOperatorAgent"]
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/analyze", response_model=SummaryResponse)
async def analyze(request: GoalRequest):
    if not request.goal or len(request.goal.strip()) == 0:
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    try:
        result = await run_commander(request.goal)
        return SummaryResponse(status="success", summary=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)