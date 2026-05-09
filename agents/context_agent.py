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

from database.agent_logger import log_agent_event

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "stratify.db")
GEMINI_MODEL = "gemini-2.5-flash"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _search_by_type(doc_type: str, query: str) -> list[dict]:
    conn = _connect()
    words = [w.strip() for w in query.split() if w.strip()]
    if not words:
        rows = []
    else:
        clauses = " OR ".join(["title LIKE ? OR content LIKE ?" for _ in words])
        params = []
        for word in words:
            like = f"%{word}%"
            params.extend([like, like])
        sql = f"SELECT * FROM knowledge_base WHERE type = ? AND ({clauses}) ORDER BY date DESC"
        rows = conn.execute(sql, [doc_type] + params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_meeting_notes(topic: str) -> dict:
    return {"meeting_notes": _search_by_type("meeting_note", topic)}


def search_sops(situation: str) -> dict:
    return {"sops": _search_by_type("sop", situation)}


def search_past_decisions(topic: str) -> dict:
    return {"decisions": _search_by_type("decision", topic)}


def get_all_context(query: str) -> dict:
    conn = _connect()
    words = [w.strip() for w in query.split() if w.strip()]
    if not words:
        rows = []
    else:
        clauses = " OR ".join(["title LIKE ? OR content LIKE ?" for _ in words])
        params = []
        for word in words:
            like = f"%{word}%"
            params.extend([like, like])
        sql = f"SELECT * FROM knowledge_base WHERE {clauses} ORDER BY date DESC"
        rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {"all_context": [dict(r) for r in rows]}


CONTEXT_AGENT_PROMPT = """
You are the Context Agent.
Use tools to retrieve real SOPs, meeting notes, and past decisions from the database.
Always mention source title and date in your answer.
"""


async def run_context_agent(query: str) -> str:
    print(f"[CONTEXT AGENT] Query: {query}")
    log_agent_event("ContextAgent", "started", query)

    agent = LlmAgent(
        name="ContextAgent",
        model=GEMINI_MODEL,
        instruction=CONTEXT_AGENT_PROMPT,
        tools=[
            FunctionTool(search_meeting_notes),
            FunctionTool(search_sops),
            FunctionTool(search_past_decisions),
            FunctionTool(get_all_context),
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
            print("[CONTEXT AGENT] Done")
            log_agent_event("ContextAgent", "completed", response_text[:500])

    return response_text


async def main():
    result = await run_context_agent("What SOPs and past decisions apply when a lead developer is sick and a critical frontend bug is open?")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())