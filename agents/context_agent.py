import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"

# Mock knowledge base (Vertex AI Vector Search baad mein connect karenge)
MOCK_KNOWLEDGE_BASE = [
    {
        "id": 1,
        "type": "meeting_note",
        "date": "2026-03-28",
        "title": "Sprint 23 Planning",
        "content": "Team decided Bug #42 is highest priority. Alice Smith assigned as lead. Bob Johnson is backup for all frontend critical issues."
    },
    {
        "id": 2,
        "type": "sop",
        "date": "2026-01-15",
        "title": "Critical Bug Response SOP",
        "content": "When a critical bug is open and assignee is unavailable: 1) Reassign to senior dev immediately. 2) Notify #engineering-critical Slack channel. 3) Inform project manager. 4) Schedule emergency huddle within 1 hour."
    },
    {
        "id": 3,
        "type": "decision",
        "date": "2026-03-20",
        "title": "Frontend Architecture Decision",
        "content": "Frontend stack is React 18 with TypeScript. All critical frontend bugs must be reviewed by a senior frontend developer before closing."
    },
    {
        "id": 4,
        "type": "meeting_note",
        "date": "2026-03-30",
        "title": "Daily Standup",
        "content": "Alice Smith mentioned Bug #42 is complex. Involves user profile data edge case. Suggested fix approach: check null values in user config object before rendering profile component."
    },
    {
        "id": 5,
        "type": "sop",
        "date": "2026-02-01",
        "title": "Developer Sick Leave Protocol",
        "content": "When lead developer is sick: notify team lead within 1 hour. Reassign all critical tasks. Daily standup must include status update on reassigned tasks."
    }
]

def search_meeting_notes(topic: str) -> dict:
    """Search past meeting notes related to a topic."""
    results = [
        doc for doc in MOCK_KNOWLEDGE_BASE
        if doc["type"] == "meeting_note" and
        any(word.lower() in doc["content"].lower() for word in topic.split())
    ]
    return {"meeting_notes": results if results else [{"message": f"No meeting notes found for: {topic}"}]}

def search_sops(situation: str) -> dict:
    """Search Standard Operating Procedures for a given situation."""
    results = [
        doc for doc in MOCK_KNOWLEDGE_BASE
        if doc["type"] == "sop" and
        any(word.lower() in doc["content"].lower() for word in situation.split())
    ]
    return {"sops": results if results else [{"message": f"No SOPs found for: {situation}"}]}

def search_past_decisions(topic: str) -> dict:
    """Search past architectural or team decisions related to a topic."""
    results = [
        doc for doc in MOCK_KNOWLEDGE_BASE
        if doc["type"] == "decision" and
        any(word.lower() in doc["content"].lower() for word in topic.split())
    ]
    return {"decisions": results if results else [{"message": f"No decisions found for: {topic}"}]}

def get_all_context(query: str) -> dict:
    """Search entire knowledge base for anything relevant to the query."""
    results = [
        doc for doc in MOCK_KNOWLEDGE_BASE
        if any(word.lower() in doc["content"].lower() or
               word.lower() in doc["title"].lower()
               for word in query.split())
    ]
    return {"all_context": results if results else [{"message": "No relevant context found"}]}

CONTEXT_AGENT_PROMPT = """
You are the Context Agent sub-agent of the Agentic Project War-Room system.
Your job is to retrieve relevant past information from the knowledge base.

You have access to these tools:
- search_meeting_notes: Find relevant past meeting notes
- search_sops: Find Standard Operating Procedures for a situation
- search_past_decisions: Find past architectural or team decisions
- get_all_context: Search everything in the knowledge base

When asked a question, use the appropriate tool and return a clear summary of relevant context.
Always mention the date and source of information you return.
"""

async def run_context_agent(query: str) -> str:
    print(f"\n[CONTEXT AGENT] Query received: {query}")

    tools = [
        FunctionTool(search_meeting_notes),
        FunctionTool(search_sops),
        FunctionTool(search_past_decisions),
        FunctionTool(get_all_context),
    ]

    agent = LlmAgent(
        name="ContextAgent",
        model=GEMINI_MODEL,
        instruction=CONTEXT_AGENT_PROMPT,
        description="Retrieves past meeting notes, SOPs and decisions from knowledge base",
        tools=tools,
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="agentic-war-room",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="agentic-war-room",
        user_id="user_001"
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )

    response_text = ""
    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("[CONTEXT AGENT] Response ready")

    return response_text

async def main():
    queries = [
        "What is the SOP when a developer is sick and critical bug is open?",
        "Any past decisions about Bug #42 or frontend issues?",
    ]
    for q in queries:
        result = await run_context_agent(q)
        print(f"\nQuery: {q}")
        print(f"Result: {result}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())