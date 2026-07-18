from fastapi import APIRouter

from app.api.routes import auth, dashboard, health

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(health.router, tags=["health"])
