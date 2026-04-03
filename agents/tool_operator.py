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

# Mock action log (real Slack/Calendar/Jira baad mein connect karenge)
ACTION_LOG = []

def send_slack_message(channel: str, message: str) -> dict:
    """Send a message to a Slack channel."""
    action = {
        "tool": "Slack",
        "channel": channel,
        "message": message,
        "status": "sent"
    }
    ACTION_LOG.append(action)
    print(f"[SLACK] #{channel}: {message[:60]}...")
    return {"status": "success", "channel": channel, "message_sent": message}

def reassign_jira_ticket(ticket_id: str, new_assignee: str, comment: str) -> dict:
    """Reassign a Jira ticket to a new developer."""
    action = {
        "tool": "Jira",
        "ticket_id": ticket_id,
        "new_assignee": new_assignee,
        "comment": comment,
        "status": "reassigned"
    }
    ACTION_LOG.append(action)
    print(f"[JIRA] Ticket #{ticket_id} reassigned to {new_assignee}")
    return {"status": "success", "ticket_id": ticket_id, "new_assignee": new_assignee}

def create_calendar_event(title: str, attendees: str, duration_minutes: int, description: str) -> dict:
    """Create a calendar event and invite attendees."""
    action = {
        "tool": "Calendar",
        "title": title,
        "attendees": attendees,
        "duration_minutes": duration_minutes,
        "description": description,
        "status": "created"
    }
    ACTION_LOG.append(action)
    print(f"[CALENDAR] Event created: {title} ({duration_minutes} mins) for {attendees}")
    return {"status": "success", "event_title": title, "attendees": attendees, "duration": f"{duration_minutes} minutes"}

def update_jira_status(ticket_id: str, new_status: str, comment: str) -> dict:
    """Update the status of a Jira ticket."""
    action = {
        "tool": "Jira",
        "ticket_id": ticket_id,
        "new_status": new_status,
        "comment": comment,
        "status": "updated"
    }
    ACTION_LOG.append(action)
    print(f"[JIRA] Ticket #{ticket_id} status updated to: {new_status}")
    return {"status": "success", "ticket_id": ticket_id, "new_status": new_status}

def get_action_log() -> dict:
    """Get log of all actions taken in this session."""
    return {"actions_taken": ACTION_LOG, "total_actions": len(ACTION_LOG)}

TOOL_OPERATOR_PROMPT = """
You are the Tool Operator sub-agent of the Agentic Project War-Room system.
Your job is to take real actions using available tools.

You have access to these tools:
- send_slack_message: Send messages to Slack channels or users
- reassign_jira_ticket: Reassign a Jira ticket to a new developer
- create_calendar_event: Schedule calendar meetings
- update_jira_status: Update status of a Jira ticket
- get_action_log: See what actions have already been taken

When given instructions, execute ALL required actions using the tools.
After completing all actions, provide a summary of everything you did.
Be decisive - if you are told to take an action, take it immediately.
"""

async def run_tool_operator(instructions: str) -> dict:
    print(f"\n[TOOL OPERATOR] Instructions received: {instructions[:80]}...")

    tools = [
        FunctionTool(send_slack_message),
        FunctionTool(reassign_jira_ticket),
        FunctionTool(create_calendar_event),
        FunctionTool(update_jira_status),
        FunctionTool(get_action_log),
    ]

    agent = LlmAgent(
        name="ToolOperatorAgent",
        model=GEMINI_MODEL,
        instruction=TOOL_OPERATOR_PROMPT,
        description="Executes real actions via Slack, Jira, and Calendar tools",
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
        parts=[types.Part(text=instructions)]
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
                print("[TOOL OPERATOR] All actions completed")

    return {"summary": response_text, "action_log": ACTION_LOG}

async def main():
    instructions = """
    Take these actions immediately:
    1. Reassign Jira ticket #42 from Alice Smith to Bob Johnson with comment 'Reassigned due to Alice being sick'
    2. Update Jira ticket #42 status to 'In Progress'
    3. Send Slack message to channel 'engineering-critical' saying: 'CRITICAL: Bug #42 reassigned to Bob Johnson. Alice is out sick. EOD deadline.'
    4. Create a 15-minute calendar event called 'Bug #42 Emergency Huddle' for Bob Johnson and Project Manager
    """

    result = await run_tool_operator(instructions)
    print("\n" + "=" * 50)
    print("TOOL OPERATOR SUMMARY:")
    print("=" * 50)
    print(result["summary"])
    print("\nACTION LOG:")
    for action in result["action_log"]:
        print(f"  - {action['tool']}: {action['status']}")

if __name__ == "__main__":
    asyncio.run(main())