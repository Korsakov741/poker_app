"""
Punto 12 — Registro de decisión: junta el `DecisionPackage` del
Punto 8 con la acción REAL que el usuario tomó (que puede diferir de
la recomendada). Esto es, en rigor, la segunda mitad del principio
no-negociable #1 del proyecto ("la app debe permitirme ingresar la
acción real que tomé... y recalcular") — no había un lugar dedicado a
esto todavía; nace acá porque es exactamente lo que el Punto 12
necesita como input.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..final_decision.decision_engine import DecisionPackage


@dataclass
class RecordedDecision:
    hand_id: str
    street: str
    decision_package: DecisionPackage
    actual_action_taken: str

    @property
    def best_recommendation(self) -> str | None:
        if not self.decision_package.candidates:
            return None
        return self.decision_package.candidates[0].action

    @property
    def matched_top_recommendation(self) -> bool:
        return self.actual_action_taken == self.best_recommendation

    @property
    def value_gap(self) -> float:
        """
        Diferencia entre el valor heurístico del mejor candidato y el
        de la acción que realmente se tomó — siempre >= 0 (el mejor
        candidato, por definición, tiene el valor más alto o igual).
        Es la medida central de "dónde se perdió más valor".
        """
        candidates_by_action = {c.action: c.heuristic_value for c in self.decision_package.candidates}
        if not candidates_by_action:
            return 0.0
        best_value = max(candidates_by_action.values())
        actual_value = candidates_by_action.get(self.actual_action_taken, 0.0)
        return max(0.0, best_value - actual_value)


def record_decision(
    hand_id: str, street: str, decision_package: DecisionPackage, actual_action_taken: str
) -> RecordedDecision:
    return RecordedDecision(
        hand_id=hand_id, street=street, decision_package=decision_package,
        actual_action_taken=actual_action_taken,
    )
