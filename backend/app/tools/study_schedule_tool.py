from __future__ import annotations

import json
from datetime import date, timedelta

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ScheduleActivityInput(BaseModel):
    temp_id: str = Field(min_length=1, max_length=80)
    duration_minutes: int = Field(ge=5, le=240)


class StudyScheduleToolInput(BaseModel):
    activities: list[ScheduleActivityInput] = Field(min_length=1)
    daily_minutes: int = Field(ge=15, le=240)
    start_date: date
    intensity: str = Field(default="balanced", max_length=40)


class StudyScheduleTool(BaseTool):
    name: str = "StudyScheduleTool"
    description: str = (
        "Construit un planning d'etude deterministe en respectant les minutes "
        "disponibles par jour."
    )
    args_schema: type[BaseModel] = StudyScheduleToolInput

    def _run(
        self,
        activities: list[dict[str, object]],
        daily_minutes: int,
        start_date: date | str,
        intensity: str = "balanced",
    ) -> str:
        parsed_start = start_date
        if not isinstance(start_date, date):
            parsed_start = date.fromisoformat(start_date)
        parsed_activities = [
            ScheduleActivityInput.model_validate(activity) for activity in activities
        ]
        schedule = self.build_schedule(
            activities=parsed_activities,
            daily_minutes=daily_minutes,
            start_date=parsed_start,
            intensity=intensity,
        )
        return json.dumps(schedule, ensure_ascii=False, indent=2)

    def build_schedule(
        self,
        *,
        activities: list[ScheduleActivityInput],
        daily_minutes: int,
        start_date: date,
        intensity: str,
    ) -> dict[str, object]:
        if daily_minutes < 15:
            raise ValueError("daily_minutes must be at least 15.")

        schedule: dict[str, str] = {}
        current_date = start_date
        used_today = 0
        gap = 2 if intensity == "light" else 1

        for activity in activities:
            if activity.duration_minutes > daily_minutes and used_today > 0:
                current_date += timedelta(days=gap)
                used_today = 0

            if used_today + activity.duration_minutes > daily_minutes:
                current_date += timedelta(days=gap)
                used_today = 0

            schedule[activity.temp_id] = current_date.isoformat()
            used_today += min(activity.duration_minutes, daily_minutes)

        target_end_date = max(date.fromisoformat(value) for value in schedule.values())
        return {
            "target_end_date": target_end_date.isoformat(),
            "activities": schedule,
        }
