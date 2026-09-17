"""
Integración con el Punto 1. Esta función es el punto de entrada que
la futura interfaz (Punto 8 en adelante) va a llamar cada vez que
CUALQUIER RangeState cambie — no hay caché ni resultado guardado acá
a propósito, así que "cualquier ajuste manual dispara recálculo
inmediato" queda garantizado por diseño: no existe un resultado
viejo que pueda quedar desactualizado, porque no se guarda ninguno.
"""
from __future__ import annotations

from ..equity import calculate_equity, EquityResult
from .state import RangeState


def recompute_equity(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    range_states: list[RangeState],
    num_sims: int = 30_000,
    seed: int | None = None,
) -> EquityResult:
    excluded = set(hero) | set(board) | set(dead)
    opponent_ranges = [rs.to_point1_range(excluded) for rs in range_states]
    return calculate_equity(hero, board, dead, opponent_ranges, num_sims=num_sims, seed=seed)
