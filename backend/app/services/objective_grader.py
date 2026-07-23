from __future__ import annotations

from dataclasses import dataclass

from app.models.assessment import Question, StudentAnswer


@dataclass(frozen=True)
class ObjectiveGrade:
    points_awarded: float
    evaluation_status: str
    is_correct: bool
    feedback: str
    missing_concepts: list[str]


class ObjectiveQuestionGrader:
    def grade(self, *, question: Question, answer: StudentAnswer) -> ObjectiveGrade:
        correct_option = next(
            (option for option in question.options if option.is_correct),
            None,
        )
        if correct_option is None:
            msg = f"Question {question.id} has no correct option."
            raise ValueError(msg)

        if answer.selected_option_id is None:
            return ObjectiveGrade(
                points_awarded=0.0,
                evaluation_status="unanswered",
                is_correct=False,
                feedback="Aucune reponse fournie.",
                missing_concepts=[],
            )

        if answer.selected_option_id == correct_option.id:
            return ObjectiveGrade(
                points_awarded=float(question.points),
                evaluation_status="correct",
                is_correct=True,
                feedback="Bonne reponse.",
                missing_concepts=[],
            )

        return ObjectiveGrade(
            points_awarded=0.0,
            evaluation_status="incorrect",
            is_correct=False,
            feedback=(
                f"Reponse incorrecte. La bonne reponse etait : {correct_option.text}"
            ),
            missing_concepts=[correct_option.text[:120]],
        )
