"""
Punto 8 — Capa de ajuste, en el ORDEN DE PRIORIDAD FIJO que exige el
resumen técnico:
  1) línea GTO/Explotador ya mezclada (Punto 11)
  2) amortiguador de ICM (Punto 17)
  3) chequeo de coherencia con SPR (Punto 5)
Las restricciones estructurales (dinero real, SPR) tienen la ÚLTIMA
palabra sobre ajustes finos de lectura de rival — por eso van al
final, después de los ajustes "blandos" de lectura.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .heuristic_values import ActionValueEstimate
from ..decision.mixing import ExploitVsGTODecision
from ..icm.penalty import ICMPenaltyResult
from ..table.position_spr import SPRResult


@dataclass
class AdjustmentNote:
    layer: str      # 'gto_exploit' | 'icm' | 'spr_coherence'
    message: str


def apply_gto_exploit_layer(
    estimate: ActionValueEstimate,
    gto_exploit: ExploitVsGTODecision | None,
) -> tuple[ActionValueEstimate, AdjustmentNote | None]:
    """
    Solo aplica a los candidatos que dependen de una lectura del
    rival (bet_value, bet_bluff) — call y fold no se tocan acá, ya
    están anclados en equity/pot-odds real, no en una lectura de
    rango explotable.
    """
    if gto_exploit is None or estimate.action not in ("bet_value", "bet_bluff"):
        return estimate, None

    w = gto_exploit.weight_exploit_final
    # a menor peso explotador (más confianza en GTO puro), se amortigua
    # el valor heurístico hacia 0 — no se anula del todo, se atenúa
    adjusted_value = estimate.heuristic_value * (0.5 + 0.5 * w)
    note = AdjustmentNote(
        layer="gto_exploit",
        message=f"Atenuado por peso explotador {w:.2f} (Punto 11): {estimate.heuristic_value:.3f} -> {adjusted_value:.3f}",
    )
    return ActionValueEstimate(action=estimate.action, heuristic_value=adjusted_value, reasoning=estimate.reasoning), note


def apply_icm_layer(
    estimate: ActionValueEstimate,
    icm_penalty: ICMPenaltyResult | None,
) -> tuple[ActionValueEstimate, AdjustmentNote | None]:
    """
    Solo aplica a acciones que arriesgan fichas (call, bet_value,
    bet_bluff) — fold nunca se penaliza por ICM, retirarse no arriesga nada.
    """
    if icm_penalty is None or not icm_penalty.applies or estimate.action == "fold":
        return estimate, None

    ev_ref = max(abs(icm_penalty.ev_before_dollars or 0.0), 1e-9)
    penalty_ratio = (icm_penalty.icm_penalty_dollars or 0.0) / ev_ref
    adjusted_value = estimate.heuristic_value - max(0.0, penalty_ratio)
    note = AdjustmentNote(
        layer="icm",
        message=f"Penalizado por presión de ICM (Punto 17): -{max(0.0, penalty_ratio):.3f}",
    )
    return ActionValueEstimate(action=estimate.action, heuristic_value=adjusted_value, reasoning=estimate.reasoning), note


def apply_spr_coherence_layer(
    estimate: ActionValueEstimate,
    spr: SPRResult | None,
    proposed_bet_fraction_of_stack: float | None,
) -> tuple[ActionValueEstimate, AdjustmentNote | None]:
    """
    Chequeo ESTRUCTURAL, no de lectura — tiene la última palabra. En
    territorio push/fold, cualquier apuesta que no se acerque al
    stack efectivo (all-in) es estructuralmente incoherente: no se
    anula el candidato (sigue siendo información), pero se marca
    explícito con una advertencia, no se oculta en silencio.
    """
    if spr is None or estimate.action not in ("bet_value", "bet_bluff"):
        return estimate, None
    if spr.category != "push_fold":
        return estimate, None
    if proposed_bet_fraction_of_stack is not None and proposed_bet_fraction_of_stack >= 0.85:
        return estimate, None  # ya es esencialmente un all-in, coherente

    note = AdjustmentNote(
        layer="spr_coherence",
        message=(
            f"SPR en zona push/fold ({spr.spr:.2f}) — una apuesta que no sea "
            f"prácticamente all-in es estructuralmente incoherente acá"
        ),
    )
    return estimate, note
