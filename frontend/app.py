import sqlite3
import requests
import streamlit as st

API_URL = "http://localhost:8080/analyze"
DB_PATH = "database/warroom.db"


def fetch_data(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute(query, params).fetchone()
    conn.close()
    return row


def execute_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

def fetch_agent_runs():
    return fetch_data("""
        SELECT agent_name, stage, message, created_at
        FROM agent_runs
        ORDER BY id ASC
    """)


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
        bg = "#081120"
        card = "#0f172a"
        soft = "#111c34"
        text = "#f8fafc"
        subtext = "#cbd5e1"
        border = "#24324a"
        accent = "#f97316"
        muted = "#94a3b8"
        button_text = "#f8fafc"
        secondary_button_bg = "#182235"
    else:
        bg = "#f6f8fc"
        card = "#ffffff"
        soft = "#eef2ff"
        text = "#0f172a"
        subtext = "#475569"
        border = "#dbe3ef"
        accent = "#dc2626"
        muted = "#64748b"
        button_text = "#0f172a"
        secondary_button_bg = "#ffffff"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top right, {soft} 0%, {bg} 35%),
                linear-gradient(180deg, {bg} 0%, {bg} 100%);
            color: {text};
        }}

        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 2rem;
            max-width: 1280px;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        h1, h2, h3, h4, h5, h6, p, label, div, span {{
            color: {text};
        }}

        .topbar {{
            background: {card};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 1rem;
        }}

        .brand {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {text};
            margin: 0;
        }}

        .brand-accent {{
            color: {accent};
        }}

        .tagline {{
            color: {subtext};
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }}

        .hero-card {{
            background: linear-gradient(135deg, {card} 0%, {soft} 100%);
            border: 1px solid {border};
            border-radius: 22px;
            padding: 1.2rem 1.2rem 1rem 1.2rem;
            margin-bottom: 1rem;
        }}

        .hero-title {{
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.4rem;
        }}

        .hero-copy {{
            color: {subtext};
            font-size: 1rem;
            line-height: 1.6;
            max-width: 850px;
        }}

        .pill {{
            display: inline-block;
            margin-right: 0.45rem;
            margin-top: 0.6rem;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            border: 1px solid {border};
            background: {card};
            color: {subtext};
            font-size: 0.82rem;
            font-weight: 600;
        }}

        .info-card {{
            background: {card};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 1rem;
        }}

        .info-title {{
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }}

        .info-copy {{
            color: {subtext};
            line-height: 1.55;
            font-size: 0.93rem;
        }}

        div[data-testid="stMetric"] {{
            background: {card};
            border: 1px solid {border};
            border-radius: 16px;
            padding: 0.8rem;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {border};
            border-radius: 14px;
            overflow: hidden;
        }}

        textarea, input {{
            border-radius: 12px !important;
        }}

        div[data-baseweb="select"] > div {{
            border-radius: 12px !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            overflow-x: auto;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 12px 12px 0 0;
            padding-left: 16px;
            padding-right: 16px;
        }}

        .footer-note {{
            text-align: center;
            color: {muted};
            font-size: 0.84rem;
            padding-top: 0.5rem;
        }}

        div.stButton > button {{
            border-radius: 12px !important;
        }}

        div.stButton > button[kind="secondary"] {{
            background: {secondary_button_bg} !important;
            color: {button_text} !important;
            border: 1px solid {border} !important;
        }}

        div.stButton > button p {{
            color: inherit !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Project War-Room",
    page_icon="🚨",
    layout="wide"
)

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "goal" not in st.session_state:
    st.session_state.goal = ""

apply_theme(st.session_state.theme)

top1, top2, top3 = st.columns([6, 0.7, 0.9])

with top1:
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">Project <span class="brand-accent">War-Room</span></div>
            <div class="tagline">Multi-agent workspace for project monitoring, risk analysis, and operational response.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top2:
    theme_icon = "🌙" if st.session_state.theme == "Dark" else "☀️"
    if st.button(theme_icon, use_container_width=True):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
        st.rerun()

with top3:
    if st.button("Refresh", use_container_width=True):
        st.rerun()

task_count = fetch_one("SELECT COUNT(*) FROM tasks")[0]
open_count = fetch_one("SELECT COUNT(*) FROM tasks WHERE status != 'Closed'")[0]
critical_count = fetch_one("SELECT COUNT(*) FROM tasks WHERE priority = 'Critical' AND status != 'Closed'")[0]
available_count = fetch_one("SELECT COUNT(*) FROM team_members WHERE available = 1")[0]
action_count = fetch_one("SELECT COUNT(*) FROM action_log")[0]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Tasks", task_count)
m2.metric("Open Tasks", open_count)
m3.metric("Critical Open", critical_count)
m4.metric("Available Team", available_count)
m5.metric("Logged Actions", action_count)

page = st.radio(
    "Navigation",
    ["Home", "Tasks", "Team", "Action Log", "Manage Data", "About"],
    horizontal=True,
    label_visibility="collapsed"
)

if page == "Home":
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-title">Analyze a situation in seconds</div>
                <div class="hero-copy">
                    Describe a project problem in plain English and let the system assess risk,
                    check context, and recommend the next best actions. You can also run the
                    autonomous daily health check without typing anything.
                </div>
                <div class="pill">Easy for non-technical users</div>
                <div class="pill">Real local data flow</div>
                <div class="pill">Multi-agent orchestration</div>
                <div class="pill">Autonomous daily check</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        quick1, quick2, quick3 = st.columns(3)
        with quick1:
            if st.button("Critical Bug", use_container_width=True):
                st.session_state.goal = (
                    "Our lead developer Alice is out sick today. Critical bug #42 is still open. "
                    "The deadline is end of day. Analyze the situation and take necessary internal actions."
                )
        with quick2:
            if st.button("Production Issue", use_container_width=True):
                st.session_state.goal = (
                    "Production is unstable, users are reporting failures, and the on-call lead is busy. "
                    "Analyze the situation and suggest immediate actions."
                )
        with quick3:
            if st.button("Sprint Delay", use_container_width=True):
                st.session_state.goal = (
                    "Sprint deadline is tomorrow, blocked tasks remain open, and code reviews are pending. "
                    "Analyze project risk and recommend actions."
                )

        goal = st.text_area(
            "Your prompt",
            value=st.session_state.get("goal", ""),
            height=95,
            placeholder="Example: A critical task is blocked and two team members are unavailable. What should we do today?"
        )

        analyze_col, auto_col, mcp_col = st.columns(3)
        with analyze_col:
            run_analysis = st.button("Analyze Situation", type="primary", use_container_width=True)
        with auto_col:
            run_daily = st.button("Run Daily Auto Check", use_container_width=True)
        with mcp_col:
            run_mcp = st.button("Run MCP Ops Check", use_container_width=True)

    with right:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Prompt Tips</div>
                <div class="info-copy">
                    Mention the issue, who is affected, the deadline, and any staffing problem.
                    Short and specific prompts usually give the best result.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Current MVP Scope</div>
                <div class="info-copy">
                    This version works with real local data, real internal action logging,
                    ADK-based multi-agent orchestration, a real Google Calendar action,
                    and an autonomous daily health check mode.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if run_analysis:
        if not goal.strip():
            st.warning("Please enter a situation first.")
        else:
            with st.spinner("Analyzing with the multi-agent system..."):
                try:
                    response = requests.post(API_URL, json={"goal": goal}, timeout=300)

                    if response.status_code == 200:
                        data = response.json()
                        summary = data["summary"]
                        status = data["status"]
                        parsed = parse_summary(summary)

                        if status == "fallback":
                            st.warning("Fallback mode is active because live model quota is exhausted.")
                        else:
                            st.success("Analysis completed successfully.")

                        normalized_status = parsed["status"].upper()
                        if normalized_status:
                            st.markdown(f"*Executive Status:* {normalized_status}")

                        badge1, badge2, badge3, badge4 = st.columns(4)
                        with badge1:
                            st.success("Multi-Agent")
                        with badge2:
                            st.success("DB-Backed")
                        with badge3:
                            st.success("Real Calendar")
                        with badge4:
                            st.info("Interactive")

                        a1, a2, a3 = st.columns(3)
                        with a1:
                            st.markdown("### Red Flags")
                            if parsed["red_flags"]:
                                for item in parsed["red_flags"]:
                                    st.error(item)
                            else:
                                st.info("No red flags listed.")
                        with a2:
                            st.markdown("### Actions Taken")
                            if parsed["actions"]:
                                for item in parsed["actions"]:
                                    st.success(item)
                            else:
                                st.info("No actions listed.")
                        with a3:
                            st.markdown("### Recommendations")
                            if parsed["recommendations"]:
                                for item in parsed["recommendations"]:
                                    st.info(item)
                            else:
                                st.info("No recommendations listed.")

                        with st.expander("View Full Executive Summary"):
                            st.text_area("Summary", value=summary, height=220)

                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.text(response.text)

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure python main.py is running.")
                except requests.exceptions.Timeout:
                    st.error("Request timed out.")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

    if run_daily:
        with st.spinner("Running autonomous daily health check..."):
            try:
                response = requests.post("http://localhost:8080/analyze-daily", timeout=300)

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]
                    status = data["status"]
                    parsed = parse_summary(summary)

                    if status == "fallback":
                        st.warning("Fallback mode is active because live model quota is exhausted.")
                    else:
                        st.success("Autonomous daily health check completed successfully.")

                    normalized_status = parsed["status"].upper()
                    if normalized_status:
                        st.markdown(f"*Executive Status:* {normalized_status}")

                    badge1, badge2, badge3, badge4 = st.columns(4)
                    with badge1:
                        st.success("Multi-Agent")
                    with badge2:
                        st.success("DB-Backed")
                    with badge3:
                        st.success("Real Calendar")
                    with badge4:
                        st.success("Autonomous")

                    a1, a2, a3 = st.columns(3)
                    with a1:
                        st.markdown("### Red Flags")
                        if parsed["red_flags"]:
                            for item in parsed["red_flags"]:
                                st.error(item)
                        else:
                            st.info("No red flags listed.")
                    with a2:
                        st.markdown("### Actions Taken")
                        if parsed["actions"]:
                            for item in parsed["actions"]:
                                st.success(item)
                        else:
                            st.info("No actions listed.")
                    with a3:
                        st.markdown("### Recommendations")
                        if parsed["recommendations"]:
                            for item in parsed["recommendations"]:
                                st.info(item)
                        else:
                            st.info("No recommendations listed.")

                    with st.expander("View Full Executive Summary"):
                        st.text_area("Daily Summary", value=summary, height=220)

                else:
                    st.error(f"API Error: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Make sure python main.py is running.")
            except requests.exceptions.Timeout:
                st.error("Request timed out.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

    if run_mcp:
        mcp_goal = goal.strip() or "Check urgent open tasks and team availability. If delivery risk is present, create an emergency huddle for amaank2405@gmail.com."

        with st.spinner("Running MCP-powered operations check..."):
            try:
                response = requests.post(
                    "http://localhost:8080/analyze-mcp",
                    json={"goal": mcp_goal},
                    timeout=300
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]
                    status = data["status"]

                    if status == "fallback":
                        st.warning("Fallback mode is active because live model quota is exhausted.")
                    else:
                        st.success("MCP operations check completed successfully.")

                    st.markdown("*Execution Mode:* MCP")

                    badge1, badge2, badge3, badge4 = st.columns(4)
                    with badge1:
                        st.success("Multi-Agent")
                    with badge2:
                        st.success("DB-Backed")
                    with badge3:
                        st.success("Real Calendar")
                    with badge4:
                        st.success("MCP")

                    st.markdown("### MCP Result")
                    st.text_area("MCP Summary", value=summary, height=260)

                else:
                    st.error(f"API Error: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Make sure python main.py is running.")
            except requests.exceptions.Timeout:
                st.error("Request timed out.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")
elif page == "Tasks":
    st.subheader("Current Tasks")
    tasks = fetch_data("""
        SELECT id, title, assignee, status, priority, deadline
        FROM tasks
        ORDER BY
            CASE priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END,
            id
    """)
    if tasks:
        st.dataframe(tasks, use_container_width=True)
    else:
        st.info("No tasks found.")

elif page == "Team":
    st.subheader("Team Status")
    team = fetch_data("""
        SELECT
            id,
            name,
            role,
            email,
            skills,
            CASE WHEN available = 1 THEN 'Available' ELSE 'Unavailable' END AS availability
        FROM team_members
        ORDER BY id
    """)
    if team:
        st.dataframe(team, use_container_width=True)
    else:
        st.info("No team members found.")

elif page == "Action Log":
    st.subheader("Recent Action Log")

    actions = fetch_data("""
        SELECT id, tool, action, details, timestamp
        FROM action_log
        ORDER BY id DESC
        LIMIT 20
    """)

    if actions:
        st.dataframe(actions, use_container_width=True)

        st.markdown("### Real External Actions")
        calendar_rows = fetch_data("""
            SELECT id, details, timestamp
            FROM action_log
            WHERE tool = 'GoogleCalendar'
            ORDER BY id DESC
            LIMIT 10
        """)

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

elif page == "Manage Data":
    st.subheader("Manage Project Data")

    left, right = st.columns(2)

    with left:
        st.markdown("### Add Task")
        with st.form("add_task_form"):
            title = st.text_input("Task Title")
            assignee = st.text_input("Assignee")
            status = st.selectbox("Status", ["Open", "In Progress", "Blocked", "Closed"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            deadline = st.text_input("Deadline", placeholder="2026-04-10")
            description = st.text_area("Description", height=80)
            submit_task = st.form_submit_button("Add Task")

            if submit_task:
                if not title.strip():
                    st.warning("Task title is required.")
                else:
                    execute_query(
                        """
                        INSERT INTO tasks (title, assignee, status, priority, deadline, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (title.strip(), assignee.strip(), status, priority, deadline.strip(), description.strip())
                    )
                    st.success("Task added successfully.")
                    st.rerun()

        st.markdown("---")

        st.markdown("### Update Task")
        task_options = fetch_data("SELECT id, title, assignee, status FROM tasks ORDER BY id")
        if task_options:
            task_map = {
                f"{task['id']} - {task['title']} ({task['status']})": task for task in task_options
            }
            with st.form("update_task_form"):
                selected_task_label = st.selectbox("Select Task", list(task_map.keys()))
                selected_task = task_map[selected_task_label]
                new_assignee = st.text_input("New Assignee", value=selected_task["assignee"] or "")
                new_status = st.selectbox(
                    "New Status",
                    ["Open", "In Progress", "Blocked", "Closed"],
                    index=["Open", "In Progress", "Blocked", "Closed"].index(selected_task["status"])
                    if selected_task["status"] in ["Open", "In Progress", "Blocked", "Closed"] else 0
                )
                submit_update_task = st.form_submit_button("Update Task")

                if submit_update_task:
                    if not new_assignee.strip():
                        st.warning("Assignee cannot be empty while updating a task.")
                    else:
                        execute_query(
                            "UPDATE tasks SET assignee = ?, status = ? WHERE id = ?",
                            (new_assignee.strip(), new_status, selected_task["id"])
                        )
                        st.success("Task updated successfully.")
                        st.rerun()

        st.markdown("---")

        st.markdown("### Delete Task")
        delete_task_options = fetch_data("SELECT id, title FROM tasks ORDER BY id")
        if delete_task_options:
            delete_task_map = {f"{task['id']} - {task['title']}": task["id"] for task in delete_task_options}
            with st.form("delete_task_form"):
                selected_delete_task = st.selectbox("Select Task To Delete", list(delete_task_map.keys()))
                confirm_delete_task = st.checkbox("I understand this task will be permanently deleted")
                submit_delete_task = st.form_submit_button("Delete Task")

                if submit_delete_task:
                    if not confirm_delete_task:
                        st.warning("Please confirm task deletion.")
                    else:
                        execute_query("DELETE FROM tasks WHERE id = ?", (delete_task_map[selected_delete_task],))
                        st.success("Task deleted successfully.")
                        st.rerun()

    with right:
        st.markdown("### Add Team Member")
        with st.form("add_team_form"):
            name = st.text_input("Name")
            role = st.text_input("Role")
            email = st.text_input("Email")
            skills = st.text_input("Skills", placeholder="python,react,debugging")
            available = st.selectbox("Available", ["Yes", "No"])
            submit_member = st.form_submit_button("Add Team Member")

            if submit_member:
                if not name.strip():
                    st.warning("Team member name is required.")
                else:
                    execute_query(
                        """
                        INSERT INTO team_members (name, role, email, skills, available)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (name.strip(), role.strip(), email.strip(), skills.strip(), 1 if available == "Yes" else 0)
                    )
                    st.success("Team member added successfully.")
                    st.rerun()

        st.markdown("---")

        st.markdown("### Update Team Availability")
        member_options = fetch_data("SELECT id, name, available FROM team_members ORDER BY id")
        if member_options:
            member_map = {f"{m['id']} - {m['name']}": m for m in member_options}
            with st.form("update_member_form"):
                selected_member_label = st.selectbox("Select Team Member", list(member_map.keys()))
                selected_member = member_map[selected_member_label]
                new_availability = st.selectbox(
                    "Availability",
                    ["Available", "Unavailable"],
                    index=0 if selected_member["available"] == 1 else 1
                )
                submit_update_member = st.form_submit_button("Update Availability")

                if submit_update_member:
                    execute_query(
                        "UPDATE team_members SET available = ? WHERE id = ?",
                        (1 if new_availability == "Available" else 0, selected_member["id"])
                    )
                    st.success("Team member availability updated successfully.")
                    st.rerun()

        st.markdown("---")

        st.markdown("### Delete Team Member")
        delete_member_options = fetch_data("SELECT id, name FROM team_members ORDER BY id")
        if delete_member_options:
            delete_member_map = {f"{m['id']} - {m['name']}": m["id"] for m in delete_member_options}
            with st.form("delete_member_form"):
                selected_delete_member = st.selectbox("Select Team Member To Delete", list(delete_member_map.keys()))
                confirm_delete_member = st.checkbox("I understand this team member will be permanently deleted")
                submit_delete_member = st.form_submit_button("Delete Team Member")

                if submit_delete_member:
                    if not confirm_delete_member:
                        st.warning("Please confirm team member deletion.")
                    else:
                        execute_query("DELETE FROM team_members WHERE id = ?", (delete_member_map[selected_delete_member],))
                        st.success("Team member deleted successfully.")
                        st.rerun()

elif page == "About":
    st.subheader("About Project War-Room")

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">What You Can Do</div>
                <div class="info-copy">
                    Analyze delivery risks, investigate blocked work, handle critical bugs,
                    review team availability, and maintain a live operational history.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a2:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">How It Works</div>
                <div class="info-copy">
                    The Commander Agent coordinates Data Miner, Context Agent, and Tool Operator
                    to convert a plain-English situation into structured project action.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a3:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Best For</div>
                <div class="info-copy">
                    Project leads, engineering managers, startup teams, operations teams,
                    and hackathon demos needing a simple but real local MVP.
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
            **What is real in this MVP**
            - Real local database reads
            - Real local database writes
            - Real action logging
            - Real FastAPI + Streamlit flow
            - ADK-based agent orchestration
            """
        )

    with b2:
        st.markdown(
            """
            **Future scope**
            - Slack integration
            - Jira integration
            - Google Calendar integration
            - AlloyDB migration
            - Vector search / semantic retrieval
            - Multi-user auth and project spaces
            """
        )

st.markdown("---")
st.markdown(
    '<div class="footer-note">Built with ADK, FastAPI, Streamlit, and SQLite for a clean local MVP workflow.</div>',
    unsafe_allow_html=True
)
