"""
Textura de board — módulo separado, depende SOLO de las cartas del
board (nada de rangos ni evaluación de manos), tal como pide el
resumen técnico del Punto 15: "reutilizable por el punto 16 a futuro".

ACLARACIÓN A FLAGGEAR: "seco" y "mojado" no tienen una definición
matemática única y universal en teoría de póker — es un concepto
cualitativo incluso en la literatura de referencia. Lo que sigue es
una heurística explícita y documentada (no una fórmula estándar de
ningún libro), basada en dos señales objetivas: qué tan concentrados
están los palos (proyecto de color) y qué tan conectados están los
rangos (proyecto de escalera). Si en algún momento el criterio no te
convence, se ajusta acá sin tocar nada de los puntos 1, 2 o 15.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass

from ..equity.cards import RANKS


def _rank_value(rank: str, ace_high: bool = True) -> int:
    """2=2, ..., A=14 (ace_high) o A=1 (para detectar escalera rueda A-5)."""
    if rank == "A" and not ace_high:
        return 1
    return RANKS.index(rank) + 2


def _straight_connectivity(ranks: list[str]) -> int:
    """
    Máxima cantidad de rangos del board que caben dentro de ALGUNA
    ventana de 5 rangos consecutivos (incluye la posibilidad de
    escalera rueda, As como 1). Cuanto más alto, más conectado el
    board para proyectos de escalera.
    """
    values = set()
    for r in ranks:
        values.add(_rank_value(r, ace_high=True))
        if r == "A":
            values.add(1)  # rueda

    best = 0
    for low in range(1, 11):  # ventanas: 1-5, 2-6, ..., 10-14
        window = set(range(low, low + 5))
        best = max(best, len(values & window))
    return best


@dataclass
class BoardTexture:
    board: list[str]
    paired: bool                 # algún rango aparece 2+ veces
    trips_or_more: bool           # algún rango aparece 3+ veces
    suit_counts: dict[str, int]
    max_suit_count: int
    suit_texture: str              # 'rainbow' | 'two_tone' | 'wet_flush' | 'monotone'
    straight_connectivity: int     # 0..len(board)
    straight_texture: str           # 'desconectado' | 'algo_conectado' | 'muy_conectado'
    overall: str                     # 'seco' | 'mojado'


def analyze_texture(board: list[str]) -> BoardTexture:
    if len(board) not in (3, 4, 5):
        raise ValueError("La textura de board solo aplica a flop/turn/río (3, 4 o 5 cartas)")

    ranks = [c[0].upper() for c in board]
    suits = [c[1].lower() for c in board]

    rank_counts = Counter(ranks)
    paired = any(c >= 2 for c in rank_counts.values())
    trips_or_more = any(c >= 3 for c in rank_counts.values())

    suit_counts = dict(Counter(suits))
    max_suit_count = max(suit_counts.values())
    if max_suit_count == len(board) and len(board) >= 3:
        suit_texture = "monotone"
    elif max_suit_count >= 3:
        suit_texture = "wet_flush"       # color ya hecho o muy cerca (con solo 1 carta más)
    elif max_suit_count == 2:
        suit_texture = "two_tone"         # proyecto de color a 2 cartas
    else:
        suit_texture = "rainbow"

    connectivity = _straight_connectivity(ranks)
    connectivity_ratio = connectivity / len(board)
    if connectivity_ratio >= 0.8:
        straight_texture = "muy_conectado"
    elif connectivity_ratio >= 0.6:
        straight_texture = "algo_conectado"
    else:
        straight_texture = "desconectado"

    is_wet = (
        suit_texture in ("wet_flush", "monotone", "two_tone")
        or straight_texture in ("muy_conectado", "algo_conectado")
        or paired
    )
    overall = "mojado" if is_wet else "seco"

    return BoardTexture(
        board=board,
        paired=paired,
        trips_or_more=trips_or_more,
        suit_counts=suit_counts,
        max_suit_count=max_suit_count,
        suit_texture=suit_texture,
        straight_connectivity=connectivity,
        straight_texture=straight_texture,
        overall=overall,
    )
