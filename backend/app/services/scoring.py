from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def round_score(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP))


def calculate_percentage(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0

    return round_score((score / max_score) * 100)


def level_from_percentage(percentage: float) -> str:
    if percentage >= 90:
        return "Expert"
    if percentage >= 75:
        return "Avance"
    if percentage >= 55:
        return "Intermediaire"
    if percentage >= 35:
        return "Debutant"
    return "A renforcer"
