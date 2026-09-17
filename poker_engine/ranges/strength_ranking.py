"""
Carga el ranking de fuerza precomputado (ver compute_strength_ranking.py)
y expone la función que necesita el método "top %" de entrada manual
del Punto 2.
"""
import json
from functools import lru_cache
from pathlib import Path

from .hand_types import ALL_HAND_TYPES

_DATA_PATH = Path(__file__).parent / "data" / "strength_ranking.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, float]:
    if not _DATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró {_DATA_PATH}. Correr primero: "
            f"python3 -m poker_engine.ranges.compute_strength_ranking"
        )
    with open(_DATA_PATH) as f:
        return json.load(f)


def equity_vs_random(hand_type: str) -> float:
    """Equity heads-up preflop de este tipo contra un rango 100% al azar."""
    data = _load()
    if hand_type not in data:
        raise ValueError(f"Tipo de mano desconocido: {hand_type!r}")
    return data[hand_type]


@lru_cache(maxsize=1)
def ranked_types() -> list[str]:
    """Los 169 tipos ordenados de más fuerte a más débil."""
    data = _load()
    return sorted(ALL_HAND_TYPES, key=lambda t: -data[t])


def top_percent_types(pct: float) -> list[str]:
    """
    Los tipos de mano que forman el top `pct`% del rango preflop,
    medido en % de COMBOS (no % de tipos) — un 'top 15%' real de
    póker cuenta combos, no casilleros de la grilla, porque AA (6
    combos) no debería pesar lo mismo que AKo (12 combos) en el
    porcentaje total.
    """
    from .hand_types import combo_count

    if not (0 < pct <= 100):
        raise ValueError("pct debe estar entre 0 y 100")
    target_combos = (pct / 100.0) * 1326  # C(52,2) combos totales posibles
    ordered = ranked_types()
    selected = []
    acc = 0
    for t in ordered:
        if acc >= target_combos:
            break
        selected.append(t)
        acc += combo_count(t)
    return selected
