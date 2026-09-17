"""
Punto 3 — Dos puntajes continuos 0-100, derivados de las stats
crudas del Punto 6 (esta capa NO duplica ningún cálculo, solo
interpreta lo que el Punto 6 ya calculó).

Las etiquetas tradicionales ("TAG", "LAG", "nit", "calling station")
son ZONAS de este mapa 2D, no categorías de entrada — a propósito no
se pide clasificar al jugador en una caja, se leen los dos ejes.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..history.hud import PlayerHUDStats

# constante de saturación para el factor de agresión: a qué valor de
# AF se considera "a mitad de camino" en la escala 0-100. AF=2.0 es
# un punto de referencia estándar razonable (ligeramente agresivo).
AF_SATURATION_POINT = 2.0


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class BehaviorScores:
    player: str
    tightness_score: float | None   # 0 = extremadamente loose, 100 = extremadamente tight
    aggression_score: float | None   # 0 = extremadamente pasivo, 100 = extremadamente agresivo
    tightness_sample_size: int
    aggression_sample_size: int


def compute_behavior_scores(stats: PlayerHUDStats) -> BehaviorScores:
    # ---- eje tight <-> loose ----
    # VPIP YA ES, por definición, la medida directa de con qué
    # frecuencia el jugador entra a una mano — es literalmente el eje
    # loose. tightness_score es su complemento.
    if stats.vpip_pct is None:
        tightness_score = None
    else:
        tightness_score = clamp(100.0 - stats.vpip_pct)

    # ---- eje pasivo <-> agresivo ----
    # combina DOS señales, cuando hay datos de ambas: qué tan seguido
    # sube en vez de pagar preflop (PFR/VPIP), y el factor de
    # agresión postflop (AF), cada una normalizada a 0-100 por
    # separado y promediada. Si falta una, se usa solo la otra.
    sub_scores = []

    if stats.vpip_pct and stats.vpip_pct > 0 and stats.pfr_pct is not None:
        pfr_vpip_ratio = clamp(stats.pfr_pct / stats.vpip_pct * 100)  # ya 0-100
        sub_scores.append(pfr_vpip_ratio)

    if stats.aggression_factor is not None:
        af_score = clamp(100.0 * stats.aggression_factor / (stats.aggression_factor + AF_SATURATION_POINT))
        sub_scores.append(af_score)

    aggression_score = sum(sub_scores) / len(sub_scores) if sub_scores else None

    return BehaviorScores(
        player=stats.player,
        tightness_score=tightness_score,
        aggression_score=aggression_score,
        tightness_sample_size=stats.hands_dealt,
        aggression_sample_size=stats.postflop_actions_sampled,
    )
