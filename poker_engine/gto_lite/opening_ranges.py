"""
Punto 4 — Submódulo A (casi estático): tablas de rango de apertura
por posición, con variantes por cantidad de jugadores y profundidad
de stack, más ajustes por acción previa (vs. open, vs. 3-bet).

REEMPLAZA el placeholder del Punto 2 (`ranges/position_defaults.py`)
— ese placeholder usaba un % fijo por posición sin importar mesa ni
stack. Este módulo es la versión "real" (documentada como heurística
propia, no un solver) que Point 2/11 deberían empezar a usar.

Los % base por posición son los MISMOS que ya tenía el placeholder
del Punto 2 (10/15/25/40/30) — no los reinvento, los "oficializo"
como referencia deep-stack 9-max, y les agrego las dos dimensiones
que faltaban: tamaño de mesa y profundidad de stack.

FÓRMULAS PROPIAS (no de ningún libro), documentadas explícitamente
como heurísticas razonables, no derivaciones rigurosas de un solver:
  pct_final = pct_base_9max_deep × factor_mesa × factor_profundidad
"""
from __future__ import annotations

from ..ranges.matrix import HandTypeMatrix
from ..ranges.position_defaults import Position
from ..knowledge.population_defaults import POPULATION_DEFAULT_STATS

BASE_OPEN_PCT_9MAX_DEEP: dict[Position, float | None] = {
    Position.EARLY: 10.0,
    Position.MIDDLE: 15.0,
    Position.LATE: 25.0,
    Position.BUTTON: 40.0,
    Position.SMALL_BLIND: 30.0,
    Position.BIG_BLIND: None,  # la BB no "abre" — actúa último preflop, su decisión es
                                 # defender/completar contra lo que hicieron los demás,
                                 # no un % de apertura propiamente dicho
}

_STACK_DEPTH_FACTOR = {
    "push_fold": 3.0,   # rangos de push clásicamente MUCHO más anchos (fold equity domina)
    "bajo": 1.3,
    "medio": 1.0,          # referencia
    "profundo": 0.85,       # deep: un poco más selectivo, pesa más la jugabilidad postflop
}


def table_size_factor(num_players: int) -> float:
    """
    Cada jugador de MENOS que la referencia (9-max) ensancha el rango
    ~8% relativo — heurística propia simple: menos jugadores detrás
    tuyo = menos riesgo de toparte con una mano mejor, así que se
    puede abrir más ancho.
    """
    if num_players < 2:
        raise ValueError("num_players debe ser al menos 2")
    baseline = 9
    return 1.0 + max(0, baseline - num_players) * 0.08


def stack_depth_factor(spr_category: str) -> float:
    if spr_category not in _STACK_DEPTH_FACTOR:
        raise ValueError(f"spr_category inválida: {spr_category!r}")
    return _STACK_DEPTH_FACTOR[spr_category]


def opening_percent(position: Position, num_players: int, spr_category: str) -> float:
    base = BASE_OPEN_PCT_9MAX_DEEP.get(position)
    if base is None:
        raise ValueError(
            f"{position.value} no tiene un % de apertura propiamente dicho "
            f"(ver docstring del módulo — la BB defiende, no abre)"
        )
    pct = base * table_size_factor(num_players) * stack_depth_factor(spr_category)
    return min(pct, 100.0)


def opening_range(position: Position, num_players: int, spr_category: str) -> HandTypeMatrix:
    pct = opening_percent(position, num_players, spr_category)
    return HandTypeMatrix.from_top_percent(pct)


def vs_open_3bet_range(position: Position, num_players: int, spr_category: str) -> HandTypeMatrix:
    """
    Rango de 3-bet al enfrentar un open. Anclado en el 3-bet%
    poblacional del Punto 14 (~7%) como referencia base, en vez de
    una constante inventada sin respaldo — con los mismos factores de
    mesa/profundidad que la apertura.
    """
    base_pct = POPULATION_DEFAULT_STATS["threebet_pct"]
    pct = base_pct * table_size_factor(num_players) * stack_depth_factor(spr_category)
    return HandTypeMatrix.from_top_percent(min(pct, 100.0))


_VS_3BET_CONTINUE_RETENTION = 0.35  # heurística propia: retener ~35% del rango de apertura original al continuar vs. un 3-bet


def vs_3bet_continue_range(position: Position, num_players: int, spr_category: str) -> HandTypeMatrix:
    """Rango de continuar (pagar/4-bet) al enfrentar un 3-bet — más angosto todavía que el de 3-bet."""
    base_pct = opening_percent(position, num_players, spr_category)
    pct = base_pct * _VS_3BET_CONTINUE_RETENTION
    return HandTypeMatrix.from_top_percent(min(pct, 100.0))
