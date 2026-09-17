"""
Punto 12 — Métrica basada en el teorema fundamental del póker
(Sklansky, "The Theory of Poker") — Punto 14 pedía codificarlo como
métrica de revisión. CODIFICACIÓN PROPIA, no transcripción: la idea
central del teorema (cada vez que jugás distinto de cómo jugarías si
vieras las cartas del rival, herís tu propio resultado esperado, y
viceversa) se traduce acá en un número concreto y calculable — no es
el texto del libro, es una implementación de la idea.

Se compara la equity que INFORMÓ la decisión real (calculada contra
el rango estimado del rival) contra la equity que se habría calculado
si hero hubiera visto la mano real del rival — solo posible en manos
que llegaron a showdown. La distancia entre ambas es una medida
concreta de qué tan lejos estuvo la creencia de la decisión de la
"información perfecta".
"""
from __future__ import annotations
from dataclasses import dataclass

from ..equity.engine import calculate_equity
from ..equity.ranges import Range


@dataclass
class FundamentalTheoremGap:
    believed_equity_pct: float
    perfect_info_equity_pct: float
    gap: float   # perfecta - creída. positivo = el rango estimado era pesimista, negativo = optimista


def fundamental_theorem_gap(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    believed_equity_pct: float,
    revealed_villain_hand: tuple[str, str],
    num_sims: int = 20_000,
    seed: int | None = None,
) -> FundamentalTheoremGap:
    perfect_info_range = Range.from_combos([(revealed_villain_hand[0], revealed_villain_hand[1], 1.0)])
    result = calculate_equity(hero, board, dead, [perfect_info_range], num_sims=num_sims, seed=seed)
    perfect_equity_pct = result.players[0].equity_pct

    return FundamentalTheoremGap(
        believed_equity_pct=believed_equity_pct,
        perfect_info_equity_pct=perfect_equity_pct,
        gap=perfect_equity_pct - believed_equity_pct,
    )
