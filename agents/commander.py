import os
import sys
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_miner import run_data_miner
from agents.context_agent import run_context_agent
from agents.tool_operator import run_tool_operator
from database.agent_logger import log_agent_event, clear_agent_runs

GEMINI_MODEL = "gemini-2.5-flash"


async def call_data_miner(query: str) -> dict:
    log_agent_event("CommanderAgent", "delegating", f"Calling Data Miner: {query}")
    print(f"[COMMANDER] Calling DATA MINER: {query}")
    result = await run_data_miner(query)
    return {"data_miner_result": result}


async def call_context_agent(query: str) -> dict:
    log_agent_event("CommanderAgent", "delegating", f"Calling Context Agent: {query}")
    print(f"[COMMANDER] Calling CONTEXT AGENT: {query}")
    result = await run_context_agent(query)
    return {"context_result": result}


async def call_tool_operator(instructions: str) -> dict:
    log_agent_event("CommanderAgent", "delegating", f"Calling Tool Operator: {instructions[:300]}")
    print(f"[COMMANDER] Calling TOOL OPERATOR: {instructions[:80]}...")
    result = await run_tool_operator(instructions)
    return {"tool_result": result["summary"]}


COMMANDER_PROMPT = """
You are the Commander Agent of Project War-Room.
You orchestrate three sub-agents:
- call_data_miner
- call_context_agent
- call_tool_operator

Your job:
1. Understand the project situation and convert it into a concise operational briefing
2. Call Data Miner for current tasks, deadlines, blocked work, and team availability
3. Call Context Agent for SOPs, notes, and prior decisions
4. Determine whether there is project risk
5. If there is critical or high project risk, you MUST call Tool Operator before producing the final answer
6. Produce a final executive summary that synthesizes evidence, decisions, and next steps

Hard rules:
- You must use tools; do not invent project facts
- If there is a critical task, urgent blocker, delivery risk, or developer absence affecting delivery, call Tool Operator
- If urgent coordination is needed, instruct Tool Operator to create a real Google Calendar emergency huddle unless the prompt already includes a pre-executed Google Calendar huddle result
- If the prompt includes a pre-executed Google Calendar huddle result, treat that as the completed Tool Operator Calendar attempt, include the exact status in Actions Taken, and do not request or call a duplicate Calendar huddle
- Do not merely say that actions should be taken; actually call Tool Operator first
- Do not claim Slack or Jira were called externally unless they truly were
- Internal notifications and status updates are allowed
- In crisis scenarios, the final answer must reflect actions already executed by Tool Operator
- Do not copy the user's wording back as the summary
- Do not write a transcript of tool calls
- Each bullet must add new operational value: a risk, decision, action, owner need, or next step
- Keep bullets short and specific
- If external credentials are missing, mention that as an execution limitation, then give a manual fallback action
- Actions Taken must describe what the system actually checked, logged, routed, or attempted
- Recommendations must be forward-looking and must not repeat Red Flags or Actions Taken

Final format:

EXECUTIVE SUMMARY
=================
Status: [GREEN/YELLOW/RED]
Red Flags:
- ...
Actions Taken:
- ...
Recommendations:
- ...
"""


async def run_commander(goal: str) -> str:
    clear_agent_runs()
    log_agent_event("CommanderAgent", "started", goal)

    print("\n" + "=" * 60)
    print("[COMMANDER] NEW GOAL RECEIVED")
    print("=" * 60)
    print(f"Goal: {goal}")
    print("[COMMANDER] Initialising all agents...")
    print("[COMMANDER] Thinking and delegating...\n")

    agent = LlmAgent(
        name="CommanderAgent",
        model=GEMINI_MODEL,
        instruction=COMMANDER_PROMPT,
        tools=[
            FunctionTool(call_data_miner),
            FunctionTool(call_context_agent),
            FunctionTool(call_tool_operator),
        ],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="agentic-war-room",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="agentic-war-room",
        user_id="user_001",
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=goal)],
    )

    response_text = ""

    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            print("\n[COMMANDER] Final response ready")
            log_agent_event("CommanderAgent", "completed", response_text[:500])

    return response_text


async def main():
    goal = (
        "It is Monday morning. Our lead developer is out sick. "
        "A critical frontend task is still open and there is delivery risk today. "
        "Review the situation, apply relevant SOPs, take necessary internal actions, "
        "and create a real emergency huddle if needed."
    )

    result = await run_commander(goal)

    print("\n" + "=" * 60)
    print("FINAL EXECUTIVE SUMMARY:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
