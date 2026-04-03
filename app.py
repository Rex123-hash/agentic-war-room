import streamlit as st
import requests

st.set_page_config(
    page_title="Project War-Room",
    page_icon="🚨",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #FF4B4B;
    text-align: center;
    padding: 1rem;
}
.sub-header {
    text-align: center;
    color: #888;
    margin-bottom: 2rem;
}
.scenario-card {
    background: #1E1E1E;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🚨 Agentic Project War-Room</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your AI-powered Project Manager — just describe your problem, AI handles the rest</div>', unsafe_allow_html=True)

st.markdown("---")

# --- Quick scenario buttons ---
st.subheader("⚡ Quick Scenarios — Click to Auto-Fill")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🤒 Developer Sick + Critical Bug", use_container_width=True):
        st.session_state.goal = "Our lead developer Alice is out sick today. Critical bug #42 (Frontend UI Crash) is still open and affects 15% of users. The deadline is end of day. Please analyse the situation and take all necessary actions."

with col2:
    if st.button("🔥 Production Server Down", use_container_width=True):
        st.session_state.goal = "Our production server is down. Users cannot access the application. The DevOps lead is in a meeting. We need immediate crisis response and stakeholder communication."

with col3:
    if st.button("📅 Sprint Deadline at Risk", use_container_width=True):
        st.session_state.goal = "Sprint 23 ends tomorrow but 40% of tasks are still open. Two developers are blocked waiting for code review. The client demo is scheduled for tomorrow at 2 PM. What should we do?"

col4, col5, col6 = st.columns(3)

with col4:
    if st.button("👥 Team Conflict Detected", use_container_width=True):
        st.session_state.goal = "Two senior developers are in disagreement about the architecture of the new payment module. The project is blocked. We have a client deadline in 3 days. Help resolve this."

with col5:
    if st.button("📊 Weekly Project Health Check", use_container_width=True):
        st.session_state.goal = "Give me a complete health check of our current project. Check all open tasks, team availability, upcoming deadlines, and any risks. Summarize the current project status."

with col6:
    if st.button("🚀 New Feature Emergency", use_container_width=True):
        st.session_state.goal = "The client just called and wants a new login feature added urgently before tomorrow's demo. Our team is already at full capacity. How do we handle this?"

st.markdown("---")

# --- Main input ---
st.subheader("💬 Or Describe Your Own Situation")
st.markdown("Just write what's happening in plain English — no technical knowledge needed")

goal = st.text_area(
    "",
    value=st.session_state.get("goal", ""),
    placeholder="Example: Our project manager just resigned and we have a client presentation tomorrow. What should we do?",
    height=150
)

# --- How it works section ---
with st.expander("🤖 How does this work?"):
    st.markdown("""
    When you click *Activate War-Room*, our AI system does this automatically:
    
    1. *Commander Agent* receives your situation and breaks it into tasks
    2. *Data Miner Agent* checks all current tasks, deadlines, and team availability  
    3. *Context Agent* searches past meeting notes and company SOPs
    4. *Tool Operator Agent* takes real actions — reassigns tickets, sends Slack alerts, schedules meetings
    5. You get a complete *Executive Summary* with status, risks, and recommendations
    
    All of this happens in seconds — no manual work needed!
    """)

# --- Activate button ---
st.markdown("")
activate = st.button("🚀 Activate War-Room", type="primary", use_container_width=True)

if activate:
    if not goal.strip():
        st.warning("⚠️ Please describe your situation first — either click a quick scenario or type your own!")
    else:
        st.markdown("---")
        st.subheader("⚙️ Agents Working...")

        progress_bar = st.progress(0)
        status_text = st.empty()

        col1, col2, col3, col4 = st.columns(4)
        agent1 = col1.empty()
        agent2 = col2.empty()
        agent3 = col3.empty()
        agent4 = col4.empty()

        agent1.info("🧠 Commander\n\nInitialising...")
        agent2.info("🗄️ Data Miner\n\nWaiting...")
        agent3.info("📚 Context Agent\n\nWaiting...")
        agent4.info("🔧 Tool Operator\n\nWaiting...")

        progress_bar.progress(25)
        status_text.markdown("Commander Agent analysing situation...")

        try:
            import time
            time.sleep(1)
            agent1.success("🧠 Commander\n\n✅ Delegating tasks")
            agent2.warning("🗄️ Data Miner\n\n⚙️ Querying DB...")
            progress_bar.progress(50)
            status_text.markdown("Data Miner fetching tasks and team info...")

            response = requests.post(
                "https://war-room-af7evfwqwq-uc.a.run.app/analyze",
                json={"goal": goal},
                timeout=180
            )

            progress_bar.progress(75)
            agent2.success("🗄️ Data Miner\n\n✅ Data fetched")
            agent3.success("📚 Context Agent\n\n✅ SOPs found")
            status_text.markdown("Tool Operator executing actions...")

            import time
            time.sleep(0.5)
            agent4.success("🔧 Tool Operator\n\n✅ Actions taken")
            progress_bar.progress(100)
            status_text.markdown("✅ All agents completed!")

            if response.status_code == 200:
                data = response.json()
                summary = data["summary"]

                st.markdown("---")
                st.subheader("📊 Executive Summary")

                # Status badge
                if "Status: RED" in summary:
                    st.error("🔴 *Project Status: RED* — Immediate action required!")
                elif "Status: YELLOW" in summary:
                    st.warning("🟡 *Project Status: YELLOW* — Attention needed")
                elif "Status: GREEN" in summary:
                    st.success("🟢 *Project Status: GREEN* — All good!")

                # Parse and display sections nicely
                sections = summary.split("\n")
                in_summary = False
                red_flags = []
                actions = []
                recommendations = []
                current_section = ""

                for line in sections:
                    if "Red Flags:" in line:
                        current_section = "flags"
                    elif "Actions Taken:" in line:
                        current_section = "actions"
                    elif "Recommendations:" in line:
                        current_section = "recs"
                    elif line.strip().startswith("-") or line.strip().startswith("*"):
                        item = line.strip().lstrip("-*").strip()
                        if item:
                            if current_section == "flags":
                                red_flags.append(item)
                            elif current_section == "actions":
                                actions.append(item)
                            elif current_section == "recs":
                                recommendations.append(item)

                col_left, col_right = st.columns(2)

                with col_left:
                    if red_flags:
                        st.markdown("### 🚩 Red Flags Detected")
                        for flag in red_flags:
                            st.error(f"⚠️ {flag}")

                    if actions:
                        st.markdown("### ✅ Actions Taken Automatically")
                        for action in actions:
                            st.success(f"✔️ {action}")

                with col_right:
                    if recommendations:
                        st.markdown("### 💡 Recommendations")
                        for rec in recommendations:
                            st.info(f"→ {rec}")

                st.markdown("---")
                with st.expander("📄 View Full Raw Summary"):
                    st.markdown(summary)

            else:
                st.error(f"API Error: {response.status_code} — {response.text}")

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out — agents are taking too long. Please try again!")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API server!")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#888; font-size:0.8rem'>"
    "Powered by Google ADK + Gemini 2.5 Flash | Multi-Agent System | Gen AI Academy APAC 2026"
    "</div>",
    unsafe_allow_html=True
)