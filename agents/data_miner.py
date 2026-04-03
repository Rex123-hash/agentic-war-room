import os
import sys
import sqlite3
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "warroom.db")
GEMINI_MODEL = "gemini-2.5-flash"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_tasks() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return {"tasks": [dict(r) for r in rows]}


def get_critical_tasks() -> dict:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM tasks
        WHERE priority IN ('Critical', 'High') AND status != 'Closed'
        ORDER BY deadline ASC
        """
    ).fetchall()
    conn.close()
    return {"critical_tasks": [dict(r) for r in rows]}


def get_available_developers() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM team_members WHERE available = 1").fetchall()
    conn.close()
    return {"available_developers": [dict(r) for r in rows]}


def get_team_status() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM team_members").fetchall()
    conn.close()
    return {"team": [dict(r) for r in rows]}


def get_blocked_tasks() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM tasks WHERE status = 'Blocked'").fetchall()
    conn.close()
    return {"blocked_tasks": [dict(r) for r in rows]}


DATA_MINER_PROMPT = """
You are the Data Miner sub-agent.
You must always use tools to fetch real project data from the database.
Return concise structured findings for the Commander.
"""


async def run_data_miner(query: str) -> str:
    print(f"[DATA MINER] Query: {query}")

    agent = LlmAgent(
        name="DataMinerAgent",
        model=GEMINI_MODEL,
        instruction=DATA_MINER_PROMPT,
        tools=[
            FunctionTool(get_all_tasks),
            FunctionTool(get_critical_tasks),
            FunctionTool(get_available_developers),
            FunctionTool(get_team_status),
            FunctionTool(get_blocked_tasks),
        ],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="agentic-war-room", session_service=session_service)
    session = await session_service.create_session(app_name="agentic-war-room", user_id="user_001")

    message = types.Content(role="user", parts=[types.Part(text=query)])
    response_text = ""

    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            print("[DATA MINER] Done")

    return response_text


async def main():
    result = await run_data_miner("What are the critical tasks, blocked tasks, and available developers right now?")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())