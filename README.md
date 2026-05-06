# Project War-Room

Project War-Room is a cloud-deployed multi-agent operations dashboard for project risk, delivery blockers, team availability, action logging, and AI-assisted incident response.

The app combines a polished dark dashboard UI with a FastAPI backend, Google ADK agents, Gemini reasoning, SQLite-backed local project data, optional Firestore support, and Cloud Run deployment.

## Live Deployment

- Frontend: https://war-room-frontend-bdtynmiyrq-el.a.run.app
- Backend: https://war-room-backend-bdtynmiyrq-el.a.run.app
- Health check: https://war-room-backend-bdtynmiyrq-el.a.run.app/health

## Core Features

- Introductory home page with shortcuts into the operational workspace
- Dark executive dashboard with project metrics, navigation, and quick insight panels
- Agent analysis page for natural-language project situations
- Executive summary output with red flags, actions taken, and recommendations
- Daily autonomous project health check
- MCP operations check mode for protocol-oriented operational workflows
- Current tasks page with search, filtering, priority/status visibility, and CSV export
- Team page for availability and team member review
- Action log page for auditability
- Manage Data page for adding, updating, and deleting tasks or team members
- About page explaining the architecture and workflow
- SQLite-backed persistence for tasks, team members, action logs, agent runs, and chat memory
- Optional Firestore integration through environment configuration
- Cloud Run deployment with separate backend and frontend services

## Agent Architecture

Project War-Room uses Google ADK with a router-worker pattern:

- Commander Agent: reads the user situation, routes work, and produces the final operational briefing
- Data Miner Agent: checks project task state, priorities, deadlines, team availability, and action data
- Context Agent: adds operating context, SOP-style guidance, and prior-decision awareness
- Tool Operator Agent: attempts concrete operational actions when risk is high
- MCP Ops Agent: supports MCP-oriented operational checks

## Tech Stack

- Frontend: Streamlit
- Backend: FastAPI
- AI orchestration: Google ADK
- Model: Gemini 2.5 Flash through Vertex AI / Google GenAI configuration
- Data: SQLite by default, optional Firestore
- Deployment: Google Cloud Run
- Build pipeline: Google Cloud Build
- Container registry: Artifact Registry

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python main.py
```

Start the frontend in another terminal:

```bash
streamlit run frontend/app.py
```

By default, the frontend expects the backend at `http://127.0.0.1:8080`.

## Environment Variables

Useful variables:

- `WAR_ROOM_BACKEND_URL`: backend URL used by the frontend
- `WAR_ROOM_API_KEY`: shared frontend-to-backend app key when enabled
- `WAR_ROOM_DISABLE_UI_AUTH`: set to `true` to skip the UI access screen
- `GOOGLE_CLOUD_PROJECT`: Google Cloud project for Vertex AI
- `GOOGLE_CLOUD_LOCATION`: Vertex AI location, for example `us-central1`
- `GOOGLE_GENAI_USE_VERTEXAI`: set to `true` for Vertex AI mode
- `GEMINI_MODEL`: primary model, currently `gemini-2.5-flash`
- `GEMINI_FALLBACK_MODEL`: fallback model, currently `gemini-2.5-flash-lite`
- `USE_FIRESTORE`: set to `true` to use Firestore instead of SQLite for data-store helpers

## Cloud Run Deployment

The project is deployed as two services:

- `war-room-backend`: FastAPI API and ADK agent orchestration
- `war-room-frontend`: Streamlit dashboard UI

Images are stored in Artifact Registry:

```text
asia-south1-docker.pkg.dev/project-track-1-491917/war-room/war-room-backend:latest
asia-south1-docker.pkg.dev/project-track-1-491917/war-room/war-room-frontend:latest
```

## Streamlit Note

The current app relies on Streamlit only for the frontend. The backend is already separate FastAPI, so the clean path away from Streamlit is to rebuild the UI in React, Next.js, or Vite and call the existing backend endpoints:

- `GET /health`
- `POST /analyze`
- `POST /analyze-daily`
- `POST /analyze-mcp`

That migration would give smoother navigation, full control over animations, stronger production UI patterns, and easier custom branding while preserving the current backend and agents.

## Team

Built by:

- Amaan Khan
- Srishti Rathi
