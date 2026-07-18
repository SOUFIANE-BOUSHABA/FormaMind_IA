# FormaMind AI

FormaMind AI is a premium multi-agent educational platform. The future product will support document-grounded learning, assessments, personalized roadmaps, and oral-defense simulation. The current repository includes the project foundation, authentication, and the protected dashboard layout.

## Repository Structure

```text
frontend/   React, TypeScript, Vite, Tailwind CSS
backend/    FastAPI, SQLAlchemy, Alembic, pytest
docs/       Architecture notes
```

## Technology Stack

- Backend: Python 3.11+, FastAPI, Pydantic, pydantic-settings, SQLAlchemy, Alembic, JWT authentication, pytest, Ruff.
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
- SQLAlchemy and Alembic setup.
- React/Vite frontend setup.
- Strict TypeScript configuration.
- Tailwind and design token foundation.
- Authenticated application shell.
- Premium dashboard screen based on the Stitch reference.
- Protected placeholders for future product routes.
- Project and architecture documentation.

Not implemented:

- PDF upload.
- RAG, vector storage, LLMs, or real AI agents.
- Quiz generation, assessments, learning plans, reports, or soutenance simulation.
- Dashboard database tables or analytics persistence.
- Docker, deployment, or CI/CD.

The dashboard currently uses a deterministic summary service. It does not run AI agents or read analytics from product tables yet.
