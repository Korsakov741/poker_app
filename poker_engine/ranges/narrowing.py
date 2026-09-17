"""
*** PLACEHOLDER EXPLÍCITO DEL PUNTO 3 — NO ES EL PUNTO 3 REAL ***

Paso 3 del pipeline del Punto 2: angostar el rango de un rival según
su acción (sube/paga). El resumen técnico autoriza explícitamente
usar acá "heurísticas genéricas por defecto (ej. una subida reduce
al tercio superior de manos), diseñadas como módulo separado y
reemplazable para cuando se construya el punto 3" — literal.

LIMITACIÓN A FLAGGEAR (no está en el resumen, la encontré yo
armando esto): el "ranking de fuerza" que se usa acá para ordenar
qué manos son "el tercio superior" es el ranking preflop (equity vs.
mano al azar, calculado en el Punto 2 base). Post-flop, ese ranking
ya no es exacto — una mano como "76s" puede ser basura preflop pero
la mejor mano posible en un board 5-6-7. Usarlo igual post-flop como
proxy genérico es una simplificación consciente: no sabe leer el
board, solo angosta el tipo de mano en términos generales de "qué tan
premium se ve". El Punto 3 real, cuando exista, va a angostar según
comportamiento observado del rival (sizing-tells reales), no según
esta tabla estática — ahí es donde se vuelve preciso post-flop.

Cuando el Punto 3 esté construido, esta función se reemplaza por la
función de ajuste de rango real del Punto 3 (mismo input/output:
matriz -> matriz), sin tocar el resto del pipeline.
"""
from enum import Enum

from .matrix import HandTypeMatrix
from .hand_types import combo_count
from . import strength_ranking
from ..knowledge.population_defaults import population_informed_keep_fractions


class NarrowAction(str, Enum):
    RAISE = "raise"       # sube o resube — señal fuerte, heurística: top 33%
    BET = "bet"             # apuesta de iniciativa (ej. c-bet) — señal media, top 50%
    CALL = "call"           # paga — saca el fondo débil, top 70%


# ACTUALIZADO por el Punto 14: estas constantes ya NO son arbitrarias
# — se derivan del prior poblacional (ver knowledge/population_defaults.py).
# Con los valores de referencia actuales dan prácticamente lo mismo
# que las constantes originales (0.33/0.5/0.7), pero ahora están
# atadas a un número documentado en vez de salir de la nada.
_DEFAULT_KEEP_FRACTION = {
    NarrowAction.RAISE: population_informed_keep_fractions()["raise"],
    NarrowAction.BET: population_informed_keep_fractions()["bet"],
    NarrowAction.CALL: population_informed_keep_fractions()["call"],
}


def narrow_by_action(
    matrix: HandTypeMatrix,
    action: NarrowAction,
    keep_fraction: float | None = None,
) -> HandTypeMatrix:
    """
    Devuelve una NUEVA matriz (no muta la original) con solo el
    `keep_fraction` superior de la masa de combos actual, ordenado
    por el ranking de fuerza. Corte duro (no hay suavizado en el
    borde) — simplificación explícita, ver docstring del módulo.
    """
    if keep_fraction is None:
        keep_fraction = _DEFAULT_KEEP_FRACTION[action]
    if not (0.0 < keep_fraction <= 1.0):
        raise ValueError("keep_fraction debe estar en (0, 1]")

    current = matrix.nonzero_types()
    if not current:
        return matrix.copy()  # rango ya vacío, nada que angostar

    ranked = [t for t in strength_ranking.ranked_types() if t in current]
    total_combos = sum(current[t] * combo_count(t) for t in ranked)
    target = keep_fraction * total_combos

    result = HandTypeMatrix()
    acc = 0.0
    for t in ranked:
        if acc >= target:
            break
        result.set_weight(t, current[t])
        acc += current[t] * combo_count(t)
    return result
