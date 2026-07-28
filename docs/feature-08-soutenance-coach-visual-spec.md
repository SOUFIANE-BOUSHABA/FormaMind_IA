# Feature 08 - Soutenance Coach Agent

## Goal

Feature 08 adds an authenticated oral-defense simulator for FormaMind AI. The
learner creates a soutenance session, answers one jury-style question at a time,
then receives a structured report with score, readiness level, strengths,
missing concepts, recommendations, and improved answers.

The feature is intentionally MVP-friendly: no microphone, webcam, WebSocket,
Redis, Celery, or background worker. The learner types the answer that would
normally be spoken.

## Backend Lifecycle

1. `POST /api/v1/soutenance-sessions`
   - `app.api.routes.soutenance.create_soutenance_session`
   - Authenticates the user and sends the request to
     `SoutenanceSessionService.create_session`.

2. `SoutenanceSessionService`
   - Builds a safe `ProjectContextSnapshot`.
   - Builds a learner-scoped `LearnerProfileSnapshot`.
   - Provides deterministic `SoutenanceRubricTool`.
   - Calls `SoutenanceCoachAgent.generate_questions`.
   - Validates the returned `SoutenanceSessionDraft`.
   - Persists `SoutenanceSession` and `SoutenanceQuestion` rows.

3. `SoutenanceCoachAgent`
   - Uses CrewAI `Agent`, `Task`, and `Crew`.
   - Uses Gemini through CrewAI when `GEMINI_API_KEY` is configured.
   - Uses safe fallback generation if the LLM output is unavailable or invalid.
   - Produces varied jury questions across categories.

4. `GET /api/v1/soutenance-sessions/{id}/current-question`
   - Returns only the current unanswered `PublicSoutenanceQuestion`.
   - Keeps the session sequential and simple to test.

5. `POST /api/v1/soutenance-sessions/{id}/answers`
   - Validates the question is the current question.
   - Rejects duplicate answers.
   - Calls `SoutenanceCoachAgent.evaluate_answer`.
   - Validates rubric criteria with `SoutenanceRubricTool`.
   - Persists `SoutenanceAnswer` and `SoutenanceRubricScore`.
   - Advances `current_question_index`.
   - Completes the session automatically after the final answer.

6. `GET /api/v1/soutenance-sessions/{id}/results`
   - Returns the final score, readiness level, category scores, weaknesses,
     missing concepts, recommendations, and improved answers.

## Agentic Responsibilities

The Soutenance Coach Agent is not just a direct LLM call. It receives tools and
has explicit task responsibilities:

- read a project-context snapshot using `ProjectContextTool`;
- read learner readiness and weak areas using `LearnerProfileTool`;
- select question categories and difficulty from the request;
- generate multiple distinct jury questions;
- evaluate the learner answer with a deterministic rubric;
- create feedback, missing concepts, improved answer, and next action.

## Data Model

- `SoutenanceSession`
  - owner-scoped by `user_id`;
  - stores mode, difficulty, status, question count, progress, final score, and
    aggregate feedback.

- `SoutenanceQuestion`
  - belongs to one session;
  - stores category, difficulty, expected concepts, evaluation focus, and answer
    status.

- `SoutenanceAnswer`
  - one answer per question;
  - stores the learner answer, total score, feedback, strengths, missing
    concepts, improved answer, and recommendation.

- `SoutenanceRubricScore`
  - stores per-criterion score, weight, and comment.

## Frontend Lifecycle

1. `/soutenance`
   - `SoutenanceSessionsPage`
   - Shows session creation controls and history.

2. `/soutenance/:sessionId`
   - `SoutenanceSessionPage`
   - Shows progress, current question, answer textarea, and training feedback.
   - In jury mode, feedback is hidden until results.

3. `/soutenance/:sessionId/results`
   - `SoutenanceResultsPage`
   - Shows final report, category scores, rubric feedback, and improved answers.

## Files

- Backend models: `backend/app/models/soutenance.py`
- Backend migration:
  `backend/alembic/versions/20260726_0006_create_soutenance_sessions.py`
- Backend schemas: `backend/app/schemas/soutenance.py`
- Backend tools: `backend/app/tools/soutenance_tools.py`
- Backend agent: `backend/app/agents/soutenance_coach_agent.py`
- Backend repository: `backend/app/repositories/soutenance.py`
- Backend service: `backend/app/services/soutenance.py`
- Backend routes: `backend/app/api/routes/soutenance.py`
- Frontend API: `frontend/src/features/soutenance/api/soutenance-api.ts`
- Frontend hooks: `frontend/src/features/soutenance/hooks/useSoutenance.ts`
- Frontend pages: `frontend/src/features/soutenance/pages/*`

## Soutenance Explanation

For the professor: this agent prepares and evaluates an oral defense. It has
tools, stateful persisted sessions, a deterministic rubric, user-scoped profile
context, question progression, answer evaluation tasks, and final reporting. The
LLM is used for generation/evaluation, but the application service controls the
workflow, validation, persistence, and scoring boundaries.

See `docs/feature-08-soutenance-coach-lifecycle.svg` for the visual lifecycle.
