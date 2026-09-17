"""
Punto 3 — Función de ajuste de rango real: entra (jugador, calle,
tamaño de apuesta) → sale un sesgo sobre el rango de ese jugador.
Reemplaza DIRECTAMENTE la heurística genérica placeholder del Punto 2
(narrowing.py) — mismo tipo de entrada/salida (HandTypeMatrix ->
HandTypeMatrix), así que el resto del pipeline del Punto 2
(state.py) no se entera del cambio.

Regla del propio resumen técnico: no usar un tell hasta tener un
mínimo de observaciones de showdown en ese balde específico. Uso 7
como umbral (mitad del rango 5-10 que sugiere el resumen) — ajustable.

LIMITACIÓN A FLAGGEAR: esta función SOLO puede angostar el rango
hacia arriba (quedarse con el % superior por fuerza), igual que el
placeholder genérico que reemplaza — no puede representar "este
jugador tiende a farolear en este balde" como un sesgo hacia manos
DÉBILES específicas, porque la infraestructura actual del Punto 2
(HandTypeMatrix + narrow_by_action) solo sabe expresar "top X% por
fuerza". Lo que SÍ mejora respecto del placeholder: el X% ya no es
una constante genérica (33/50/70%) sino que sale de datos reales de
ESE jugador en ESE balde específico. Representar un sesgo hacia
manos débiles específicas (rango polarizado) es un problema de
representación más profundo — tu propio resumen técnico lo marca
como extensión PENDIENTE del Submódulo A del Punto 4 (rangos
polarizados vs. mergeados), no algo para resolver silenciosamente acá.
"""
from __future__ import annotations

from ..ranges.matrix import HandTypeMatrix
from ..ranges.narrowing import NarrowAction, narrow_by_action as generic_narrow_by_action
from .sizing_tells import SizingTellsTable, pot_bucket

MIN_OBSERVATIONS = 7

# tasa de manos fuertes -> keep_fraction. Mapeo lineal simple y
# documentado: 100% de manos fuertes en el historial -> angostar
# mucho (quedarse con el 25% superior); 0% fuertes (siempre farol/
# valor fino en ese balde, según lo que hay registrado) -> angostar
# poco (80%), reflejando que este tamaño de apuesta NO es un tell de
# fuerza para este jugador — no puede, con la infraestructura actual,
# representar directamente "sesgo hacia manos débiles" (ver docstring).
_KEEP_FRACTION_AT_STRONG_1 = 0.25
_KEEP_FRACTION_AT_STRONG_0 = 0.80


def keep_fraction_from_strong_rate(strong_rate: float) -> float:
    return _KEEP_FRACTION_AT_STRONG_0 + strong_rate * (
        _KEEP_FRACTION_AT_STRONG_1 - _KEEP_FRACTION_AT_STRONG_0
    )


def real_narrow_by_action(
    matrix: HandTypeMatrix,
    player: str,
    street: str,
    pot_fraction: float,
    action: NarrowAction,
    sizing_tells: SizingTellsTable,
) -> tuple[HandTypeMatrix, dict]:
    """
    Devuelve (matriz_angostada, info_de_diagnóstico). info incluye
    si se usó un tell real o el fallback genérico, y cuántas
    observaciones respaldan la decisión — útil para debugging y para
    que el Punto 8 pueda mostrar "de dónde salió este número".
    """
    bucket = pot_bucket(pot_fraction)
    strong_rate, n_obs = sizing_tells.strong_rate(player, street, bucket)

    if strong_rate is None or n_obs < MIN_OBSERVATIONS:
        # sin evidencia suficiente -> fallback explícito al placeholder genérico del Punto 2
        narrowed = generic_narrow_by_action(matrix, action)
        info = {
            "source": "generic_placeholder",
            "reason": f"solo {n_obs} observaciones en el balde {bucket} de {street} (mínimo {MIN_OBSERVATIONS})",
            "n_observations": n_obs,
        }
        return narrowed, info

    keep_fraction = keep_fraction_from_strong_rate(strong_rate)
    narrowed = generic_narrow_by_action(matrix, action, keep_fraction=keep_fraction)
    info = {
        "source": "real_sizing_tell",
        "bucket": bucket,
        "strong_rate_observado": round(strong_rate, 3),
        "n_observations": n_obs,
        "keep_fraction_usado": round(keep_fraction, 3),
    }
    return narrowed, info
