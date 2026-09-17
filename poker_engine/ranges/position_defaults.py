"""
*** PLACEHOLDER EXPLÍCITO DEL PUNTO 4 — NO ES EL PUNTO 4 REAL ***

El resumen técnico del Punto 2 dice que el rango preflop inicial por
posición es "input externo, del punto 4". El Punto 4 todavía no está
construido (depende del Punto 14 para los valores concretos de las
tablas de apertura). Mientras tanto, esta función da un placeholder
GENÉRICO y DELIBERADAMENTE SIMPLE — un % de manos por posición según
sentido común de teoría de póker estándar (más ajustado en posición
temprana, más suelto en botón), sin considerar profundidad de stack,
cantidad de jugadores, ni acción previa (eso SÍ es trabajo real del
Punto 4 con su Submódulo A).

Esta función tiene UN SOLO trabajo: no bloquear el desarrollo del
resto del Punto 2 mientras el Punto 4 no exista. El día que
construyamos el Punto 4, esta función se reemplaza (o se borra
directamente) y el resto del Punto 2 no se entera — porque el
pipeline de 4 pasos en state.py llama a esto a través de una función
inyectable, no hardcodeada.
"""
from enum import Enum

from .matrix import HandTypeMatrix


class Position(str, Enum):
    EARLY = "early"      # UTG, UTG+1
    MIDDLE = "middle"     # MP, MP+1, HJ
    LATE = "late"          # CO
    BUTTON = "button"
    SMALL_BLIND = "sb"
    BIG_BLIND = "bb"


# % de combos (no de tipos) que abre cada posición — genérico, sin
# fuente de un libro puntual, solo sentido común estándar de rangos
# de apertura preflop. EL PUNTO 4 REEMPLAZA ESTO POR TABLAS REALES.
_GENERIC_OPEN_PCT = {
    Position.EARLY: 10.0,
    Position.MIDDLE: 15.0,
    Position.LATE: 25.0,
    Position.BUTTON: 40.0,
    Position.SMALL_BLIND: 30.0,
    Position.BIG_BLIND: 100.0,  # el BB no "abre", este valor no se usa igual (ver nota abajo)
}


def placeholder_opening_range(position: Position) -> HandTypeMatrix:
    """
    Rango de apertura genérico por posición. PLACEHOLDER — ver
    docstring del módulo. La Big Blind no tiene un "rango de
    apertura" real (actúa último preflop sin nadie más que haya
    limpeado) — devolver 100% acá es una simplificación grosera,
    marcada a propósito para que no se use tal cual en una decisión
    real de BB; el Punto 4 tiene que resolver esto con lógica propia
    (rango de defensa vs. distintos tamaños de subida, no un solo %).
    """
    pct = _GENERIC_OPEN_PCT[position]
    return HandTypeMatrix.from_top_percent(pct)
