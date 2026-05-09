import os
import secrets
import sys
import sqlite3
import csv
import io
import requests
import streamlit as st
from PIL import Image, ImageDraw


def _make_favicon():
    sz = 64
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(8, 6), (56, 6), (56, 34), (32, 58), (8, 34)]
    d.polygon(pts, fill=(59, 130, 246, 255))
    d.line([(32, 18), (32, 44)], fill=(255, 255, 255, 220), width=5)
    d.line([(20, 30), (44, 30)], fill=(255, 255, 255, 220), width=5)
    return img

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_setup import DB_PATH, get_connection, setup_database
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

BACKEND_URL = os.getenv("STRATIFY_BACKEND_URL", "http://127.0.0.1:8080").rstrip("/")
API_URL = f"{BACKEND_URL}/analyze"
DAILY_URL = f"{BACKEND_URL}/analyze-daily"
MCP_URL = f"{BACKEND_URL}/analyze-mcp"
API_KEY = os.getenv("STRATIFY_API_KEY", "")
UI_ACCESS_KEY = os.getenv("STRATIFY_UI_ACCESS_KEY") or API_KEY
DISABLE_UI_AUTH = os.getenv("STRATIFY_DISABLE_UI_AUTH", "false").lower() == "true"
DEFAULT_PROMPT = "A critical issue is open, delivery is at risk today, and we need an action plan."

setup_database()


def is_local_request() -> bool:
    try:
        host = st.context.headers.get("host", "")
    except Exception:
        return False

    host = host.split(":", 1)[0].lower()
    return host in {"localhost", "127.0.0.1", "::1"}


@st.cache_data(show_spinner=False, ttl=5)
def cached_agent_runs():
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute("""
            SELECT agent_name, stage, message, created_at
            FROM agent_runs
            ORDER BY id ASC
        """).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    except Exception:
        return []


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
    try:
        return cached_agent_runs()
    except sqlite3.OperationalError:
        return []
    except Exception:
        return []


def fallback_warning_text(payload: dict, default_message: str) -> str:
    return payload.get("fallback_message") or default_message


def parse_summary(summary: str):
    sections = {
        "status": "",
        "red_flags": [],
        "actions": [],
        "recommendations": [],
    }

    def clean(line: str) -> str:
        return line.strip().lstrip("#").strip().strip("*").strip(":").strip()

    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    current = None

    for line in lines:
        stripped = line.strip("*").strip("#").strip()

        if "Status:" in line:
            val = line.split("Status:", 1)[-1].strip().strip("*").strip()
            if val:
                sections["status"] = val
        elif any(stripped.startswith(h) for h in ("Red Flags", "Red flags")):
            current = "red_flags"
        elif any(stripped.startswith(h) for h in ("Actions Taken", "Actions taken")):
            current = "actions"
        elif stripped.startswith("Recommendations"):
            current = "recommendations"
        elif line.startswith(("-", "*", "•")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".):"):
            value = line.lstrip("-*•0123456789.)").strip().strip("*").strip()
            if current and value and not value.endswith(":"):
                sections[current].append(value)

    return sections


def get_api_headers():
    if is_local_request():
        return {}

    if not API_KEY:
        raise RuntimeError("STRATIFY_API_KEY is not configured for the frontend")

    return {"X-API-Key": API_KEY}


def mask_email(value: str) -> str:
    if not value or "@" not in value:
        return ""

    local_part, domain = value.split("@", 1)
    if not local_part:
        return f"***@{domain}"

    if len(local_part) == 1:
        masked_local = "*"
    elif len(local_part) == 2:
        masked_local = f"{local_part[0]}*"
    else:
        masked_local = f"{local_part[0]}{'*' * (len(local_part) - 2)}{local_part[-1]}"

    return f"{masked_local}@{domain}"


def require_ui_access():
    if DISABLE_UI_AUTH or is_local_request():
        st.session_state.ui_authenticated = True
        return

    if not UI_ACCESS_KEY:
        st.error("STRATIFY_UI_ACCESS_KEY or STRATIFY_API_KEY must be configured before the dashboard can be used.")
        st.stop()

    if st.session_state.get("ui_authenticated"):
        return

    st.title("Stratify Access")
    st.caption("Enter the dashboard access key to continue.")

    with st.form("ui_access_form"):
        provided_key = st.text_input("Access Key", type="password")
        submitted = st.form_submit_button("Unlock")

        if submitted:
            if secrets.compare_digest(provided_key, UI_ACCESS_KEY):
                st.session_state.ui_authenticated = True
                st.rerun()
            else:
                st.error("Invalid access key.")

    st.stop()


def navigate_to(page_name: str):
    st.query_params["page"] = page_name
    st.rerun()


def ui_icon(name: str) -> str:
    icons = {
        "shield": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3l7 3v6c0 4.8-2.9 7.9-7 9-4.1-1.1-7-4.2-7-9V6l7-3z"/>
                <path d="M12 8v8"/>
                <path d="M8.8 11.5H15.2"/>
            </svg>
        """,
        "tasks": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <rect x="5" y="4" width="14" height="16" rx="2"/>
                <path d="M9 2.8h6v3H9z"/>
                <path d="M8.5 10.5h7"/>
                <path d="M8.5 14.5h7"/>
            </svg>
        """,
        "list": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 6.5h10"/>
                <path d="M9 12h10"/>
                <path d="M9 17.5h10"/>
                <circle cx="5.5" cy="6.5" r="1"/>
                <circle cx="5.5" cy="12" r="1"/>
                <circle cx="5.5" cy="17.5" r="1"/>
            </svg>
        """,
        "alert": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 4.5l8 14H4l8-14z"/>
                <path d="M12 9v4.8"/>
                <path d="M12 17.2h.01"/>
            </svg>
        """,
        "team": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="9" cy="9" r="3.2"/>
                <circle cx="17" cy="10.5" r="2.4"/>
                <path d="M4.5 18.5c.7-2.8 2.9-4.5 6-4.5s5.3 1.7 6 4.5"/>
                <path d="M15.2 18.2c.4-1.8 1.7-3.1 3.8-3.6"/>
            </svg>
        """,
        "log": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <rect x="6" y="4" width="12" height="16" rx="2"/>
                <path d="M9 8.5h6"/>
                <path d="M9 12h6"/>
                <path d="M9 15.5h4.5"/>
            </svg>
        """,
        "agent": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <rect x="7" y="8" width="10" height="9" rx="2"/>
                <path d="M12 4v4"/>
                <path d="M9.5 17v2"/>
                <path d="M14.5 17v2"/>
                <circle cx="10" cy="12.5" r=".7" fill="currentColor" stroke="none"/>
                <circle cx="14" cy="12.5" r=".7" fill="currentColor" stroke="none"/>
                <path d="M10 15h4"/>
            </svg>
        """,
        "info": """
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"/>
                <path d="M12 10.5v5"/>
                <circle cx="12" cy="7.5" r=".7" fill="currentColor" stroke="none"/>
            </svg>
        """,
    }
    return icons[name]


def render_page_header(title: str, subtitle: str, icon_name: str):
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-inner">
                <div class="page-header-icon">{ui_icon(icon_name)}</div>
                <div>
                    <div class="page-header-title">{title}</div>
                    <div class="page-header-sub">{subtitle}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header():
    st.markdown(
        f"""
        <div class="app-header">
            <div class="brand-lockup">
                <div class="brand-icon">{ui_icon("shield")}</div>
                <div>
                    <div class="brand-title">Stratify</div>
                    <div class="brand-subtitle">
                        Multi-agent workspace for project monitoring, risk analysis, and operational response.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def records_to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_top_nav(current_page: str):
    nav_labels = ["Home", "Agents", "Tasks", "Team", "Action Log", "Manage Data", "About"]
    st.markdown('<div class="topbar-spacer"></div>', unsafe_allow_html=True)
    nav_columns = st.columns(len(nav_labels), gap="small")
    for column, label in zip(nav_columns, nav_labels):
        with column:
            button_type = "primary" if current_page == label else "secondary"
            if st.button(label, key=f"nav_{label}", type=button_type, use_container_width=True):
                if st.session_state.nav_page != label:
                    st.session_state.nav_page = label
                    st.query_params["page"] = label
                    st.rerun()
    st.markdown('<div class="topbar-spacer bottom"></div>', unsafe_allow_html=True)


def apply_theme(theme_name: str):
    if theme_name == "Dark":
        bg = "#050505"
        surface = "rgba(0,0,0,0.40)"
        card = "rgba(0,0,0,0.60)"
        text = "#FAFAFA"
        subtext = "#A1A1AA"
        border = "rgba(255,255,255,0.10)"
        accent = "#FAFAFA"
        muted = "#71717A"
        input_bg = "rgba(0,0,0,0.60)"
    else:
        bg = "#F9FAFB"
        surface = "#FFFFFF"
        card = "#F3F4F6"
        text = "#111827"
        subtext = "#6B7280"
        border = "#E5E7EB"
        accent = "#6366F1"
        muted = "#9CA3AF"
        input_bg = "#FFFFFF"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        #MainMenu {{visibility:hidden;}}
        footer {{visibility:hidden;}}
        header {{visibility:hidden;}}

        .stApp {{
            background:
                radial-gradient(circle at 18% -8%, rgba(37,99,235,0.08), transparent 26rem),
                linear-gradient(135deg, #050505 0%, #080808 50%, #0a0a0a 100%);
            color: {text};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem;
            max-width: 1600px;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}

        h1, h2, h3, h4, h5, h6, p, div, span, label, li {{ color: {text}; }}

        .main .block-container {{
            animation: pageFadeIn 0.18s ease-out;
        }}
        @keyframes pageFadeIn {{
            from {{ opacity: 0.82; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* HEADER */
        .app-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .brand-lockup {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .brand-icon {{
            width: 48px;
            height: 48px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.20);
            background: rgba(255,255,255,0.10);
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }}
        .brand-icon svg {{ width: 28px; height: 28px; }}
        .brand-title {{
            font-size: 40px;
            line-height: 1.1;
            font-weight: 800;
            letter-spacing: 0;
            color: #fff;
        }}
        .brand-title span {{ color: #F97316; }}
.brand-subtitle {{
            margin-top: 5px;
            font-size: 16px;
            line-height: 1.6;
            color: #9CA3AF;
        }}

        /* TOP NAV */
        .topbar-spacer {{
            height: 8px;
            border-top: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px 12px 0 0;
            background: rgba(0,0,0,0.20);
            margin-top: 8px;
        }}
        .topbar-spacer.bottom {{
            height: 16px;
            border-top: none;
            border-bottom: 1px solid rgba(255,255,255,0.10);
            border-radius: 0 0 12px 12px;
            margin-top: -2px;
            margin-bottom: 24px;
        }}
        .topbar-shell {{
            background: rgba(0,0,0,0.20);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 8px;
            margin: 8px 0 24px;
            backdrop-filter: blur(10px);
            box-shadow: none;
        }}
        .topbar-nav {{
            flex: 1 1 auto;
            min-width: 0;
        }}
        .topbar-links {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: nowrap;
            overflow-x: auto;
            padding-bottom: 2px;
        }}
        .topbar-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            min-height: 42px;
            padding: 0 16px;
            border-radius: 8px;
            border: 1px solid transparent;
            background: transparent;
            color: #9CA3AF;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            white-space: nowrap;
            transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, color 0.18s ease;
        }}
        .topbar-link:hover {{
            background: rgba(255,255,255,0.05);
            color: #fff;
            box-shadow: none;
        }}
        .topbar-link.active {{
            background: rgba(0,0,0,0.60);
            border-color: rgba(255,255,255,0.10);
            color: #fff;
            box-shadow: inset 0 -2px 0 rgba(255,255,255,0.86), 0 10px 24px rgba(255,255,255,0.08);
        }}
        .topbar-link-icon {{
            width: 16px;
            height: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        .topbar-link-icon svg {{
            width: 16px;
            height: 16px;
        }}
        /* PAGE HEADER */
        .page-header {{
            padding: 2px 0 24px; border-bottom: 1px solid {border}; margin-bottom: 28px;
        }}
        .page-header-inner {{ display: flex; align-items: flex-start; gap: 14px; }}
        .page-header-icon {{
            width: 44px; height: 44px; border: 1px solid {border}; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            color: {subtext}; background: {surface};
        }}
        .page-header-title {{ font-size: 34px; font-weight: 800; color: {text}; line-height: 1.08; }}
        .page-header-sub {{ font-size: 15px; color: {subtext}; margin-top: 6px; line-height: 1.7; max-width: 820px; }}

        /* HERO SECTION (flat, not a card) */
        .hero-section, .dashboard-panel {{
            background: rgba(0,0,0,0.40);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
            box-shadow: 0 18px 40px rgba(0,0,0,0.18);
        }}
        .hero-section {{ padding: 24px; }}
        .hero-title {{
            font-size: 20px; font-weight: 700; color: {text};
            margin-bottom: 10px; line-height: 1.25;
        }}
        .hero-copy, .subtle-copy {{
            font-size: 16px; color: {subtext}; line-height: 1.75;
        }}

        /* METRIC CARDS (only prominent ones) */
        .metric-card {{
            background: rgba(0,0,0,0.40); border: 1px solid rgba(255,255,255,0.10); border-radius: 12px;
            padding: 16px; min-height: 128px; height: 100%;
            display: flex; flex-direction: column; justify-content: space-between;
            box-shadow: 0 18px 40px rgba(0,0,0,0.18);
            backdrop-filter: blur(10px);
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }}
        .metric-card:hover {{ box-shadow: 0 6px 18px rgba(0,0,0,0.12); border-color: rgba(255,255,255,0.14); }}
        .metric-top {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; min-height: 44px; }}
        .metric-icon {{
            width: 40px; height: 40px; border-radius: 999px;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px;
            background: color-mix(in srgb, currentColor 22%, transparent);
            border: 2px solid color-mix(in srgb, currentColor 58%, transparent);
            box-shadow: 0 0 0 1px color-mix(in srgb, currentColor 18%, transparent), 0 12px 26px color-mix(in srgb, currentColor 18%, transparent);
        }}
        .metric-label {{
            margin: 0; font-size: 11px; letter-spacing: 0.06em;
            text-transform: uppercase; color: {muted}; white-space: nowrap;
        }}
        .metric-value {{ margin: 0; font-size: 30px; font-weight: 800; color: {text}; line-height: 1.1; }}
        .metric-sub {{ color: {subtext}; font-size: 14px; line-height: 1.5; min-height: 34px; }}

        /* CONTENT SECTIONS (flat) */
        .section-title {{ font-size: 15px; font-weight: 700; color: {text}; margin-bottom: 4px; }}
        .section-sub {{ font-size: 15px; color: {subtext}; line-height: 1.7; margin-bottom: 14px; }}
        .mini-title {{ font-size: 14px; font-weight: 700; color: {text}; margin-bottom: 8px; }}

        /* SIDEBAR (flat, not floating) */
        .sidebar-block {{ padding: 18px 0; border-bottom: 1px solid {border}; }}
        .sidebar-block:last-child {{ border-bottom: none; }}
        .sidebar-label {{
            font-size: 11px; font-weight: 700; letter-spacing: 0.07em;
            text-transform: uppercase; color: {muted}; margin-bottom: 8px;
        }}
        .sidebar-body {{ font-size: 15px; color: {subtext}; line-height: 1.75; }}
        .sidebar-stat {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 6px 0; border-bottom: 1px solid {border}; font-size: 13px;
        }}
        .sidebar-stat:last-child {{ border-bottom: none; }}
        .sidebar-stat-label {{ color: {subtext}; }}
        .sidebar-stat-value {{ font-weight: 700; color: {text}; }}

        /* BADGE PILLS */
        .badge-pill {{
            display: inline-block; background: rgba(37,99,235,0.10); color: #93C5FD;
            border: 1px solid rgba(37,99,235,0.20); border-radius: 999px;
            padding: 5px 14px; font-size: 14px;
            margin-right: 6px; margin-bottom: 6px;
        }}
        .badge-pill.green {{ background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.20); color: #86EFAC; }}
        .badge-pill.purple {{ background: rgba(168,85,247,0.10); border-color: rgba(168,85,247,0.20); color: #D8B4FE; }}
        .badge-pill.orange {{ background: rgba(249,115,22,0.10); border-color: rgba(249,115,22,0.20); color: #FDBA74; }}

        .insight-card {{
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(0,0,0,0.40);
            margin-bottom: 16px;
            backdrop-filter: blur(10px);
            box-shadow: none;
        }}
        .insight-card.yellow {{ background: rgba(234,179,8,0.05); border-color: rgba(234,179,8,0.20); }}
        .insight-card.mixed {{ background: linear-gradient(135deg, rgba(239,68,68,0.05), rgba(37,99,235,0.05)); border-color: rgba(255,255,255,0.20); }}
        .insight-card.green {{ background: rgba(34,197,94,0.05); border-color: rgba(34,197,94,0.20); }}
        .insight-title {{ font-size: 14px; font-weight: 700; margin-bottom: 8px; }}
        .insight-copy {{ font-size: 15px; line-height: 1.75; color: #D1D5DB; }}

        .feature-card {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 20px;
            height: 100%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .feature-head {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .feature-icon {{
            width: 40px;
            height: 40px;
            border-radius: 12px;
            border: 1px solid {border};
            background: {bg};
            display: flex;
            align-items: center;
            justify-content: center;
            color: {text};
        }}
        .feature-title {{
            font-size: 16px;
            font-weight: 700;
            color: {text};
        }}
        .feature-copy {{
            font-size: 14px;
            line-height: 1.8;
            color: {subtext};
        }}
        .feature-list {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .feature-list li {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 14px;
            color: {subtext};
            line-height: 1.7;
        }}
        .feature-list li::before {{
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 999px;
            margin-top: 8px;
            flex: 0 0 8px;
            background: {accent};
        }}

        /* CONVERSATION */
        .conversation-shell {{
            margin-top: 0;
            background: rgba(0,0,0,0.40);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 24px;
            backdrop-filter: blur(10px);
            box-shadow: none;
        }}
        .conversation-item {{
            display: flex; gap: 10px; align-items: flex-start;
            padding: 10px 12px; border-radius: 10px;
            background: rgba(37,99,235,0.10); border: 1px solid rgba(37,99,235,0.20);
            margin-bottom: 8px; font-size: 15px;
        }}
        .conversation-icon {{
            width: 28px; height: 28px; border-radius: 8px;
            background: rgba(0,0,0,0.60); border: 1px solid rgba(255,255,255,0.10);
            color: #fff;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; flex: 0 0 28px;
        }}
        .conversation-empty {{ color: {muted}; font-size: 15px; padding: 12px 0; }}

        /* RESULT / SUMMARY (flat, no card) */
        .result-card, .summary-shell, .timeline-shell {{
            background: rgba(0,0,0,0.40);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 24px;
            box-shadow: none;
            backdrop-filter: blur(10px);
        }}
        .summary-shell {{ margin-top: 16px; }}
        .timeline-shell {{ margin-top: 16px; }}
        .summary-title, .timeline-title {{
            font-size: 14px; font-weight: 700; margin-bottom: 12px; color: {text};
        }}
        .summary-grid {{ display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 24px; }}
        .summary-status {{ font-size: 14px; margin-bottom: 10px; }}
        .summary-status strong {{ color: #FFC72C; }}
        .summary-col-title {{ font-weight: 700; margin-bottom: 8px; }}
        .summary-red {{ color: #FF6A63; }}
        .summary-green {{ color: #47D46B; }}
        .summary-blue {{ color: #5A93FF; }}
        .timeline-empty {{ text-align: center; color: {subtext}; padding: 20px 0; line-height: 1.7; }}

        /* TRI GRID */
        .tri-grid {{ display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 16px; margin-top: 8px; }}
        .tri-card {{ border: 1px solid rgba(255,255,255,0.10); border-radius: 10px; background: rgba(0,0,0,0.40); padding: 14px; }}
        .tri-title {{ font-size: 14px; font-weight: 700; margin-bottom: 10px; }}
        .home-shortcut {{
            min-height: 190px;
            padding: 22px;
            border-radius: 14px;
            background:
                linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.015)),
                rgba(0,0,0,0.40);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 18px 40px rgba(0,0,0,0.18);
        }}
        .shortcut-symbol {{
            width: 56px;
            height: 56px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 18px;
            border: 1px solid currentColor;
            background: color-mix(in srgb, currentColor 14%, transparent);
            box-shadow: 0 12px 28px color-mix(in srgb, currentColor 15%, transparent);
        }}
        .shortcut-symbol svg {{
            width: 28px;
            height: 28px;
        }}
        .signal-list {{ display: flex; flex-direction: column; gap: 6px; }}
        .signal-item {{
            border: 1px solid rgba(255,255,255,0.10); border-radius: 8px;
            padding: 10px 12px; background: rgba(0,0,0,0.60); font-size: 15px; line-height: 1.5;
        }}

        /* CAP GRID */
        .cap-grid {{ display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 10px; margin: 12px 0; }}
        .cap-card {{ border: 1px solid rgba(255,255,255,0.10); border-radius: 8px; padding: 10px 14px; background: rgba(255,255,255,0.05); font-size: 14px; font-weight: 600; color:#9CA3AF; }}

        /* MODE PILLS */
        .mode-pill {{
            display: inline-block; border-radius: 999px;
            padding: 4px 10px; font-size: 11px; font-weight: 700;
            margin-bottom: 12px; border: 1px solid {border};
        }}
        .mode-interactive {{ background: rgba(249,115,22,0.1); color: #F97316; }}
        .mode-auto {{ background: rgba(16,185,129,0.1); color: #10B981; }}
        .mode-mcp {{ background: rgba(99,102,241,0.1); color: #6366F1; }}

        /* STATUS BANNER */
        .status-banner {{
            border-radius: 8px; border: 1px solid #1D4F2B;
            background: rgba(11,55,25,0.9); color: #E8FFF0;
            padding: 10px 14px; font-size: 14px; margin-top: 10px;
        }}

        /* FOOTER */
        .footer-note {{ text-align: center; color: {muted}; font-size: 12px; padding-top: 12px; }}

        /* BUTTONS */
        .stButton > button {{
            border-radius: 8px !important; font-weight: 600 !important;
            height: 42px !important; border: 1px solid rgba(255,255,255,0.10) !important;
            background: rgba(255,255,255,0.05) !important; color: {text} !important;
            box-shadow: none !important;
            transition: background 0.15s ease, border-color 0.15s ease !important;
            padding: 0 16px !important;
        }}
        div[data-testid="stButton"] {{ width: 100%; }}
        .stButton > button:hover {{
            border-color: rgba(255,255,255,0.16) !important; background: rgba(255,255,255,0.10) !important;
            color: #fff !important; box-shadow: none !important;
        }}
        .stButton > button:active, .stButton > button:focus, .stButton > button:focus-visible {{
            border-color: rgba(255,255,255,0.22) !important;
            background: rgba(0,0,0,0.72) !important;
            color: #fff !important;
            box-shadow: none !important;
        }}
        .stButton > button[kind="primary"] {{
            border-color: rgba(255,255,255,0.22) !important;
            background: rgba(0,0,0,0.72) !important;
            color: #fff !important;
            box-shadow: none !important;
        }}
        button[data-testid="stBaseButton-primary"],
        div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {{
            border-color: rgba(255,255,255,0.22) !important;
            background: rgba(0,0,0,0.72) !important;
            color: #fff !important;
            box-shadow: none !important;
        }}

        /* INPUTS */
        .stTextInput input {{
            background: {input_bg} !important; color: {text} !important;
            border: 1px solid rgba(255,255,255,0.20) !important; border-radius: 8px !important;
            min-height: 40px !important; height: 40px !important;
        }}
        .stTextArea textarea {{
            background: {input_bg} !important; color: {text} !important;
            border: 1px solid rgba(255,255,255,0.20) !important; border-radius: 8px !important;
            min-height: 100px !important; line-height: 1.5 !important;
        }}
        .stTextArea textarea:focus, .stTextInput input:focus {{
            border-color: {accent} !important;
            box-shadow: 0 0 0 3px rgba(124,141,255,0.15) !important;
        }}
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {{
            background: {input_bg} !important; color: {text} !important;
            border: 1px solid {border} !important; border-radius: 8px !important;
            min-height: 40px !important;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            display: flex; flex-direction: column;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid {border}; border-radius: 10px; overflow: hidden;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {surface}; border-radius: 14px;
            border: 1px solid {border}; box-shadow: 0 1px 3px rgba(0,0,0,0.08); padding: 4px;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )



def metric_card(label, value, border_color, icon_html, subtitle):
    return f"""
    <div class="metric-card">
        <div class="metric-top">
            <div class="metric-icon" style="color:{border_color};">{icon_html}</div>
            <div>
                <p class="metric-label">{label}</p>
                <p class="metric-value">{value}</p>
            </div>
        </div>
        <div class="metric-sub">{subtitle}</div>
    </div>
    """


def render_metrics_row(task_count, open_count, critical_count, available_count, action_count):
    m1, m2, m3, m4, m5 = st.columns(5, gap="small")
    with m1:
        st.markdown(metric_card("Total Tasks", task_count, "#7DD3FC", ui_icon("tasks"), "All tasks in system"), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card("Open Tasks", open_count, "#F97316", ui_icon("list"), "Awaiting action"), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card("Critical Open", critical_count, "#FF4D4D", ui_icon("alert"), "Requires immediate attention"), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card("Available Team", available_count, "#10B981", ui_icon("team"), "Ready to contribute"), unsafe_allow_html=True)
    with m5:
        st.markdown(metric_card("Logged Actions", action_count, "#A855F7", ui_icon("log"), "Total actions recorded"), unsafe_allow_html=True)
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)


def capability_badges(mode_label):
    last_label = "MCP" if mode_label == "MCP" else "Autonomous" if mode_label == "AUTONOMOUS" else "Interactive"
    last_class = "" if mode_label != "INTERACTIVE" else " alt"
    st.markdown(
        f"""
        <div class="cap-grid">
            <div class="cap-card">Multi-Agent</div>
            <div class="cap-card">SQLite</div>
            <div class="cap-card">Real Calendar</div>
            <div class="cap-card{last_class}">{last_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    def render_signal_card(title: str, items: list[str], title_class: str):
        safe_items = items or ["No items listed."]
        body = "".join(f'<div class="signal-item">{item}</div>' for item in safe_items)
        return f"""
        <div class="tri-card">
            <div class="tri-title {title_class}">{title}</div>
            <div class="signal-list">{body}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="tri-grid">
            {render_signal_card('Red Flags', parsed['red_flags'], 'summary-red')}
            {render_signal_card('Actions Taken', parsed['actions'], 'summary-green')}
            {render_signal_card('Recommendations', parsed['recommendations'], 'summary-blue')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="summary-shell"><div class="summary-title">Executive Summary</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(summary, unsafe_allow_html=False)

    agent_runs = fetch_agent_runs()
    if agent_runs:
        timeline_body = "".join(
            f'<div class="signal-item"><strong>{row["agent_name"]}</strong> | {row["stage"]} | {row["message"]}</div>'
            for row in agent_runs
        )
    else:
        timeline_body = '<div class="timeline-empty">No agent activity recorded yet.<br/>Agent actions and events will appear here.</div>'

    st.markdown(
        f"""
        <div class="timeline-shell">
            <div class="timeline-title">Agent Activity Timeline</div>
            {timeline_body}
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Stratify", page_icon=_make_favicon(), layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "draft_prompt" not in st.session_state:
    st.session_state.draft_prompt = ""

if st.session_state.draft_prompt == DEFAULT_PROMPT:
    st.session_state.draft_prompt = ""

if st.session_state.get("home_prompt") == DEFAULT_PROMPT:
    st.session_state.home_prompt = ""

if "session_token" not in st.session_state:
    st.session_state.session_token = secrets.token_urlsafe(16)

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

require_ui_access()

requested_page = st.query_params.get("page")
allowed_pages = ["Home", "Agents", "Tasks", "Team", "Action Log", "Manage Data", "About"]
if requested_page in allowed_pages:
    st.session_state.nav_page = requested_page

apply_theme(st.session_state.theme)

task_count, open_count, critical_count, available_count, action_count = cached_metrics()

# top navigation
page = st.session_state.nav_page
render_top_nav(page)
render_app_header()
render_metrics_row(task_count, open_count, critical_count, available_count, action_count)
if False:
    with st.popover("⋯", use_container_width=True):
        st.markdown("**Display**")
        if st.button("Toggle Theme", use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
            st.rerun()
        if st.button("Refresh Page", use_container_width=True, key="refresh_btn"):
            st.rerun()


if page == "Home":
    st.markdown(
        """
        <div class="hero-section" style="padding:34px 32px;">
            <div class="hero-title" style="font-size:28px;">Welcome to Stratify</div>
            <div class="hero-copy" style="max-width:900px;">
                Built for project leads who need clarity without digging through scattered
                updates. Stratify brings tasks, team capacity, and recent actions into
                one focused workspace, so you can understand what is moving, what is blocked,
                and where your attention is needed next.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:26px"></div>', unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown(
            f"""
            <div class="tri-card home-shortcut">
                <div class="shortcut-symbol" style="color:#5A93FF;">{ui_icon("tasks")}</div>
                <div class="tri-title summary-blue">Tasks</div>
                <div class="hero-copy">Review active work, priorities, owners, and deadlines.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Tasks", type="primary", use_container_width=True, key="home_go_tasks"):
            navigate_to("Tasks")
    with h2:
        st.markdown(
            f"""
            <div class="tri-card home-shortcut">
                <div class="shortcut-symbol" style="color:#47D46B;">{ui_icon("team")}</div>
                <div class="tri-title summary-green">Team</div>
                <div class="hero-copy">Check roles, skills, and who is currently available.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Team", use_container_width=True, key="home_go_team"):
            navigate_to("Team")
    with h3:
        st.markdown(
            f"""
            <div class="tri-card home-shortcut">
                <div class="shortcut-symbol" style="color:#FF6A63;">{ui_icon("log")}</div>
                <div class="tri-title summary-red">Action Log</div>
                <div class="hero-copy">Audit recent operations and recorded system actions.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Action Log", use_container_width=True, key="home_go_actions"):
            navigate_to("Action Log")
elif page == "Agents":
    render_page_header(
        "Agents",
        "Run interactive project analysis, autonomous checks, and MCP operations from one workspace.",
        "agent",
    )
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown(
            """
            <div class="hero-section">
                <div class="hero-title">Agent Workspace</div>
                <div class="hero-copy">
                    Describe a real project issue, delivery risk, blocked task, or team problem.
                    The system analyzes it using your live project context and suggests next actions.
                </div>
                <div style="margin-top:12px;">
                    <span class="badge-pill">Real user input</span>
                    <span class="badge-pill">Multi-agent orchestration</span>
                    <span class="badge-pill">Real calendar action</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        quick1, quick2, quick3 = st.columns(3)
        with quick1:
            if st.button("Critical Bug", use_container_width=True):
                st.session_state.draft_prompt = "A critical issue is open, delivery is at risk today, and we need an action plan. Create a Google Calendar emergency huddle for immediate coordination."
        with quick2:
            if st.button("Production Issue", use_container_width=True):
                st.session_state.draft_prompt = "Production is unstable, users are impacted, and immediate coordination is required."
        with quick3:
            if st.button("Sprint Delay", use_container_width=True):
                st.session_state.draft_prompt = "Sprint delivery is at risk because some tasks are blocked and deadlines are close."

        st.markdown('<div class="prompt-input-shell">', unsafe_allow_html=True)
        user_prompt = st.text_area(
            "Your Message",
            value=st.session_state.draft_prompt,
            height=100,
            placeholder="Example: We have 2 blocked tasks, one critical issue, and one unavailable team member. What should we do today?"
        )
        st.markdown('</div>', unsafe_allow_html=True)

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
            st.session_state.session_token = secrets.token_urlsafe(16)
            st.cache_data.clear()
            st.rerun()

        st.markdown('<div class="conversation-shell"><div class="section-title">Conversation</div>', unsafe_allow_html=True)
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history[-6:]:
                icon = "💬" if msg["role"] == "user" else "✓"
                st.markdown(
                    f"""
                    <div class="conversation-item">
                        <div class="conversation-icon">{icon}</div>
                        <div>{msg["content"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="conversation-empty">No conversation yet. Type your own project situation and click Analyze Situation.</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown(
            f"""
            <div class="sidebar-block">
                <div class="sidebar-label">Prompt tips</div>
                <div class="sidebar-body">
                    Mention the issue, who is affected, the deadline, and any blocking problem.
                    Be specific — the agents use your live data.
                </div>
            </div>
            <div class="sidebar-block">
                <div class="sidebar-label">Current snapshot</div>
                <div class="sidebar-stat"><span class="sidebar-stat-label">Critical open</span><span class="sidebar-stat-value">{critical_count}</span></div>
                <div class="sidebar-stat"><span class="sidebar-stat-label">Open tasks</span><span class="sidebar-stat-value">{open_count}</span></div>
                <div class="sidebar-stat"><span class="sidebar-stat-label">Available team</span><span class="sidebar-stat-value">{available_count}</span></div>
            </div>
            <div class="sidebar-block">
                <div class="sidebar-label">Capabilities</div>
                <div class="sidebar-body">
                    Live task context · Multi-agent orchestration · MCP operations · Action logging · Calendar coordination
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
                            "session_id": st.session_state.session_token,
                        },
                        headers=get_api_headers(),
                        timeout=45,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        summary = data["summary"]
                        st.session_state.session_token = data.get("session_id", st.session_state.session_token)
                        st.session_state.chat_history.append({"role": "assistant", "content": summary})

                        if data["status"] == "fallback":
                            st.warning(
                                fallback_warning_text(
                                    data,
                                    "Live model execution is unavailable, so a local fallback response was returned.",
                                )
                            )
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
                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

    if run_daily:
        with st.spinner("Running autonomous daily check..."):
            try:
                response = requests.post(DAILY_URL, headers=get_api_headers(), timeout=45)

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]

                    if data["status"] == "fallback":
                        st.warning(
                            fallback_warning_text(
                                data,
                                "Live model execution is unavailable, so a local fallback response was returned.",
                            )
                        )
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
            except RuntimeError as exc:
                st.error(str(exc))
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
                        "session_id": st.session_state.session_token,
                    },
                    headers=get_api_headers(),
                    timeout=45,
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["summary"]
                    st.session_state.session_token = data.get("session_id", st.session_state.session_token)
                    st.session_state.chat_history.append({"role": "assistant", "content": summary})

                    if data["status"] == "fallback":
                        st.warning(
                            fallback_warning_text(
                                data,
                                "Live model execution is unavailable, so a local fallback response was returned.",
                            )
                        )
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
            except RuntimeError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

elif page == "Tasks":
    render_page_header(
        "Current Tasks",
        "Track and review active work across the project using your live task data.",
        "tasks",
    )
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
    t1, t2, t3 = st.columns([2, 1, 1])
    with t1:
        task_search = st.text_input("Search tasks", placeholder="Search by title, assignee, or status", key="tasks_search")
    with t2:
        task_status = st.selectbox("Status", ["All"] + sorted({t["status"] for t in tasks if t["status"]}), key="tasks_status")
    with t3:
        task_priority = st.selectbox("Priority", ["All"] + sorted({t["priority"] for t in tasks if t["priority"]}), key="tasks_priority")
    filtered_tasks = [
        task for task in tasks
        if (not task_search or task_search.lower() in " ".join(str(v).lower() for v in task.values()))
        and (task_status == "All" or task["status"] == task_status)
        and (task_priority == "All" or task["priority"] == task_priority)
    ]
    with st.container(border=True):
        if filtered_tasks:
            st.download_button(
                "Export Tasks CSV",
                data=records_to_csv(filtered_tasks),
                file_name="project_tasks.csv",
                mime="text/csv",
                key="tasks_export_csv",
            )
            st.dataframe(filtered_tasks, use_container_width=True)
        else:
            st.info("No tasks found.")

elif page == "Team":
    render_page_header(
        "Team Status",
        "Overview of team members, roles, skills, and current availability.",
        "team",
    )
    raw_team = cached_team_members()
    team = [
        {
            "id": member.get("id", ""),
            "name": member.get("name", ""),
            "role": member.get("role", ""),
            "email": mask_email(member.get("email", "")),
            "skills": member.get("skills", ""),
            "availability": "Available" if member.get("available") in [True, 1, "Available"] else "Unavailable",
        }
        for member in raw_team
    ]
    t1, t2 = st.columns([2, 1])
    with t1:
        team_search = st.text_input("Search team", placeholder="Search by name, role, email, or skills", key="team_search")
    with t2:
        team_availability = st.selectbox("Availability", ["All", "Available", "Unavailable"], key="team_availability_filter")
    filtered_team = [
        member for member in team
        if (not team_search or team_search.lower() in " ".join(str(v).lower() for v in member.values()))
        and (team_availability == "All" or member["availability"] == team_availability)
    ]
    with st.container(border=True):
        if filtered_team:
            st.dataframe(filtered_team, use_container_width=True)
        else:
            st.info("No team members found.")

elif page == "Action Log":
    render_page_header(
        "Recent Action Log",
        "Review logged operations, tool activity, and external actions captured by the system.",
        "log",
    )
    actions = cached_action_logs(20)
    log_search = st.text_input("Search action log", placeholder="Search tool, action, details, or timestamp", key="action_log_search")
    filtered_actions = [
        row for row in actions
        if not log_search or log_search.lower() in " ".join(str(v).lower() for v in row.values())
    ]
    with st.container(border=True):
        if filtered_actions:
            st.dataframe(filtered_actions, use_container_width=True)
            st.markdown("### Real External Actions")
            calendar_rows = [
                row for row in cached_action_logs(50)
                if row.get("tool") == "GoogleCalendar"
            ][:10]
            if calendar_rows:
                for row in calendar_rows:
                    details = row["details"]
                    safe_details = details.split("| event_link=")[0].strip()
                    st.info(safe_details)
            else:
                st.info("No real external action links found yet.")
        else:
            st.info("No actions logged yet.")

elif page == "Manage Data":
    render_page_header(
        "Manage Project Data",
        "Add, update, and remove tasks and team information carefully using the live project database.",
        "list",
    )

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
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

        with st.container(border=True):
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

        with st.container(border=True):
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

    with right:
        with st.container(border=True):
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

        with st.container(border=True):
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

        with st.container(border=True):
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

    st.markdown(
        """
        <div class="panel-card">
            <div class="subtle-copy">
                All changes are applied immediately. Deleted items cannot be recovered, so please review carefully before confirming.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif page == "About":
    render_page_header(
        "About",
        "Understand what the system does today, how it works, and where the product can grow next.",
        "info",
    )

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-head">
                    <div class="feature-icon">{ui_icon("tasks")}</div>
                    <div class="feature-title">What You Can Do</div>
                </div>
                <div class="feature-copy">
                    Analyze delivery risks, review blocked work, monitor team availability,
                    run operational checks, and coordinate urgent responses from a single dashboard.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-head">
                    <div class="feature-icon">{ui_icon("agent")}</div>
                    <div class="feature-title">How It Works</div>
                </div>
                <div class="feature-copy">
                    The Commander Agent coordinates Data Miner, Context Agent, and Tool Operator
                    to analyze project state and produce structured operational guidance.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a3:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-head">
                    <div class="feature-icon">{ui_icon("team")}</div>
                    <div class="feature-title">Best For</div>
                </div>
                <div class="feature-copy">
                    Project leads, engineering managers, startup teams, and operations teams
                    that need an AI-powered project operations workflow.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="navbar-divider" style="margin:24px 0 20px">', unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-head">
                    <div class="feature-icon">{ui_icon("shield")}</div>
                    <div class="feature-title">Current Implementation</div>
                </div>
                <ul class="feature-list">
                    <li>SQLite-backed project data</li>
                    <li>FastAPI and Streamlit workflow</li>
                    <li>ADK-based multi-agent orchestration</li>
                    <li>Google Calendar coordination action</li>
                    <li>MCP-based operations mode</li>
                    <li>Action logging and agent activity tracking</li>
                    <li>Interactive and autonomous analysis modes</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b2:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-head">
                    <div class="feature-icon">{ui_icon("info")}</div>
                    <div class="feature-title">Future Scope</div>
                </div>
                <ul class="feature-list">
                    <li>Slack integration</li>
                    <li>Jira integration</li>
                    <li>Vector-based context retrieval</li>
                    <li>Multi-project workspaces</li>
                    <li>Authentication and access control</li>
                    <li>Cloud-native production hardening</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    '<div class="footer-note">Built with ADK · FastAPI · Streamlit · SQLite · Google ADK · MCP</div>',
    unsafe_allow_html=True
)
