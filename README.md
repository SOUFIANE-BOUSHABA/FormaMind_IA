# FormaMind AI

FormaMind AI is a premium multi-agent educational platform foundation. The future product will support document-grounded learning, assessments, personalized roadmaps, and oral-defense simulation. This repository currently implements only the technical foundation.

## Repository Structure

```text
frontend/   React, TypeScript, Vite, Tailwind CSS
backend/    FastAPI, SQLAlchemy, Alembic, pytest
docs/       Architecture notes
```

## Technology Stack

- Backend: Python 3.11+, FastAPI, Pydantic, pydantic-settings, SQLAlchemy, Alembic, pytest, Ruff.
- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Zod.
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

No real secrets are required for the current foundation.

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
- SQLAlchemy and Alembic foundation without business entities.
- React/Vite frontend setup.
- Strict TypeScript configuration.
- Tailwind and design token foundation.
- Minimal French placeholder route.
- Project and architecture documentation.

Not implemented:

- Authentication.
- Dashboard screens.
- PDF upload.
- RAG, vector storage, LLMs, or AI agents.
- Quiz generation, assessments, learning plans, reports, or soutenance simulation.
- Docker, deployment, or CI/CD.

Only the project foundation is implemented.
