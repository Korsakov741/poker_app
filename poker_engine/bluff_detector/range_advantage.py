"""
Punto 16 — Señal (B): ventaja de rango en el board. Compara MI
rango representado contra el rango del rival, en fuerza ACTUAL sobre
este board puntual (no equity a futuro — es la misma filosofía del
Punto 15, más barato computacionalmente que simular cartas por
venir, y es lo que realmente importa para "¿el board favorece a mi
rango o al suyo?").

DECISIÓN DE DISEÑO A FLAGGEAR: enumeración COMPLETA de todos los
pares (mi_combo, combo_rival) puede ser cara con rangos anchos — uso
el mismo patrón de techo + aviso que ya usé en equity/exact.py, en
vez de colgar el cálculo.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..equity.cards import to_treys_many
from ..equity import evaluator
from ..ranges.matrix import HandTypeMatrix
from ..equity.ranges import Range

MAX_PAIRS = 500_000


class RangeAdvantageTooExpensiveError(Exception):
    pass


@dataclass
class RangeAdvantageResult:
    my_range_win_rate: float   # 0.5 = parejo, >0.5 = mi rango favorecido en este board
    n_pairs_evaluated: int


def range_advantage(
    my_range: HandTypeMatrix,
    board: list[str],
    dead: list[str],
    villain_range: Range,
) -> RangeAdvantageResult:
    if len(board) not in (3, 4, 5):
        raise ValueError("La ventaja de rango necesita un board ya repartido")

    excluded = set(board) | set(dead)
    my_combos = [
        (c1, c2, w) for c1, c2, w in my_range.expand_to_weighted_combos()
        if c1 not in excluded and c2 not in excluded and w > 0
    ]
    villain_combos = villain_range.valid_combos(excluded)

    estimated_pairs = len(my_combos) * len(villain_combos)
    if estimated_pairs > MAX_PAIRS:
        raise RangeAdvantageTooExpensiveError(
            f"{estimated_pairs:,} pares supera el techo ({MAX_PAIRS:,}) — angostar los rangos antes de llamar"
        )

    board_t = to_treys_many(board)
    total_weight = 0.0
    my_win_weight = 0.0

    for mc1, mc2, mw in my_combos:
        my_hand_t = to_treys_many((mc1, mc2))
        my_score = evaluator.score(board_t, my_hand_t)
        for vc in villain_combos:
            if vc.card1 in (mc1, mc2) or vc.card2 in (mc1, mc2):
                continue  # choque de cartas, combinación inválida
            v_hand_t = to_treys_many(vc.cards())
            v_score = evaluator.score(board_t, v_hand_t)
            pair_weight = mw * vc.weight
            total_weight += pair_weight
            if my_score < v_score:
                my_win_weight += pair_weight
            elif my_score == v_score:
                my_win_weight += pair_weight * 0.5

    if total_weight == 0:
        raise RuntimeError("No quedó ningún par válido entre los dos rangos dado el board/dead actuales")

    return RangeAdvantageResult(
        my_range_win_rate=my_win_weight / total_weight,
        n_pairs_evaluated=len(my_combos) * len(villain_combos),
    )
