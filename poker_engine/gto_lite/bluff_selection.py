"""
Punto 4 — Función reutilizable de selección de manos-farol: entra
(mi rango, board, rango del rival) -> sale combos candidatos
ordenados por bloqueadores + falta de showdown value. La reusa
directamente el Punto 16 (detector de farol) sin duplicar lógica.

DECISIÓN DE DISEÑO A FLAGGEAR: "showdown value" se normaliza usando
el rango TEÓRICO completo de scores de treys (1=mejor mano posible,
7462=peor), no el rango de manos REALMENTE alcanzables en este board
específico. Es una simplificación razonable — normalizar contra el
rango real alcanzable en cada board exigiría enumerar todo el board
primero, mucho más caro computacionalmente por poco beneficio
práctico para un ranking relativo dentro del propio rango de hero.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..equity.cards import to_treys_many
from ..equity import evaluator
from ..ranges.matrix import HandTypeMatrix
from ..ranges.hand_types import hand_type_from_combo
from ..equity.ranges import Range

_MIN_SCORE = 1       # mejor mano posible en treys
_MAX_SCORE = 7462     # peor mano posible en treys


@dataclass
class BluffCandidate:
    hand_type: str
    combo: tuple[str, str]
    blocker_fraction: float    # 0-1, cuánto del rango ponderado del rival bloquea este combo
    showdown_value: float        # 0=la peor mano posible (mejor candidato a farol), 1=la mejor mano posible
    combined_score: float          # mayor = mejor candidato a farol (más bloqueo, menos showdown value)


def select_bluff_candidates(
    hero_range: HandTypeMatrix,
    board: list[str],
    dead: list[str],
    villain_range: Range,
    top_n: int | None = 10,
) -> list[BluffCandidate]:
    if len(board) not in (3, 4, 5):
        raise ValueError("La selección de farol necesita un board ya repartido (flop/turn/río)")

    excluded = set(board) | set(dead)
    hero_combos = [
        (c1, c2, w) for c1, c2, w in hero_range.expand_to_weighted_combos()
        if c1 not in excluded and c2 not in excluded and w > 0
    ]
    if not hero_combos:
        return []

    villain_combos = villain_range.valid_combos(excluded)
    villain_total_weight = sum(c.weight for c in villain_combos)

    board_t = to_treys_many(board)

    results = []
    for c1, c2, _w in hero_combos:
        blocked_weight = sum(
            vc.weight for vc in villain_combos if c1 in vc.cards() or c2 in vc.cards()
        )
        blocker_fraction = (blocked_weight / villain_total_weight) if villain_total_weight > 0 else 0.0

        hand_t = to_treys_many((c1, c2))
        score = evaluator.score(board_t, hand_t)
        showdown_value = 1.0 - (score - _MIN_SCORE) / (_MAX_SCORE - _MIN_SCORE)

        combined = blocker_fraction - showdown_value
        results.append(BluffCandidate(
            hand_type=hand_type_from_combo(c1, c2),
            combo=(c1, c2),
            blocker_fraction=round(blocker_fraction, 4),
            showdown_value=round(showdown_value, 4),
            combined_score=round(combined, 4),
        ))

    results.sort(key=lambda r: -r.combined_score)
    return results[:top_n] if top_n else results
