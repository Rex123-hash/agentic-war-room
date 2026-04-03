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

# Import sub-agents
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.data_miner import run_data_miner
from agents.context_agent import run_context_agent
from agents.tool_operator import run_tool_operator

# --- Tools that Commander uses to call sub-agents ---
async def call_data_miner(query: str) -> dict:
    """Call the Data Miner sub-agent to fetch tasks and team info from database."""
    print(f"\n[COMMANDER] Calling DATA MINER: {query}")
    result = await run_data_miner(query)
    return {"data_miner_result": result}

async def call_context_agent(query: str) -> dict:
    """Call the Context Agent to retrieve past meeting notes, SOPs and decisions."""
    print(f"\n[COMMANDER] Calling CONTEXT AGENT: {query}")
    result = await run_context_agent(query)
    return {"context_result": result}

async def call_tool_operator(instructions: str) -> dict:
    """Call the Tool Operator to take real actions like Slack, Jira, Calendar."""
    print(f"\n[COMMANDER] Calling TOOL OPERATOR: {instructions[:60]}...")
    result = await run_tool_operator(instructions)
    return {"tool_result": result["summary"], "actions_taken": result["action_log"]}

COMMANDER_PROMPT = """
You are the Commander Agent of the Agentic Project War-Room system.
You are the PRIMARY ORCHESTRATOR managing a team of sub-agents.

You have access to 3 powerful sub-agents via tools:
- call_data_miner: Query the database for tasks, team info, deadlines
- call_context_agent: Retrieve past meeting notes, SOPs, and decisions
- call_tool_operator: Take real actions (Slack messages, Jira updates, Calendar events)

YOUR WORKFLOW:
1. Receive a crisis or project goal
2. Call call_data_miner to understand current situation
3. Call call_context_agent to find relevant SOPs and past decisions
4. Analyze all information gathered
5. Call call_tool_operator to execute necessary actions
6. Generate final Executive Summary

ALWAYS follow this exact output format at the end:

EXECUTIVE SUMMARY
=================
Status: [GREEN/YELLOW/RED]
Red Flags: [list any risks detected]
Actions Taken: [list what was done automatically]
Recommendations: [what the team should do next]
"""

async def run_commander(goal: str) -> str:
    print(f"\n{'='*60}")
    print(f"[COMMANDER] NEW GOAL RECEIVED")
    print(f"{'='*60}")
    print(f"Goal: {goal}")
    print(f"[COMMANDER] Initialising all agents...")

    tools = [
        FunctionTool(call_data_miner),
        FunctionTool(call_context_agent),
        FunctionTool(call_tool_operator),
    ]

    agent = LlmAgent(
        name="CommanderAgent",
        model=GEMINI_MODEL,
        instruction=COMMANDER_PROMPT,
        description="Primary orchestrator that coordinates all sub-agents",
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
        parts=[types.Part(text=goal)]
    )

    print("[COMMANDER] Thinking and delegating...\n")

    response_text = ""
    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                print("\n[COMMANDER] Final response ready")

    return response_text

async def main():
    goal = "It is Monday morning. Our lead developer is out sick. Critical bug #42 is still open with EOD deadline. Analyse the situation, follow SOPs, take all necessary actions, and give me a full crisis response."

    result = await run_commander(goal)

    print("\n" + "=" * 60)
    print("FINAL EXECUTIVE SUMMARY:")
    print("=" * 60)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())