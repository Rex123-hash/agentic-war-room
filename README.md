<div align="center">

# 🛡️ Stratify

**AI-powered project operations — describe the situation, the agents handle the rest.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Frontend-blue?style=for-the-badge&logo=react)](https://stratify-frontend-868361801548.us-central1.run.app)
[![API Backend](https://img.shields.io/badge/API-Backend-green?style=for-the-badge&logo=fastapi)](https://stratify-api-868361801548.us-central1.run.app)
[![Built with Google ADK](https://img.shields.io/badge/Google%20ADK-Multi--Agent-orange?style=for-the-badge&logo=google-cloud)](https://cloud.google.com/vertex-ai)
[![Gemini 2.5 Flash](https://img.shields.io/badge/Model-Gemini%202.5%20Flash-purple?style=for-the-badge&logo=google)](https://deepmind.google/technologies/gemini/)

</div>

---

## 📋 Table of Contents

- [What is Stratify?](#what-is-stratify)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Cloud Deployment](#cloud-deployment)
- [API Reference](#api-reference)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Team](#team)
- [License](#license)

---

## What is Stratify?

Stratify is a **cloud-native multi-agent operations dashboard** that transforms how teams handle project emergencies. Instead of filling out forms or navigating complex UIs, you simply **describe what's happening in plain English** — and a team of AI agents gets to work.

### Example Use Cases:
- 📌 **Blocked Task**: "Senior dev is sick, we're 3 days from launch, task X is blocked" → agents reassign work, create a huddle, post action items
- 🚨 **Production Incident**: "Payment processing down, affecting 10% of orders" → agents pull live metrics, suggest rollback, log decisions
- 📅 **Capacity Crisis**: "We're short staffed for the Q2 push" → agents analyze availability, recommend team rebalancing

**Zero friction. Real actions. Structured briefing.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent Analysis** | Commander routes analysis across specialized agents (Data Miner, Context, Tool Operator) |
| 📊 **Executive Dashboard** | Dark-themed, real-time metrics: tasks, team capacity, health status, action log |
| 📅 **Auto Calendar Huddles** | Instantly creates Google Calendar emergency meetings on critical project risk |
| 🗂️ **Task & Team Ops** | Full lifecycle: add, update, filter, reassign, export tasks and team members |
| 🔄 **Autonomous Health Checks** | Daily proactive scans for project risks without human intervention |
| 🔌 **MCP Operations Mode** | Protocol-oriented infrastructure checks via Model Context Protocol |
| 📋 **Complete Audit Trail** | Immutable action log of every agent decision, with timestamps and reasoning |
| 🔐 **Optional Auth** | Access key protection for dashboard (configurable per deployment) |
| 🌐 **Live API** | RESTful backend for programmatic access to all operations |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- GCP project with Vertex AI enabled
- Google Cloud credentials

### Installation (5 minutes)

```bash
# Clone the repository
git clone https://github.com/amaank2405/agentic-war-room.git
cd agentic-war-room

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy template from .env)
cp .env .env.local
# Edit .env.local with your GCP credentials and project details
```

### Run Locally

**Terminal 1 — Backend (FastAPI + Agents)**
```bash
python main.py
# Server starts at http://localhost:8080
```

**Terminal 2 — Frontend (React Dashboard)**
```bash
cd stratify-react
npm install

# Point local dev at the deployed backend (optional — skips running backend locally)
echo "VITE_API_URL=https://stratify-api-868361801548.us-central1.run.app" > .env.local

npm run dev
# Dashboard opens at http://localhost:3000
```

The React frontend proxies API calls to the backend. Set `VITE_API_URL` in `.env.local` to use the deployed Cloud Run backend, or leave it unset to use a locally running `main.py`.

---

## 🏗️ Architecture

Stratify uses **Google ADK (Agent Development Kit)** with a **router-worker multi-agent pattern**:

```
┌──────────────────────────────────────────────────────┐
│            User Input (Situation)                    │
└─────────────────────┬────────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │   COMMANDER AGENT       │
         │   (Router & Synthesizer)│
         └────────┬───────┬────────┘
                  │       │
      ┌───────────┘       └──────────────┐
      │                                  │
  ┌───▼────────┐  ┌────────────┐  ┌─────▼──────────┐
  │ DATA       │  │ CONTEXT    │  │ TOOL OPERATOR  │
  │ MINER      │  │ AGENT      │  │ (Executor)     │
  │            │  │            │  │                │
  │ • Tasks    │  │ • SOPs     │  │ • Calendar     │
  │ • Dates    │  │ • Notes    │  │ • Reassign     │
  │ • Team     │  │ • Prior    │  │ • Log Action   │
  │ • Status   │  │   Calls    │  │                │
  └───┬────────┘  └──┬─────────┘  └────┬───────────┘
      │              │                 │
      └──────────────┬─────────────────┘
                     │
         ┌───────────▼───────────────┐
         │   MCP OPS AGENT           │
         │  (Infrastructure Checks)  │
         └───────────┬───────────────┘
                     │
         ┌───────────▼──────────────┐
         │  EXECUTIVE BRIEFING      │
         │  (Structured Output)     │
         └──────────────────────────┘
```

### Agent Roles

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Commander** | Routes requests, synthesizes final briefing | delegates to others |
| **Data Miner** | Queries live project state | task API, team DB, calendar |
| **Context Agent** | Searches organizational knowledge | SOP files, meeting notes, logs |
| **Tool Operator** | Executes real changes | Calendar API, task updates, logging |
| **MCP Ops Agent** | Infrastructure health checks | MCP protocol operations |

---

## 📁 Project Structure

```
agentic-war-room/
├── agents/                      # Multi-agent orchestration
│   ├── commander.py            # Router & synthesizer
│   ├── data_miner.py           # Task/team queries
│   ├── context_agent.py        # Knowledge search
│   ├── tool_operator.py        # Action executor
│   └── mcp_ops_agent.py        # Infrastructure checks
│
├── database/                    # Data persistence layer
│   ├── data_store.py           # Core store abstraction
│   ├── firestore_db.py         # Firestore backend
│   ├── alloydb_client.py       # AlloyDB backend
│   ├── chat_memory.py          # Conversation history
│   ├── agent_logger.py         # Action audit trail
│   ├── vector_store.py         # Embeddings for search
│   └── db_setup.py             # Initialization
│
├── stratify-react/             # React Dashboard (Primary UI)
│   ├── src/
│   │   ├── api/                # Backend API client
│   │   ├── components/         # React components
│   │   ├── pages/              # Page routes
│   │   └── App.tsx             # Main app
│   ├── Dockerfile.frontend     # Container build
│   └── package.json            # Node dependencies
│
├── mcp_servers/                # Model Context Protocol
│   └── stratify_mcp_server.py  # MCP endpoint
│
├── main.py                     # FastAPI backend server
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables template
├── Dockerfile                  # Backend container
├── deploy.sh                   # Cloud Run deployment script
└── README.md                   # This file
```

---

## 🛠️ Tech Stack

<details open>
<summary><b>Click to expand/collapse</b></summary>

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React + TypeScript + Vite | Modern interactive dashboard UI |
| **Backend** | FastAPI + Uvicorn | High-performance REST API |
| **AI Orchestration** | Google ADK | Multi-agent coordination |
| **LLM Model** | Gemini 2.5 Flash | Primary reasoning engine |
| **Fallback Model** | Gemini 2.5 Flash Lite | Cost-optimized fallback |
| **Inference** | Vertex AI | GCP managed inference |
| **Database (Primary)** | Firestore | NoSQL real-time syncing |
| **Database (Optional)** | SQLite | Local development alternative |
| **SQL DB (Optional)** | AlloyDB | PostgreSQL-compatible option |
| **Deployment** | Cloud Run | Serverless container platform |
| **CI/CD** | Cloud Build | Automated build & deploy |
| **Registry** | Artifact Registry | Container image storage |
| **Credentials** | Google Cloud Auth | OAuth 2.0 integration |

</details>

---

## ⚙️ Configuration

All configuration comes from environment variables. Create a `.env` file in the project root:

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Vertex AI & Gemini
GOOGLE_GENAI_USE_VERTEXAI=true
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
GOOGLE_API_KEY=your-api-key

# Stratify App
STRATIFY_BACKEND_URL=http://localhost:8080
STRATIFY_API_KEY=your-shared-secret-key
STRATIFY_DISABLE_UI_AUTH=false

# Database
USE_FIRESTORE=true
FIRESTORE_DATABASE_ID=war-room-id
FIRESTORE_PROJECT_ID=your-gcp-project-id

# Optional: AlloyDB
ALLOYDB_HOST=your-alloydb-ip
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your-db-password
ALLOYDB_DATABASE=warroom_db

# Optional: Slack & GitHub Integration
SLACK_BOT_TOKEN=xoxb-...
GITHUB_TOKEN=ghp_...

# Operations
DEFAULT_HUDDLE_EMAIL=your-email@company.com
```

<details>
<summary><b>Configuration Details</b></summary>

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | string | - | GCP project ID for Vertex AI |
| `GOOGLE_CLOUD_LOCATION` | string | us-central1 | Vertex AI region (us-central1, us-west1, etc) |
| `GOOGLE_GENAI_USE_VERTEXAI` | bool | true | Use Vertex AI (vs local Gemini API) |
| `GEMINI_MODEL` | string | gemini-2.5-flash | Primary inference model |
| `GEMINI_FALLBACK_MODEL` | string | gemini-2.5-flash-lite | Fallback for cost optimization |
| `STRATIFY_BACKEND_URL` | URL | http://localhost:8080 | Backend endpoint for frontend |
| `STRATIFY_API_KEY` | string | - | Shared secret for frontend→backend auth |
| `STRATIFY_DISABLE_UI_AUTH` | bool | false | Skip login screen if true |
| `USE_FIRESTORE` | bool | true | Use Firestore (false = SQLite) |
| `FIRESTORE_DATABASE_ID` | string | war-room-id | Firestore database name |
| `DEFAULT_HUDDLE_EMAIL` | email | - | Email for auto-created Calendar meetings |

</details>

---

## 🔧 Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. GCP Authentication

```bash
# Initialize gcloud
gcloud init

# Set your project
gcloud config set project PROJECT_ID

# Authenticate
gcloud auth application-default login
```

### 3. Run Backend

```bash
# Terminal 1
python main.py

# Should output:
# INFO:     Uvicorn running on http://0.0.0.0:8080
# INFO:     Press CTRL+C to quit
```

### 4. Run Frontend

```bash
# Terminal 2
cd stratify-react
npm install
npm run dev

# Should output:
# VITE ready in Xms
# Local:   http://localhost:3000/
```

### Testing an Analysis

```bash
# Terminal 3 (or cURL)
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"situation": "Lead developer is out sick, launch is in 2 days"}'
```

Expected response:
```json
{
  "briefing": "...",
  "actions_taken": [...],
  "risk_level": "HIGH",
  "recommendations": [...]
}
```

---

## ☁️ Cloud Deployment

<details open>
<summary><b>Automated Deployment with deploy.sh</b></summary>

The included `deploy.sh` automates the entire build & deploy pipeline using **Cloud Build** (no local Docker required):

```bash
bash deploy.sh [PROJECT_ID]
# Default project: project-track-1-491917
```

This script:
1. Sets the active GCP project
2. Deploys backend to Cloud Run via `gcloud run deploy --source`
3. Captures the backend URL
4. Writes `VITE_API_URL` into `stratify-react/.env.production`
5. Deploys frontend to Cloud Run
6. Prints both live URLs

### Live URLs

| Service | URL |
|---|---|
| **Frontend** | https://stratify-frontend-868361801548.us-central1.run.app |
| **Backend API** | https://stratify-api-868361801548.us-central1.run.app |

### Manual Deployment

**Backend:**
```bash
gcloud run deploy stratify-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=PROJECT_ID,GOOGLE_GENAI_USE_VERTEXAI=true,..."
```

**Frontend:**
```bash
# Swap Dockerfiles so Cloud Build picks the React one
mv Dockerfile Dockerfile.backend && mv Dockerfile.frontend Dockerfile

gcloud run deploy stratify-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated

mv Dockerfile Dockerfile.frontend && mv Dockerfile.backend Dockerfile
```

</details>

---

## 🔌 API Reference

All endpoints require `STRATIFY_API_KEY` header (if auth is enabled).

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### Interactive Analysis

```http
POST /analyze
Content-Type: application/json

{
  "situation": "Lead backend engineer is out with flu, launch is in 48 hours, API rate limiting task is blocked"
}
```

Response:
```json
{
  "briefing": "CRITICAL: Launch at risk due to staffing gap...",
  "risk_level": "HIGH",
  "actions_taken": [
    {
      "type": "calendar_event",
      "status": "created",
      "details": "Emergency huddle scheduled 10am tomorrow"
    },
    {
      "type": "task_reassignment",
      "task_id": "TASK-123",
      "old_owner": "john@company.com",
      "new_owner": "jane@company.com"
    }
  ],
  "recommendations": [
    "Pause non-critical features",
    "Reduce test coverage scope"
  ]
}
```

### Daily Health Check

```http
POST /analyze-daily
```

Autonomously scans project for risks, runs on schedule.

### MCP Operations

```http
POST /analyze-mcp
Content-Type: application/json

{
  "operation": "system_health_check"
}
```

---

## 📚 Documentation

<details>
<summary><b>Additional Resources</b></summary>

- [Google ADK Documentation](https://cloud.google.com/agents)
- [Vertex AI API Reference](https://cloud.google.com/vertex-ai/docs)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [React + Vite Documentation](https://vitejs.dev/)
- [Firestore Guide](https://cloud.google.com/firestore/docs)

</details>

---


## 🐛 Troubleshooting

<details>
<summary><b>Common Issues & Solutions</b></summary>

### Frontend Won't Connect to Backend
```
Error: "Failed to connect to http://localhost:8080"
```
**Solution:**
- Ensure `main.py` is running in Terminal 1
- Check `VITE_API_URL` in `stratify-react/.env.local`
- Verify firewall isn't blocking port 8080

### Vertex AI Authentication Failed
```
Error: "Could not automatically determine credentials"
```
**Solution:**
- Run `gcloud auth application-default login`
- Ensure `GOOGLE_CLOUD_PROJECT` is set correctly in `.env`

### Firestore Connection Timeout
```
Error: "Timeout while connecting to Firestore"
```
**Solution:**
- Verify Firestore is enabled in GCP project
- Check network connectivity to Cloud
- Switch to SQLite with `USE_FIRESTORE=false`

### Agent Analysis Hangs
```
Analysis taking >5 minutes with no output
```
**Solution:**
- Check backend logs for errors: `tail -f logs.txt`
- Increase Vertex AI quotas in GCP console
- Reduce complexity of initial situation description

### Port Already in Use
```
Error: "Address already in use: ('0.0.0.0', 8080)"
```
**Solution:**
- Kill existing process: `lsof -i :8080` (macOS/Linux) or `netstat -ano | findstr :8080` (Windows)
- Change port: `python main.py --port 9000`

</details>

---

## 👥 Team

Built with ❤️ by:
- **Amaan Khan** — Agent Architecture & Backend
- **Srishti Rathi** — Frontend & UI/UX

---

## 📄 License

This project is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.

**In short:** You're free to use, modify, and distribute this software, including in commercial projects. Just include the license and copyright notice.

### Attribution

If you find this project useful, please consider:
- ⭐ Starring the repository
- 🔄 Sharing it with others
- 🐛 Contributing improvements
- 💬 Providing feedback

---

---

<div align="center">

**[⬆ back to top](#-stratify)**

</div>
