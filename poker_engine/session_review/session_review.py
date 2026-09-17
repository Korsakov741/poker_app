"""
Punto 12 — Agregador de sesión completa: junta todos los
`RecordedDecision` de una sesión y responde las dos preguntas que
pide el roadmap general: "qué manos revisar" y "dónde se perdió más
valor entre sesiones".
"""
from __future__ import annotations
from collections import defaultdict

from .recorded_decision import RecordedDecision


class SessionReview:
    def __init__(self, session_label: str):
        self.session_label = session_label
        self.decisions: list[RecordedDecision] = []

    def add(self, decision: RecordedDecision) -> None:
        self.decisions.append(decision)

    def hands_to_review(self, top_n: int = 10) -> list[RecordedDecision]:
        """Las decisiones con mayor `value_gap` primero — las que más vale la pena repasar."""
        return sorted(self.decisions, key=lambda d: -d.value_gap)[:top_n]

    def total_value_lost(self) -> float:
        return sum(d.value_gap for d in self.decisions)

    def value_lost_by_street(self) -> dict[str, float]:
        result: dict[str, float] = defaultdict(float)
        for d in self.decisions:
            result[d.street] += d.value_gap
        return dict(result)

    def match_rate(self) -> float | None:
        """% de decisiones donde la acción real coincidió con la mejor recomendada."""
        if not self.decisions:
            return None
        matches = sum(1 for d in self.decisions if d.matched_top_recommendation)
        return matches / len(self.decisions) * 100

    def summary(self) -> dict:
        return {
            "session": self.session_label,
            "n_decisions": len(self.decisions),
            "total_value_lost": round(self.total_value_lost(), 3),
            "value_lost_by_street": {k: round(v, 3) for k, v in self.value_lost_by_street().items()},
            "match_rate_pct": round(self.match_rate(), 1) if self.match_rate() is not None else None,
        }
