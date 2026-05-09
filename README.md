<div align="center">

# 🛡️ Stratify

**AI-powered project operations — describe the situation, the agents handle the rest.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Frontend-blue?style=for-the-badge)](https://stratify-frontend-868361801548.asia-south1.run.app)
[![Backend](https://img.shields.io/badge/API-Backend-green?style=for-the-badge)](https://stratify-backend-868361801548.asia-south1.run.app/health)
[![Built with Google ADK](https://img.shields.io/badge/Google%20ADK-Multi--Agent-orange?style=for-the-badge)](https://cloud.google.com/vertex-ai)
[![Gemini](https://img.shields.io/badge/Model-Gemini%202.5%20Flash-purple?style=for-the-badge)](https://deepmind.google/technologies/gemini/)

</div>

---

## What is Stratify?

Stratify is a cloud-deployed multi-agent operations dashboard. You describe a real project situation in plain English — a blocked task, a sick developer, a production incident — and a team of AI agents analyzes your live project data, applies SOPs, takes real actions (Calendar huddles, task reassignments, action logs), and delivers a structured executive briefing.

No forms. No ticket filing. Just describe what's happening.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent Analysis** | Commander routes work across Data Miner, Context, and Tool Operator agents |
| 📊 **Live Dashboard** | Dark executive UI with task metrics, team capacity, and action log |
| 📅 **Real Calendar Huddles** | Auto-creates Google Calendar emergency meetings on critical risk |
| 🗂️ **Task & Team Management** | Add, update, filter, and export tasks and team members |
| 🔁 **Daily Health Check** | Autonomous proactive project health scan |
| 🔌 **MCP Operations Mode** | Protocol-oriented ops checks via Model Context Protocol |
| 📋 **Action Log** | Full audit trail of every agent action taken |
| 🔐 **Auth-gated UI** | Optional access key protection for the dashboard |

---

## 🧠 Agent Architecture

Stratify uses **Google ADK** with a router-worker pattern:

```
          User Situation
                │
                ▼
     ┌──────────────────────┐
     │    Commander Agent   │
     └──────────┬───────────┘
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│Data Miner│ │ Context  │ │Tool Operator │
│          │ │  Agent   │ │              │
│ tasks ·  │ │SOPs ·    │ │ Calendar ·   │
│ deadlines│ │notes ·   │ │ reassign ·   │
│ team     │ │decisions │ │ action log   │
└──────────┘ └──────────┘ └──────────────┘
```

- **Commander** — reads the situation, delegates, synthesizes the final briefing
- **Data Miner** — queries live tasks, priorities, deadlines, team availability
- **Context Agent** — searches SOPs, meeting notes, prior decisions
- **Tool Operator** — takes real actions: Calendar huddles, task updates, logging
- **MCP Ops Agent** — MCP-protocol operational checks

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| AI Orchestration | Google ADK |
| Model | Gemini 2.5 Flash via Vertex AI |
| Database | SQLite (default) · Firestore (optional) |
| Deployment | Google Cloud Run |
| Build | Google Cloud Build |
| Registry | Artifact Registry |

---

## 🚀 Local Development

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Set environment variables** (create a `.env` file)
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
GEMINI_MODEL=gemini-2.5-flash
```

**3. Start the backend**
```bash
python main.py
```

**4. Start the frontend** (in a separate terminal)
```bash
streamlit run frontend/app.py
```

Frontend will connect to the backend at `http://127.0.0.1:8080` by default.

---

## ⚙️ Environment Variables

| Variable | Purpose |
|---|---|
| `STRATIFY_BACKEND_URL` | Backend URL used by the frontend |
| `STRATIFY_API_KEY` | Shared app key for frontend→backend auth |
| `STRATIFY_DISABLE_UI_AUTH` | Set `true` to skip the access screen |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region (e.g. `us-central1`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set `true` to use Vertex AI mode |
| `GEMINI_MODEL` | Primary model (`gemini-2.5-flash`) |
| `GEMINI_FALLBACK_MODEL` | Fallback model (`gemini-2.5-flash-lite`) |
| `USE_FIRESTORE` | Set `true` to switch from SQLite to Firestore |

---

## ☁️ Cloud Run Deployment

Two services, independently deployable:

```
stratify-backend   →  FastAPI + ADK agent orchestration
stratify-frontend  →  Streamlit dashboard UI
```

**Build and deploy backend:**
```bash
gcloud builds submit --tag asia-south1-docker.pkg.dev/PROJECT_ID/war-room/war-room-backend:latest
gcloud run deploy stratify-backend --image ... --region asia-south1
```

**Build and deploy frontend:**
```bash
# uses Dockerfile.frontend
gcloud run deploy stratify-frontend --image ... --region asia-south1
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/analyze` | Run interactive agent analysis |
| `POST` | `/analyze-daily` | Trigger autonomous daily health check |
| `POST` | `/analyze-mcp` | Run MCP ops mode analysis |

---

## 👥 Team

Built by **Amaan Khan** and **Srishti Rathi**
