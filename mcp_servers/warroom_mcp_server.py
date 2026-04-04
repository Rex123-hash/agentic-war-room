import asyncio
import json
import os
import sys
import sqlite3

from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "warroom.db")

from tools.calendar_tool import create_calendar_event

app = Server("warroom-mcp-server")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_open_tasks(limit: int = 10):
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, title, assignee, status, priority, deadline
        FROM tasks
        WHERE status != 'Closed'
        ORDER BY
            CASE priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END,
            id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_team_availability():
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, name, role, email, skills, available
        FROM team_members
        ORDER BY id
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_mcp_huddle(title: str, attendees: str, duration_minutes: int, description: str):
    return create_calendar_event(
        title=title,
        attendees=attendees,
        duration_minutes=duration_minutes,
        description=description,
    )


@app.list_tools()
async def list_mcp_tools() -> list[mcp_types.Tool]:
    return [
        mcp_types.Tool(
            name="get_open_tasks",
            description="Get open and in-progress project tasks from the War-Room database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            },
        ),
        mcp_types.Tool(
            name="get_team_availability",
            description="Get current team availability and roles from the War-Room database.",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        ),
        mcp_types.Tool(
            name="create_mcp_huddle",
            description="Create a real Google Calendar emergency huddle.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "attendees": {"type": "string"},
                    "duration_minutes": {"type": "integer"},
                    "description": {"type": "string"},
                },
                "required": ["title", "attendees", "duration_minutes", "description"],
            },
        ),
    ]


@app.call_tool()
async def call_mcp_tool(name: str, arguments: dict) -> list[mcp_types.Content]:
    try:
        if name == "get_open_tasks":
            result = get_open_tasks(arguments.get("limit", 10))
        elif name == "get_team_availability":
            result = get_team_availability()
        elif name == "create_mcp_huddle":
            result = create_mcp_huddle(
                title=arguments["title"],
                attendees=arguments["attendees"],
                duration_minutes=arguments["duration_minutes"],
                description=arguments["description"],
            )
        else:
            result = {"error": f"Unknown MCP tool: {name}"}

        return [mcp_types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as exc:
        return [mcp_types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]


async def run_mcp_stdio_server():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run_mcp_stdio_server())
