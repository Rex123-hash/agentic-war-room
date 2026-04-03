import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types
import asyncio

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"

# --- Mock database (real AlloyDB baad mein connect karenge) ---
MOCK_DB = {
    "tasks": [
        {"id": 42, "title": "Frontend UI Crash", "assignee": "Alice Smith", "status": "Open", "priority": "Critical", "deadline": "EOD today"},
        {"id": 38, "title": "API timeout fix", "assignee": "Bob Johnson", "status": "In Progress", "priority": "High", "deadline": "Tomorrow"},
        {"id": 35, "title": "Update readme", "assignee": "Carol White", "status": "Open", "priority": "Low", "deadline": "This week"},
    ],
    "team": [
        {"name": "Alice Smith", "role": "Lead Developer", "available": False, "skills": ["frontend", "react"]},
        {"name": "Bob Johnson", "role": "Senior Frontend Dev", "available": True, "skills": ["frontend", "react", "debugging"]},
        {"name": "Carol White", "role": "Frontend Dev", "available": True, "skills": ["frontend", "css"]},
        {"name": "David Green", "role": "Junior Dev", "available": True, "skills": ["frontend", "html"]},
    ]
}

# --- Tools jo Data Miner use karega ---
def get_all_tasks() -> dict:
    """Returns all tasks from the project database."""
    return {"tasks": MOCK_DB["tasks"]}

def get_critical_tasks() -> dict:
    """Returns only critical or high priority open tasks."""
    critical = [t for t in MOCK_DB["tasks"] if t["priority"] in ["Critical", "High"] and t["status"] != "Closed"]
    return {"critical_tasks": critical}

def get_available_developers() -> dict:
    """Returns list of developers who are currently available."""
    available = [m for m in MOCK_DB["team"] if m["available"]]
    return {"available_developers": available}

def get_team_status() -> dict:
    """Returns full team availability and current assignments."""
    return {"team": MOCK_DB["team"]}

DATA_MINER_PROMPT = """
You are the Data Miner sub-agent of the Agentic Project War-Room system.
Your job is to query the project database and return structured information.

You have access to these tools:
- get_all_tasks: Get all project tasks
- get_critical_tasks: Get only critical/high priority tasks
- get_available_developers: Get developers who are available today
- get_team_status: Get full team availability

When asked a question, use the appropriate tool to fetch data and return a clear, structured answer.
Always return data in a clean format that the Commander Agent can use.
"""

async def run_data_miner(query: str) -> str:
    print(f"\n[DATA MINER] Query received: {query}")

    tools = [
        FunctionTool(get_all_tasks),
        FunctionTool(get_critical_tasks),
        FunctionTool(get_available_developers),
        FunctionTool(get_team_status),
    ]

    agent = LlmAgent(
        name="DataMinerAgent",
        model=GEMINI_MODEL,
        instruction=DATA_MINER_PROMPT,
        description="Queries project database for tasks and team information",
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
                print("[DATA MINER] Response ready")

    return response_text

async def main():
    # Test queries
    queries = [
        "What are all the critical tasks right now?",
        "Which developers are available today?",
    ]
    for q in queries:
        result = await run_data_miner(q)
        print(f"\nQuery: {q}")
        print(f"Result: {result}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
