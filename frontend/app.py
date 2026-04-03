import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Agentic Project War-Room",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Agentic Project War-Room")
st.subheader("Multi-Agent Productivity Assistant — Gen AI Academy APAC 2026")

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active Agents", "4")
with col2:
    st.metric("Commander", "✅ Online")
with col3:
    st.metric("Sub-Agents", "3 Ready")
with col4:
    st.metric("API Status", "🟢 Live")

st.markdown("---")

st.subheader("🎯 Enter Crisis Scenario")

goal = st.text_area(
    "Describe the situation:",
    value="It is Monday morning. Our lead developer is out sick. Critical bug #42 is still open with EOD deadline. Analyse the situation and take all necessary actions.",
    height=120
)

if st.button("🚀 Activate War-Room", type="primary"):
    if goal.strip():
        with st.spinner("⚙️ Commander Agent activating sub-agents..."):

            log_placeholder = st.empty()
            log_placeholder.info("🔄 Commander → Calling Data Miner...")

            try:
                response = requests.post(
                    "http://localhost:8080/analyze",
                    json={"goal": goal},
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]

                    log_placeholder.empty()

                    st.success("✅ All agents completed successfully!")

                    st.markdown("---")
                    st.subheader("📊 Executive Summary")

                    if "Status: RED" in summary:
                        st.error("🔴 Project Status: RED — Immediate action required!")
                    elif "Status: YELLOW" in summary:
                        st.warning("🟡 Project Status: YELLOW — Attention needed")
                    else:
                        st.success("🟢 Project Status: GREEN — All good")

                    st.markdown(summary)

                    st.markdown("---")
                    st.subheader("🤖 Agent Activity Log")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.success("✅ Commander Agent")
                    with col2:
                        st.success("✅ Data Miner")
                    with col3:
                        st.success("✅ Context Agent")
                    with col4:
                        st.success("✅ Tool Operator")

                else:
                    st.error(f"API Error: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure FastAPI server is running: python main.py")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a goal first!")

st.markdown("---")
st.markdown("*Architecture:* Commander Agent (ADK + Gemini 2.5 Flash) → Data Miner | Context Agent | Tool Operator")