import os
import sys
import asyncio
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_SERVER_PATH = os.path.join(BASE_DIR, "mcp_servers", "warroom_mcp_server.py")
GEMINI_MODEL = "gemini-2.5-flash"


async def run_mcp_ops_agent(query: str) -> str:
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[MCP_SERVER_PATH],
            ),
            timeout=20,
        ),
        tool_filter=[
            "get_open_tasks",
            "get_team_availability",
            "create_mcp_huddle",
        ],
    )

    agent = LlmAgent(
        name="MCPOpsAgent",
        model=GEMINI_MODEL,
        instruction="""
You are an MCP-powered operations agent for Project War-Room.

Use MCP tools to:
- inspect open tasks
- inspect team availability
- create a real emergency huddle when risk is present

If the user describes urgent delivery risk, use the MCP tools before answering.
Be concise and operational.
""",
        tools=[toolset],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="warroom-mcp-client",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="warroom-mcp-client",
        user_id="user_001",
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=query)],
    )

    response_text = ""

    try:
        async for event in runner.run_async(
            user_id="user_001",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text
    finally:
        await toolset.close()

    return response_text


async def main():
    result = await run_mcp_ops_agent(
        "Check open critical work and team availability. If there is urgent delivery risk, create an emergency huddle for amaank2405@gmail.com."
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
