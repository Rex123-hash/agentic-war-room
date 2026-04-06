import os
import sys
import sqlite3
import uuid
import requests
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.data_store import (
    get_all_tasks,
    add_task,
    update_task,
    delete_task,
    get_all_team_members,
    add_team_member,
    update_team_member_availability,
    delete_team_member,
    get_action_logs,
)

API_URL = "http://localhost:8080/analyze"
DAILY_URL = "http://localhost:8080/analyze-daily"
MCP_URL = "http://localhost:8080/analyze-mcp"
DB_PATH = "database/warroom.db"


@st.cache_data(show_spinner=False, ttl=5)
def cached_agent_runs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT agent_name, stage, message, created_at
        FROM agent_runs
        ORDER BY id ASC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@st.cache_data(show_spinner=False, ttl=5)
def cached_metrics():
    tasks = get_all_tasks()
    team = get_all_team_members()
    actions = get_action_logs(limit=200)

    total_tasks = len(tasks)
    open_tasks = len([t for t in tasks if t.get("status") != "Closed"])
    critical_open = len(
        [
            t for t in tasks
            if t.get("priority") == "Critical" and t.get("status") != "Closed"
        ]
    )
    available_team = len(
        [
            member for member in team
            if member.get("available") in [True, 1, "Available"]
        ]
    )
    logged_actions = len(actions)

    return total_tasks, open_tasks, critical_open, available_team, logged_actions


@st.cache_data(show_spinner=False, ttl=5)
def cached_tasks():
    return get_all_tasks()


@st.cache_data(show_spinner=False, ttl=5)
def cached_team_members():
    return get_all_team_members()


@st.cache_data(show_spinner=False, ttl=5)
def cached_action_logs(limit: int):
    return get_action_logs(limit=limit)


def fetch_agent_runs():
    return cached_agent_runs()


def parse_summary(summary: str):
    sections = {
        "status": "",
        "red_flags": [],
        "actions": [],
        "recommendations": [],
    }

    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    current = None

    for line in lines:
        if line.startswith("Status:"):
            sections["status"] = line.replace("Status:", "").strip()
        elif line.startswith("Red Flags:"):
            current = "red_flags"
        elif line.startswith("Actions Taken:"):
            current = "actions"
        elif line.startswith("Recommendations:"):
            current = "recommendations"
        elif line.startswith("-"):
            value = line.lstrip("-").strip()
            if current and value:
                sections[current].append(value)

    return sections


def apply_theme(theme_name: str):
    if theme_name == "Dark":
        bg = "#0A0E1A"
        card = "#111827"
        soft = "#0F172A"
        text = "#F9FAFB"
        subtext = "#9CA3AF"
        border = "#1F2937"
        accent = "#F97316"
        muted = "#4B5563"
        input_bg = "#1F2937"
    else:
        bg = "#F5F7FB"
        card = "#FFFFFF"
        soft = "#EEF2FF"
        text = "#0F172A"
        subtext = "#475569"
        border = "#D6DCE8"
        accent = "#F97316"
        muted = "#64748B"
        input_bg = "#FFFFFF"

    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility:hidden;}}
        footer {{visibility:hidden;}}
        header {{visibility:hidden;}}

        .stApp {{
            background:
                radial-gradient(circle at top right, {soft} 0%, transparent 28%),
                linear-gradient(180deg, {bg} 0%, {bg} 100%);
            color: {text};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .block-container {{
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}

        h1, h2, h3, h4, h5, h6, p, div, span, label, li {{
            color: {text};
        }}

        .topbar-card, .hero-card, .panel-card, .info-card, .about-card, .result-card {{
            background: {card};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 20px 24px;
        }}

        .topbar-card {{
            margin-bottom: 20px;
        }}

        .brand-line {{
            font-size: 30px;
            font-weight: 800;
            margin: 0;
            line-height: 1.1;
        }}

        .brand-light {{ color: {text}; }}
        .brand-accent {{ color: {accent}; }}

        .tagline {{
            color: {subtext};
            font-size: 13px;
            margin-top: 6px;
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: {text};
            margin-bottom: 10px;
        }}

        .hero-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .hero-copy, .subtle-copy {{
            color: {subtext};
            font-size: 14px;
            line-height: 1.6;
        }}

        .mini-title {{
            font-size: 14px;
            font-weight: 600;
            color: {text};
            margin-bottom: 8px;
        }}

        .badge-pill {{
            display: inline-block;
            background: {soft};
            color: {subtext};
            border: 1px solid {border};
            border-radius: 999px;
            padding: 5px 12px;
            font-size: 12px;
            margin-right: 8px;
            margin-bottom: 8px;
        }}

        .metric-card {{
            background: {card};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 18px 20px;
            min-height: 94px;
        }}

        .metric-label {{
            margin: 0;
            font-size: 11px;
            letter-spacing: 0.10em;
            text-transform: uppercase;
            color: {subtext};
        }}

        .metric-value {{
            margin: 6px 0 0;
            font-size: 30px;
            font-weight: 700;
            color: {text};
        }}

        .mode-pill {{
            display: inline-block;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 12px;
            border: 1px solid {border};
        }}

        .mode-interactive {{ background: rgba(249,115,22,0.12); color: #F97316; }}
        .mode-auto {{ background: rgba(16,185,129,0.12); color: #10B981; }}
        .mode-mcp {{ background: rgba(99,102,241,0.12); color: #6366F1; }}

        .footer-note {{
            text-align: center;
            color: {muted};
            font-size: 13px;
            padding-top: 16px;
        }}

        .stButton > button {{
            border-radius: 8px !important;
            font-weight: 600 !important;
            height: 42px !important;
            border: 1px solid {border} !important;
        }}

        .stTextArea textarea, .stTextInput input {{
            background: {input_bg} !important;
            color: {text} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}

        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {{
            background: {input_bg} !important;
            color: {text} !important;
            border: 1px solid {border} !important;
            border-radius: 8px !important;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {border};
            border-radius: 12px;
            overflow: hidden;
        }}

        div[data-testid="stRadio"] > div {{
            background: {card};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 6px;
        }}

        div[data-testid="stRadio"] label {{
            padding: 6px 14px;
            border-radius: 8px;
        }}

        div[role="radiogroup"] label > div:first-child {{
            display: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, border_color):
    return f"""
    <div class="metric-card" style="border-left:3px solid {border_color};">
        <p class="metric-label">{label}</p>
        <p class="metric-value">{value}</p>
    </div>
    """


def capability_badges(mode_label):
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.success("Multi-Agent")
    with b2:
        st.success("DB-Backed")
    with b3:
        st.success("Real Calendar")
    with b4:
        if mode_label == "MCP":
            st.success("MCP")
        elif mode_label == "AUTONOMOUS":
            st.success("Autonomous")
        else:
            st.info("Interactive")


def show_structured_result(summary: str, mode_label: str):
    parsed = parse_summary(summary)

    if mode_label == "MCP":
        st.markdown('<div class="mode-pill mode-mcp">MCP</div>', unsafe_allow_html=True)
    elif mode_label == "AUTONOMOUS":
        st.markdown('<div class="mode-pill mode-auto">AUTONOMOUS</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="mode-pill mode-interactive">INTERACTIVE</div>', unsafe_allow_html=True)

    normalized_status = parsed["status"].upper()
    if normalized_status:
        st.markdown(f"**Executive Status:** `{normalized_status}`")

    capability_badges(mode_label)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### Red Flags")
        if parsed["red_flags"]:
            for item in parsed["red_flags"]:
                st.error(item)
        else:
            st.info("No red flags listed.")

    with c2:
        st.markdown("### Actions Taken")
        if parsed["actions"]:
            for item in parsed["actions"]:
                st.success(item)
        else:
            st.info("No actions listed.")

    with c3:
        st.markdown("### Recommendations")
        if parsed["recommendations"]:
            for item in parsed["recommendations"]:
                st.info(item)
        else:
            st.info("No recommendations listed.")

    with st.expander("View Full Executive Summary"):
        st.text_area("Summary", value=summary, height=220)

    agent_runs = fetch_agent_runs()
    st.markdown("### Agent Activity Timeline")
    if agent_runs:
        for row in agent_runs:
            st.markdown(f"- **{row['agent_name']}** | `{row['stage']}` | {row['message']}")
    else:
        st.info("No agent activity recorded yet.")


st.set_page_config(page_title="Project War-Room", page_icon="🚨", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "draft_prompt" not in st.session_state:
    st.session_state.draft_prompt = ""

apply_theme(st.session_state.theme)

top1, top2, top3 = st.columns([6, 0.8, 1.1])
with top1:
    st.markdown(
        """
        <div class="topbar-card">
            <div class="brand-line"><span class="brand-light">Project </span><span class="brand-accent">War-Room</span></div>
            <div class="tagline">Multi-agent workspace for project monitoring, risk analysis, and operational response.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top2:
    icon = "🌙" if st.session_state.theme == "Dark" else "☀️"
    if st.button(icon, use_container_width=True):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
        st.rerun()
with top3:
    if st.button("⟳ Refresh", use_container_width=True):
        st.rerun()

task_count, open_count, critical_count, available_count, action_count = cached_metrics()

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(metric_card("Total Tasks", task_count, "#6366F1"), unsafe_allow_html=True)
with m2:
    st.markdown(metric_card("Open Tasks", open_count, "#F97316"), unsafe_allow_html=True)
with m3:
    st.markdown(metric_card("Critical Open", critical_count, "#EF4444"), unsafe_allow_html=True)
with m4:
    st.markdown(metric_card("Available Team", available_count, "#10B981"), unsafe_allow_html=True)
with m5:
    st.markdown(metric_card("Logged Actions", action_count, "#F59E0B"), unsafe_allow_html=True)

page = st.radio(
    "Navigation",
    ["Home", "Tasks", "Team", "Action Log", "Manage Data", "About"],
    horizontal=True,
    label_visibility="collapsed",
)

if page == "Home":
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-title">Ask about your real project situation</div>
                <div class="hero-copy">
                    Type your own project issue, delivery risk, blocked task, or team problem.
                    The system will analyze it using multiple agents and suggest next actions.
                </div>
                <span class="badge-pill">⚡ Real user input</span>
                <span class="badge-pill">🗄 Real local data flow</span>
                <span class="badge-pill">🤖 Multi-agent orchestration</span>
                <span class="badge-pill">📅 Real calendar action</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        quick1, quick2, quick3 = st.columns(3)
        with quick1:
            if st.button("Critical Bug", use_container_width=True):
                st.session_state.draft_prompt = "A critical issue is open, delivery is at risk today, and we need an action plan."
        with quick2:
            if st.button("Production Issue", use_container_width=True):
                st.session_state.draft_prompt = "Production is unstable, users are impacted, and immediate coordination is required."
        with quick3:
            if st.button("Sprint Delay", use_container_width=True):
                st.session_state.draft_prompt = "Sprint delivery is at risk because some tasks are blocked and deadlines are close."

        user_prompt = st.text_area(
            "Your Message",
            value=st.session_state.draft_prompt,
            height=100,
            placeholder="Example: We have 2 blocked tasks, one critical issue, and one unavailable team member. What should we do today?"
        )

        action1, action2, action3, action4 = st.columns(4)
        with action1:
            run_analysis = st.button("Analyze Situation", type="primary", use_container_width=True)
        with action2:
            run_daily = st.button("Run Daily Auto Check", use_container_width=True)
        with action3:
            run_mcp = st.button("Run MCP Ops Check", use_container_width=True)
        with action4:
            clear_chat = st.button("Clear", use_container_width=True)

        if clear_chat:
            st.session_state.chat_history = []
            st.session_state.draft_prompt = ""
            st.session_state.session_id = str(uuid.uuid4())
            st.cache_data.clear()
            st.rerun()

        st.markdown("### Conversation")
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history[-8:]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        else:
            st.info("No conversation yet. Type your own project situation and click Analyze Situation.")

    with right:
        st.markdown(
            """
            <div class="info-card">
                <div class="mini-title">💡 Prompt Tips</div>
                <div class="subtle-copy">
                    Mention the issue, who is affected, the deadline, and any staffing problem.
                    You can describe your own real situation here.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown(
            """
            <div class="info-card">
                <div class="mini-title">🚀 Current MVP Scope</div>
                <div class="subtle-copy">
                    Real local data, real action logging, ADK-based multi-agent orchestration,
                    MCP mode, and real Google Calendar emergency huddles.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if run_analysis:
        if not user_prompt.strip():
            st.warning("Please enter a real project situation first.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            st.session_state.draft_prompt = user_prompt

            with st.spinner("Coordinating agents..."):
                try:
                    response = requests.post(
                        API_URL,
                        json={
                            "goal": user_prompt,
                            "session_id": st.session_state.session_id,
                        },
                        timeout=45,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        summary = data["summary"]
                        st.session_state.chat_history.append({"role": "assistant", "content": summary})

                        if data["status"] == "fallback":
                            st.warning("Fallback mode is active because live model quota is exhausted or the request took too long.")
                        else:
                            st.success("Analysis completed successfully.")

                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        show_structured_result(summary, "INTERACTIVE")
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.text(response.text)

                except requests.exceptions.Timeout:
                    st.error("The request took too long. Please try MCP mode or try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure `python main.py` is running.")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

    if run_daily:
        with st.spinner("Running autonomous daily check..."):
            try:
                response = requests.post(DAILY_URL, timeout=45)

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]
                    st.session_state.chat_history.append({"role": "assistant", "content": summary})

                    if data["status"] == "fallback":
                        st.warning("Fallback mode is active because live model quota is exhausted or the request took too long.")
                    else:
                        st.success("Autonomous daily health check completed successfully.")

                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    show_structured_result(summary, "AUTONOMOUS")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.Timeout:
                st.error("Daily check took too long. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Make sure `python main.py` is running.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

    if run_mcp:
        mcp_goal = user_prompt.strip() or "Check urgent open tasks and team availability. If delivery risk is present, create an emergency huddle."

        with st.spinner("Running MCP operations..."):
            try:
                response = requests.post(
                    MCP_URL,
                    json={
                        "goal": mcp_goal,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=45,
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]
                    st.session_state.chat_history.append({"role": "assistant", "content": summary})

                    if data["status"] == "fallback":
                        st.warning("Fallback mode is active because live model quota is exhausted or the request took too long.")
                    else:
                        st.success("MCP operations check completed successfully.")

                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown("### MCP Result")
                    capability_badges("MCP")
                    st.text_area("MCP Summary", value=summary, height=260)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"API Error: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.Timeout:
                st.error("MCP check took too long. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Make sure `python main.py` is running.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

elif page == "Tasks":
    st.markdown('<div class="section-title">Current Tasks</div>', unsafe_allow_html=True)
    tasks = cached_tasks()
    tasks = [
        {
            "id": task.get("id", ""),
            "title": task.get("title", ""),
            "assignee": task.get("assignee", ""),
            "status": task.get("status", ""),
            "priority": task.get("priority", ""),
            "deadline": task.get("deadline", ""),
        }
        for task in tasks
    ]
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    if tasks:
        st.dataframe(tasks, use_container_width=True)
    else:
        st.info("No tasks found.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Team":
    st.markdown('<div class="section-title">Team Status</div>', unsafe_allow_html=True)
    raw_team = cached_team_members()
    team = [
        {
            "id": member.get("id", ""),
            "name": member.get("name", ""),
            "role": member.get("role", ""),
            "email": member.get("email", ""),
            "skills": member.get("skills", ""),
            "availability": "Available" if member.get("available") in [True, 1, "Available"] else "Unavailable",
        }
        for member in raw_team
    ]
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    if team:
        st.dataframe(team, use_container_width=True)
    else:
        st.info("No team members found.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Action Log":
    st.markdown('<div class="section-title">Recent Action Log</div>', unsafe_allow_html=True)
    actions = cached_action_logs(20)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    if actions:
        st.dataframe(actions, use_container_width=True)
        st.markdown("### 🔗 Real External Actions")
        calendar_rows = [
            row for row in cached_action_logs(50)
            if row.get("tool") == "GoogleCalendar"
        ][:10]
        if calendar_rows:
            for row in calendar_rows:
                details = row["details"]
                if "event_link=" in details:
                    event_link = details.split("event_link=")[-1].strip()
                    st.markdown(f"[Open Google Calendar Event]({event_link})")
                else:
                    st.info(details)
        else:
            st.info("No real external action links found yet.")
    else:
        st.info("No actions logged yet.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Manage Data":
    st.markdown('<div class="section-title">Manage Project Data</div>', unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Add Task")
        with st.form("add_task_form"):
            title = st.text_input("Task Title")
            assignee = st.text_input("Assignee")
            status = st.selectbox("Status", ["Open", "In Progress", "Blocked", "Closed"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            deadline = st.text_input("Deadline", placeholder="2026-04-10")
            description = st.text_area("Description", height=90)
            submit_task = st.form_submit_button("Add Task", use_container_width=True)
            if submit_task:
                if not title.strip():
                    st.warning("Task title is required.")
                else:
                    add_task(
                        title.strip(),
                        assignee.strip(),
                        status,
                        priority,
                        deadline.strip(),
                        description.strip(),
                    )
                    st.cache_data.clear()
                    st.success("Task added successfully.")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Update Task")
        task_options = cached_tasks()
        if task_options:
            task_map = {f"{task['id']} - {task['title']} ({task['status']})": task for task in task_options}
            with st.form("update_task_form"):
                selected_task_label = st.selectbox("Select Task", list(task_map.keys()))
                selected_task = task_map[selected_task_label]
                new_assignee = st.text_input("New Assignee", value=selected_task.get("assignee", "") or "")
                new_status = st.selectbox(
                    "New Status",
                    ["Open", "In Progress", "Blocked", "Closed"],
                    index=["Open", "In Progress", "Blocked", "Closed"].index(selected_task["status"])
                    if selected_task.get("status") in ["Open", "In Progress", "Blocked", "Closed"] else 0
                )
                submit_update_task = st.form_submit_button("Update Task", use_container_width=True)
                if submit_update_task:
                    if not new_assignee.strip():
                        st.warning("Assignee cannot be empty while updating a task.")
                    else:
                        update_task(str(selected_task["id"]), new_assignee.strip(), new_status)
                        st.cache_data.clear()
                        st.success("Task updated successfully.")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Delete Task")
        delete_task_options = cached_tasks()
        if delete_task_options:
            delete_task_map = {f"{task['id']} - {task['title']}": task["id"] for task in delete_task_options}
            with st.form("delete_task_form"):
                selected_delete_task = st.selectbox("Select Task To Delete", list(delete_task_map.keys()))
                confirm_delete_task = st.checkbox("⚠️ I understand this will be permanently deleted")
                submit_delete_task = st.form_submit_button("Delete Task", use_container_width=True)
                if submit_delete_task:
                    if not confirm_delete_task:
                        st.warning("Please confirm task deletion.")
                    else:
                        delete_task(str(delete_task_map[selected_delete_task]))
                        st.cache_data.clear()
                        st.success("Task deleted successfully.")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Add Team Member")
        with st.form("add_team_form"):
            name = st.text_input("Name")
            role = st.text_input("Role")
            email = st.text_input("Email")
            skills = st.text_input("Skills", placeholder="python,react,debugging")
            available = st.selectbox("Available", ["Yes", "No"])
            submit_member = st.form_submit_button("Add Team Member", use_container_width=True)
            if submit_member:
                if not name.strip():
                    st.warning("Team member name is required.")
                else:
                    add_team_member(
                        name.strip(),
                        role.strip(),
                        email.strip(),
                        skills.strip(),
                        True if available == "Yes" else False,
                    )
                    st.cache_data.clear()
                    st.success("Team member added successfully.")
                    st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.session_state.member_name = ""
                    st.session_state.member_role = ""
                    st.session_state.member_email = ""
                    st.session_state.member_skills = ""
                    st.cache_data.clear()
                    st.success("Team member added successfully.")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Update Team Availability")
        member_options = cached_team_members()
        if member_options:
            member_map = {f"{member['id']} - {member['name']}": member for member in member_options}
            with st.form("update_member_form"):
                selected_member_label = st.selectbox("Select Team Member", list(member_map.keys()))
                selected_member = member_map[selected_member_label]
                selected_available = selected_member.get("available")
                new_availability = st.selectbox(
                    "Availability",
                    ["Available", "Unavailable"],
                    index=0 if selected_available in [True, 1, "Available"] else 1
                )
                submit_update_member = st.form_submit_button("Update Availability", use_container_width=True)
                if submit_update_member:
                    update_team_member_availability(
                        str(selected_member["id"]),
                        True if new_availability == "Available" else False,
                    )
                    st.cache_data.clear()
                    st.success("Team member availability updated successfully.")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Delete Team Member")
        delete_member_options = cached_team_members()
        if delete_member_options:
            delete_member_map = {f"{member['id']} - {member['name']}": member["id"] for member in delete_member_options}
            with st.form("delete_member_form"):
                selected_delete_member = st.selectbox("Select Team Member To Delete", list(delete_member_map.keys()))
                confirm_delete_member = st.checkbox("⚠️ I understand this will be permanently deleted")
                submit_delete_member = st.form_submit_button("Delete Team Member", use_container_width=True)
                if submit_delete_member:
                    if not confirm_delete_member:
                        st.warning("Please confirm team member deletion.")
                    else:
                        delete_team_member(str(delete_member_map[selected_delete_member]))
                        st.cache_data.clear()
                        st.success("Team member deleted successfully.")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "About":
    st.markdown('<div class="section-title">About Project War-Room</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(
            """
            <div class="about-card">
                <div class="mini-title">What You Can Do</div>
                <div class="subtle-copy">
                   Analyze delivery risks, review blocked work, monitor team availability,
                    run operational checks, and coordinate urgent responses from a single dashboard
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        st.markdown(
            """
            <div class="about-card">
                <div class="mini-title">How It Works</div>
                <div class="subtle-copy">
                    The Commander Agent coordinates Data Miner, Context Agent, and Tool Operator
                    to analyze project state, retrieve supporting context, and produce structured operational guidance.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a3:
        st.markdown(
            """
            <div class="about-card">
                <div class="mini-title">Best For</div>
                <div class="subtle-copy">
                    Project leads, engineering managers, startup teams, operations teams,
                    and hackathon demos that need an AI-powered project operations workflow.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown(
            """
            <div class="about-card">
               <div class="mini-title">Current Implementation</div>
                <div class="subtle-copy">
                    ✅ Firestore-backed project data<br>
                    ✅ FastAPI + Streamlit workflow<br>
                    ✅ ADK-based multi-agent orchestration<br>
                    ✅ Google Calendar coordination action<br>
                    ✅ MCP-based operations mode<br>
                    ✅ Action logging and agent activity tracking<br>
                    ✅ Interactive and autonomous analysis modes
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b2:
        st.markdown(
            """
            <div class="about-card">
                <div class="mini-title">Future Scope</div>
                <div class="subtle-copy">
                    → Slack integration<br>
                    → Jira integration<br>
                    → Vector search based context retrieval<br>
                    → Multi-project workspaces<br>
                    → Authentication and access control<br>
                    → Cloud-native production hardening
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    '<div class="footer-note">Built with ADK · FastAPI · Streamlit · SQLite · Google ADK · MCP</div>',
    unsafe_allow_html=True
)
