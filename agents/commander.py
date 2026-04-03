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

GEMINI_MODEL = "gemini-2.5-flash"


async def call_data_miner(query: str) -> dict:
    print(f"[COMMANDER] Calling DATA MINER: {query}")
    result = await run_data_miner(query)
    return {"data_miner_result": result}


async def call_context_agent(query: str) -> dict:
    print(f"[COMMANDER] Calling CONTEXT AGENT: {query}")
    result = await run_context_agent(query)
    return {"context_result": result}


async def call_tool_operator(instructions: str) -> dict:
    print(f"[COMMANDER] Calling TOOL OPERATOR: {instructions[:60]}...")
    result = await run_tool_operator(instructions)
    return {"tool_result": result["summary"]}


COMMANDER_PROMPT = """
You are the Commander Agent of the Agentic Project War-Room.
You orchestrate three sub-agents:
- call_data_miner
- call_context_agent
- call_tool_operator

Workflow:
1. Understand the user's project situation
2. Call Data Miner for current tasks, blocked work, and team availability
3. Call Context Agent for SOPs, notes, and decisions
4. Decide whether operational actions are needed
5. If needed, call Tool Operator to update the internal system
6. Produce the final executive summary

Important:
- Data Miner reads real project data from the database
- Context Agent reads real SOPs and notes from the database
- Tool Operator records real internal actions in the database
- Do not claim that external Slack/Jira/Calendar APIs were called unless the tools actually do that

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

    return response_text


async def main():
    goal = (
        "It is Monday morning. Our lead developer is out sick. "
        "Critical bug #42 is still open with EOD deadline. "
        "Analyse the situation, follow SOPs, take all necessary internal actions, "
        "and give me a full crisis response."
    )

    result = await run_commander(goal)

    print("\n" + "=" * 60)
    print("FINAL EXECUTIVE SUMMARY:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())