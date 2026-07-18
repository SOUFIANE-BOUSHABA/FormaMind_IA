from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DbSession
from app.repositories.document import DocumentRepository
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard")


@router.get("/summary", response_model=DashboardSummary)
def read_dashboard_summary(
    current_user: CurrentUser,
    db: DbSession,
) -> DashboardSummary:
    return DashboardService(DocumentRepository(db)).get_summary(current_user)
