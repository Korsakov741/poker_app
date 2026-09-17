"""
HandTypeMatrix — la estructura central del Punto 2: los 169 tipos de
mano con un peso [0,1] cada uno, con los TRES métodos de entrada
manual que pide el resumen técnico:
  (a) pintar en la grilla       -> set_weight / paint
  (b) selección por top %       -> from_top_percent
  (c) notación abreviada        -> from_notation
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .hand_types import ALL_HAND_TYPES, expand_to_combos, validate_hand_type
from .notation import parse_notation
from . import strength_ranking


class HandTypeMatrix:
    def __init__(self):
        self._weights: dict[str, float] = {t: 0.0 for t in ALL_HAND_TYPES}

    # ---------- (a) pintar en la grilla ----------
    def set_weight(self, hand_type: str, weight: float) -> None:
        validate_hand_type(hand_type)
        if not (0.0 <= weight <= 1.0):
            raise ValueError(f"Peso fuera de [0,1]: {weight}")
        self._weights[hand_type] = weight

    def get_weight(self, hand_type: str) -> float:
        validate_hand_type(hand_type)
        return self._weights[hand_type]

    def paint(self, weights: dict[str, float]) -> None:
        """Setea varios pesos de una — 'pintar' un bloque de la grilla."""
        for hand_type, weight in weights.items():
            self.set_weight(hand_type, weight)

    # ---------- (b) top % ----------
    @classmethod
    def from_top_percent(cls, pct: float) -> "HandTypeMatrix":
        m = cls()
        for t in strength_ranking.top_percent_types(pct):
            m.set_weight(t, 1.0)
        return m

    # ---------- (c) notación abreviada ----------
    @classmethod
    def from_notation(cls, notation: str) -> "HandTypeMatrix":
        m = cls()
        parsed = parse_notation(notation)
        m.paint(parsed)
        return m

    def apply_notation(self, notation: str) -> None:
        """Suma tipos de la notación a la matriz existente (no la resetea)."""
        parsed = parse_notation(notation)
        for hand_type, weight in parsed.items():
            self._weights[hand_type] = max(self._weights[hand_type], weight)

    # ---------- utilidades ----------
    def nonzero_types(self) -> dict[str, float]:
        return {t: w for t, w in self._weights.items() if w > 0.0}

    def combo_count_weighted(self) -> float:
        """Suma de (peso * cantidad de combos) — tamaño efectivo del rango."""
        from .hand_types import combo_count
        return sum(w * combo_count(t) for t, w in self._weights.items())

    def scale_max_to_one(self) -> "HandTypeMatrix":
        """
        Renormaliza: si el peso máximo actual no es 1.0, reescala todo
        proporcionalmente para que sí lo sea. Ver README para la
        justificación de esta forma de 'renormalización'.
        """
        current_max = max(self._weights.values(), default=0.0)
        m = HandTypeMatrix()
        if current_max > 0:
            for t, w in self._weights.items():
                m._weights[t] = w / current_max
        return m

    def expand_to_weighted_combos(self) -> list[tuple[str, str, float]]:
        """
        Expande TODOS los tipos con peso > 0 a sus combos exactos,
        cada combo hereda el peso de su tipo. Sin remoción de cartas
        todavía — eso se aplica después, en state.py (paso 2 del
        pipeline), porque la remoción depende de qué cartas están
        visibles en cada momento, no es una propiedad de la matriz.
        """
        result = []
        for t, w in self._weights.items():
            if w <= 0:
                continue
            for c1, c2 in expand_to_combos(t):
                result.append((c1, c2, w))
        return result

    def copy(self) -> "HandTypeMatrix":
        m = HandTypeMatrix()
        m._weights = dict(self._weights)
        return m

    def __repr__(self) -> str:
        nz = self.nonzero_types()
        return f"HandTypeMatrix({len(nz)} tipos activos, {self.combo_count_weighted():.0f} combos efectivos)"
