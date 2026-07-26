from fastapi import APIRouter

from app.api.routes import (
    assessments,
    assistant,
    attempts,
    auth,
    dashboard,
    documents,
    health,
    learning_plans,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(assistant.router, tags=["assistant"])
api_router.include_router(assessments.router, tags=["assessments"])
api_router.include_router(attempts.router, tags=["attempts"])
api_router.include_router(learning_plans.router, tags=["learning-plans"])
api_router.include_router(health.router, tags=["health"])
