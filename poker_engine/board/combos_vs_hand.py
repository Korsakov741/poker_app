"""
Punto 15 — Combos que vencen mi mano según el board.

Evaluación de fuerza ACTUAL (no equity a futuro): compara mi mano ya
hecha contra cada combo del rango del rival en el board actual, sin
simular cartas por venir. Por eso es exacto en cualquier calle
post-flop, sin excepción — a diferencia del Punto 1, acá no hace
falta Monte Carlo en ninguna calle.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..equity.cards import to_treys_many
from ..equity import evaluator
from ..equity.ranges import Range
from .texture import BoardTexture, analyze_texture


@dataclass
class ComboVsHandResult:
    # los DOS números que pide el resumen técnico, siempre juntos:
    raw_count_beating_me: int      # ej. 9
    raw_count_total: int             # ej. 32   ("9 de 32 combos posibles")
    weighted_pct_beating_me: float    # % ponderado por peso del rango (más preciso)

    raw_count_tying_me: int
    weighted_pct_tying_me: float

    raw_count_losing_to_me: int
    weighted_pct_losing_to_me: float

    board_texture: BoardTexture

    def summary(self) -> str:
        return (
            f"{self.raw_count_beating_me} de {self.raw_count_total} combos posibles "
            f"me ganan ahora mismo ({self.weighted_pct_beating_me:.1f}% ponderado por peso)"
        )


def combos_beating_hero(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    rival_range: Range,
) -> ComboVsHandResult:
    if len(board) not in (3, 4, 5):
        raise ValueError(
            "El Punto 15 evalúa fuerza actual contra un board ya repartido "
            "(flop/turn/río) — no aplica preflop, donde no hay board todavía."
        )

    excluded = set(hero) | set(board) | set(dead)
    combos = rival_range.valid_combos(excluded)
    if not combos:
        raise RuntimeError(
            "El rango del rival no tiene ningún combo válido dado el "
            "board/hero/dead cards actuales."
        )

    board_t = to_treys_many(board)
    hero_t = to_treys_many(hero)
    hero_score = evaluator.score(board_t, hero_t)

    raw_win = raw_tie = raw_lose = 0
    w_win = w_tie = w_lose = 0.0
    total_weight = 0.0

    for combo in combos:
        combo_t = to_treys_many(combo.cards())
        combo_score = evaluator.score(board_t, combo_t)
        total_weight += combo.weight
        # convención treys: score más bajo = mano más fuerte
        if combo_score < hero_score:
            raw_win += 1
            w_win += combo.weight
        elif combo_score > hero_score:
            raw_lose += 1
            w_lose += combo.weight
        else:
            raw_tie += 1
            w_tie += combo.weight

    total_raw = raw_win + raw_tie + raw_lose

    return ComboVsHandResult(
        raw_count_beating_me=raw_win,
        raw_count_total=total_raw,
        weighted_pct_beating_me=(w_win / total_weight * 100) if total_weight else 0.0,
        raw_count_tying_me=raw_tie,
        weighted_pct_tying_me=(w_tie / total_weight * 100) if total_weight else 0.0,
        raw_count_losing_to_me=raw_lose,
        weighted_pct_losing_to_me=(w_lose / total_weight * 100) if total_weight else 0.0,
        board_texture=analyze_texture(board),
    )
