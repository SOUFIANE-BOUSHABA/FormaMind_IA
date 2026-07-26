# FormaMind AI

FormaMind AI is a premium multi-agent educational platform. The product supports document-grounded learning, assessments, personalized roadmaps, and future oral-defense simulation. The current repository includes authentication, dashboard, PDF/RAG flows, assessment generation, and Learning Coach learning plans.

## Repository Structure

```text
frontend/   React, TypeScript, Vite, Tailwind CSS
backend/    FastAPI, SQLAlchemy, Alembic, pytest
docs/       Architecture notes
```

## Technology Stack

- Backend: Python 3.11+, FastAPI, Pydantic, pydantic-settings, SQLAlchemy, Alembic, JWT authentication, LlamaIndex, Chroma, CrewAI, pytest, Ruff.
- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, React Hook Form, Zod.
- Styling: CSS custom properties connected to Tailwind tokens, inspired by the Stitch export.

## Local Prerequisites

- Python 3.11 or newer.
- Node.js and npm.
- Git.

On Windows PowerShell, use `npm.cmd` if script execution policy blocks `npm`.

## Backend Installation

Run from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
python -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ".[dev]"
```

## Frontend Installation

Run from `frontend/`:

```powershell
npm.cmd install
```

Linux/macOS:

```bash
npm install
```

## Environment Setup

Copy the examples if local overrides are needed:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Do not commit real secrets. The development JWT secret in `.env.example` is for local use only.

## Development Commands

Backend commands run from `backend/`:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m ruff format --check .
```

Frontend commands run from `frontend/`:

```powershell
npm.cmd run dev
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

## Current Implementation Status

Implemented:

- Monorepo folder foundation.
- FastAPI application setup.
- `/api/v1/health` endpoint.
- User model and JWT authentication endpoints.
- Protected `/api/v1/dashboard/summary` endpoint.
- Protected PDF document endpoints under `/api/v1/documents`.
- Secure local PDF storage with metadata persistence.
- LlamaIndex PDF chunking, embeddings, Chroma vector retrieval, and document processing.
- Agentic Knowledge Agent with memory, retrieval decisions, and citation verification.
- CrewAI Assessment Agent with generated evaluations and source-grounded questions.
- Assessment attempts, scoring, results, and Assessment Coach feedback.
- Learning Coach Agent with persisted learning plans, scheduled activities, progress tracking, and dashboard recommendations.
- SQLAlchemy and Alembic setup.
- React/Vite frontend setup.
- Strict TypeScript configuration.
- Tailwind and design token foundation.
- Authenticated application shell.
- Premium dashboard screen based on the Stitch reference.
- Documents management screen based on the Stitch reference.
- Assistant, assessments, results, and learning-plan screens.
- Protected placeholders for remaining future product routes.
- Project and architecture documentation.

Not implemented:

- Soutenance simulation, reports backend, admin roles, Redis/Celery/WebSockets.
- Dashboard database tables or analytics persistence.
- Docker, deployment, or CI/CD.

The dashboard currently mixes real persisted learning/evaluation/document data with deterministic summary calculations. It does not have dedicated analytics tables yet.
