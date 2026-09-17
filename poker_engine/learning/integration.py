"""
Punto 9 — Puente hacia el Punto 3: versiones "conscientes de EWMA" de
las funciones que ya existían, SIN romper las originales (que siguen
siendo válidas como base cuando no hay estado de aprendizaje
incremental todavía, ej. la primera mano de la sesión).
"""
from __future__ import annotations

from ..history.hud import PlayerHUDStats
from ..profile.scores import BehaviorScores, clamp, AF_SATURATION_POINT
from ..profile.range_adjustment import (
    MIN_OBSERVATIONS, keep_fraction_from_strong_rate,
)
from ..profile.sizing_tells import pot_bucket
from ..ranges.matrix import HandTypeMatrix
from ..ranges.narrowing import NarrowAction, narrow_by_action as generic_narrow_by_action
from .player_learning import PlayerLearningState


def compute_behavior_scores_ewma(
    player: str,
    learning_state: PlayerLearningState | None,
    hud_stats: PlayerHUDStats,
) -> BehaviorScores:
    """
    Igual que compute_behavior_scores del Punto 3, pero usa el VPIP y
    PFR suavizados por EWMA (más sensibles a cambios recientes de
    comportamiento) en vez del acumulado de toda la vida — cuando hay
    estado de aprendizaje disponible. El factor de agresión postflop
    sigue viniendo del acumulado simple del Punto 6 (el resumen
    técnico solo pide EWMA para VPIP y PFR explícitamente, no para AF
    — ver README_punto9.md).
    """
    if learning_state is None or learning_state.vpip_ewma.value is None:
        # sin estado de aprendizaje todavía (primera mano) -> cae al cálculo
        # de toda la vida del Punto 3, no hay nada que suavizar aún
        from ..profile.scores import compute_behavior_scores
        return compute_behavior_scores(hud_stats)

    vpip_ewma_pct = learning_state.vpip_ewma.value * 100
    pfr_ewma_pct = learning_state.pfr_ewma.value * 100

    tightness_score = clamp(100.0 - vpip_ewma_pct)

    sub_scores = []
    if vpip_ewma_pct > 0:
        sub_scores.append(clamp(pfr_ewma_pct / vpip_ewma_pct * 100))
    if hud_stats.aggression_factor is not None:
        sub_scores.append(clamp(100.0 * hud_stats.aggression_factor / (hud_stats.aggression_factor + AF_SATURATION_POINT)))
    aggression_score = sum(sub_scores) / len(sub_scores) if sub_scores else None

    return BehaviorScores(
        player=player,
        tightness_score=tightness_score,
        aggression_score=aggression_score,
        tightness_sample_size=learning_state.vpip_ewma.confidence,
        aggression_sample_size=learning_state.pfr_ewma.confidence,
    )


def real_narrow_by_action_ewma(
    matrix: HandTypeMatrix,
    player: str,
    street: str,
    pot_fraction: float,
    action: NarrowAction,
    learning_state: PlayerLearningState | None,
) -> tuple[HandTypeMatrix, dict]:
    """
    Igual que real_narrow_by_action del Punto 3, pero usa el
    strong_rate suavizado por EWMA del sizing-tell (peso grande,
    reacciona rápido porque el dato es escaso) en vez del promedio
    plano de toda la vida.
    """
    bucket = pot_bucket(pot_fraction)
    tracker = learning_state.sizing_tell(street, bucket) if learning_state else None

    if tracker is None or tracker.confidence < MIN_OBSERVATIONS:
        narrowed = generic_narrow_by_action(matrix, action)
        n_obs = tracker.confidence if tracker else 0
        info = {
            "source": "generic_placeholder",
            "reason": f"solo {n_obs} observaciones EWMA en el balde {bucket} de {street} (mínimo {MIN_OBSERVATIONS})",
            "n_observations": n_obs,
        }
        return narrowed, info

    keep_fraction = keep_fraction_from_strong_rate(tracker.value)
    narrowed = generic_narrow_by_action(matrix, action, keep_fraction=keep_fraction)
    info = {
        "source": "real_sizing_tell_ewma",
        "bucket": bucket,
        "strong_rate_ewma": round(tracker.value, 3),
        "n_observations": tracker.confidence,
        "keep_fraction_usado": round(keep_fraction, 3),
        "historial_completo": [round(v, 3) for v in tracker.history],
    }
    return narrowed, info
