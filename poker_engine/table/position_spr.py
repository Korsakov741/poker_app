"""
Punto 5 — Posición y profundidad de stacks (SPR).

DECISIÓN DE DISEÑO: no hay una convención única de nombres de
posición para cada tamaño de mesa posible (6-max nombra distinto que
9-max, y la mesa se va achicando en torneo — ver NOTAS_PENDIENTES.md,
la cantidad de jugadores NUNCA está fija). En vez de hardcodear
tablas de nombres por cada tamaño de mesa, calculo la posición de
forma GENÉRICA y ESCALABLE a cualquier cantidad de jugadores:

1. Botón, ciega chica, ciega grande son siempre los 3 asientos fijos
   relativos al botón.
2. El resto de los asientos ("otros") se reparten en tercios
   (temprano / medio / tardío) según qué tan lejos están de la
   primera posición en actuar (UTG) — así escala solo,
   automáticamente, sin importar si la mesa tiene 4, 6 o 9 jugadores.

Reusa el mismo `Position` enum del placeholder del Punto 4
(`ranges/position_defaults.py`) — no lo duplica.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..ranges.position_defaults import Position


def determine_position(num_players: int, button_seat: int, hero_seat: int) -> Position:
    if num_players < 2:
        raise ValueError("Hace falta al menos 2 jugadores")
    if not (0 <= button_seat < num_players) or not (0 <= hero_seat < num_players):
        raise ValueError("button_seat y hero_seat deben estar en [0, num_players)")

    if hero_seat == button_seat:
        return Position.BUTTON

    if num_players == 2:
        # heads-up: el botón también es la ciega chica, el otro asiento es la ciega grande
        return Position.BIG_BLIND

    sb_seat = (button_seat + 1) % num_players
    bb_seat = (button_seat + 2) % num_players
    if hero_seat == sb_seat:
        return Position.SMALL_BLIND
    if hero_seat == bb_seat:
        return Position.BIG_BLIND

    other_count = num_players - 3
    if other_count <= 0:
        # 3-max: no hay "otros" asientos además de BTN/SB/BB
        return Position.BUTTON  # no debería llegar acá, cubierto arriba

    distance_from_utg = (hero_seat - button_seat - 3) % num_players
    third = other_count / 3.0
    if distance_from_utg < third:
        return Position.EARLY
    elif distance_from_utg < 2 * third:
        return Position.MIDDLE
    else:
        return Position.LATE


@dataclass
class SPRResult:
    effective_stack: float
    pot_size: float
    spr: float
    category: str  # 'push_fold' | 'bajo' | 'medio' | 'profundo'


def compute_spr(stacks: dict[str, float], pot_size: float, active_players: set[str] | None = None) -> SPRResult:
    """
    SPR = stack efectivo / bote. Convención estándar (no inventada
    acá): en un pote multi-way, el stack efectivo es el MÁS CHICO
    entre los jugadores todavía activos en la mano — es el primero
    que puede quedar all-in, y es el que realmente limita cuánto se
    puede jugar postflop.
    """
    relevant = stacks if active_players is None else {p: s for p, s in stacks.items() if p in active_players}
    if not relevant:
        raise ValueError("No hay jugadores activos para calcular el SPR")
    if pot_size <= 0:
        raise ValueError("pot_size debe ser positivo")

    effective_stack = min(relevant.values())
    spr = effective_stack / pot_size

    # umbrales convencionales de la teoría de póker (no exactos, son zonas de referencia)
    if spr < 1:
        category = "push_fold"
    elif spr < 4:
        category = "bajo"
    elif spr < 10:
        category = "medio"
    else:
        category = "profundo"

    return SPRResult(effective_stack=effective_stack, pot_size=pot_size, spr=spr, category=category)
