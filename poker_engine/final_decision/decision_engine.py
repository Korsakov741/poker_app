"""
Punto 8 — Motor de decisión final. Junta las capas anteriores en una
salida ESTRUCTURADA: lista de acciones candidatas, cada una con su
propio rango informativo — nunca una sola acción elegida por la app
(principio no-negociable #1 del proyecto).

Guarda el "paquete de decisión" completo (no solo lo que se muestra)
— es el insumo central que promete el resumen técnico para el futuro
Punto 12.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..equity import EquityResult
from ..gto_lite.pot_math import ImpliedOddsAdjustment
from ..board.combos_vs_hand import ComboVsHandResult
from ..bluff_detector.detector import BluffOpportunity
from ..decision.mixing import ExploitVsGTODecision
from ..icm.penalty import ICMPenaltyResult
from ..table.position_spr import SPRResult
from ..history.models import HandRecord
from ..validation.hand_validation import validate_hand, ValidationIssue

from .legal_actions import legal_actions
from .heuristic_values import (
    ActionValueEstimate, estimate_fold, estimate_check, estimate_call, estimate_bet_value, estimate_bet_bluff,
)
from .adjustments import apply_gto_exploit_layer, apply_icm_layer, apply_spr_coherence_layer, AdjustmentNote


@dataclass
class ActionCandidate:
    action: str
    heuristic_value: float
    top_reasons: list[str]
    adjustment_notes: list[AdjustmentNote]


@dataclass
class DecisionPackage:
    street: str
    legal_actions: list[str]
    candidates: list[ActionCandidate]    # TODAS las acciones evaluadas, ordenadas — nunca una sola elegida
    validation_issues: list[ValidationIssue]
    blocked_by_validation: bool             # True si hay errores graves de datos — no confiar ciegamente en el resto


def _rank(estimate: ActionValueEstimate, notes: list[AdjustmentNote]) -> ActionCandidate:
    top_reasons = [estimate.reasoning] + [n.message for n in notes]
    return ActionCandidate(
        action=estimate.action,
        heuristic_value=estimate.heuristic_value,
        top_reasons=top_reasons[:3],
        adjustment_notes=notes,
    )


def build_decision_package(
    street: str,
    facing_bet: bool,
    hero_label: str,
    equity_result: EquityResult | None,
    implied_odds: ImpliedOddsAdjustment | None,
    combos_result: ComboVsHandResult | None,
    villain_continue_rate: float | None,
    bluff_opportunity: BluffOpportunity | None,
    gto_exploit: ExploitVsGTODecision | None = None,
    icm_penalty: ICMPenaltyResult | None = None,
    spr: SPRResult | None = None,
    proposed_bet_fraction_of_stack: float | None = None,
    hand_so_far: HandRecord | None = None,
) -> DecisionPackage:
    # Punto 13: correr la validación ANTES de construir nada, tal como pide el resumen técnico
    validation_issues: list[ValidationIssue] = []
    if hand_so_far is not None:
        validation_issues = validate_hand(hand_so_far)
    blocked = any(i.severity == "error" for i in validation_issues)

    actions = legal_actions(facing_bet)
    candidates: list[ActionCandidate] = []

    if "fold" in actions:
        est = estimate_fold()
        candidates.append(_rank(est, []))

    if "check" in actions:
        est = estimate_check()
        candidates.append(_rank(est, []))

    if "call" in actions and equity_result is not None and implied_odds is not None:
        est = estimate_call(equity_result, hero_label, implied_odds)
        est, note_icm = apply_icm_layer(est, icm_penalty)
        notes = [n for n in [note_icm] if n]
        candidates.append(_rank(est, notes))

    if "bet" in actions or "raise" in actions:
        if combos_result is not None and villain_continue_rate is not None:
            est = estimate_bet_value(combos_result, villain_continue_rate)
            est, note_gto = apply_gto_exploit_layer(est, gto_exploit)
            est, note_icm = apply_icm_layer(est, icm_penalty)
            est, note_spr = apply_spr_coherence_layer(est, spr, proposed_bet_fraction_of_stack)
            notes = [n for n in [note_gto, note_icm, note_spr] if n]
            candidates.append(_rank(est, notes))

        if bluff_opportunity is not None:
            est = estimate_bet_bluff(bluff_opportunity)
            est, note_gto = apply_gto_exploit_layer(est, gto_exploit)
            est, note_icm = apply_icm_layer(est, icm_penalty)
            est, note_spr = apply_spr_coherence_layer(est, spr, proposed_bet_fraction_of_stack)
            notes = [n for n in [note_gto, note_icm, note_spr] if n]
            candidates.append(_rank(est, notes))

    candidates.sort(key=lambda c: -c.heuristic_value)

    return DecisionPackage(
        street=street,
        legal_actions=actions,
        candidates=candidates,
        validation_issues=validation_issues,
        blocked_by_validation=blocked,
    )
