# FormaMind AI Architecture

Planned high-level flow:

```text
React frontend
    ↓
FastAPI REST API
    ↓
Application services
    ↓
Workflow orchestrator
    ├── Knowledge Agent
    ├── Assessment Agent
    └── Learning Coach Agent
    ↓
Database and vector store
```

## Boundaries

- The workflow orchestrator coordinates agents, but it is not a fourth agent.
- API routes must remain thin and must not contain business logic.
- Application services own use-case coordination and validation boundaries.
- Agents must not directly manage HTTP or database infrastructure.
- Agent outputs will later use validated Pydantic schemas.
- RAG logic will remain separated from agent definitions.
- Database models will be introduced feature by feature.
- Frontend features communicate with the backend through typed services and TanStack Query.
- Stitch remains the visual source of truth for future UI work, but generated static HTML must not be copied directly.

## Current Implementation

The current implementation includes:

- FastAPI app setup.
- Health endpoint.
- SQLAlchemy and Alembic readiness.
- User model and JWT authentication.
- Protected dashboard summary endpoint.
- Document metadata model with owner-scoped PDF upload/list/details/delete endpoints.
- Local PDF storage under a configurable upload directory.
- React/Vite app setup.
- Authenticated application shell.
- Premium dashboard layout based on Stitch.
- Documents management layout based on Stitch.
- Tailwind design token foundation.
- Documentation.

No agents, RAG text extraction, embeddings, assessments, learning-plan generation, soutenance simulation, reports backend, or vector store are implemented yet.
