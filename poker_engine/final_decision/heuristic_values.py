"""
Punto 8 — Estimación de valor heurística (NO un solver completo) por
cada acción candidata, tal como pide el resumen técnico:
  - retirarse: referencia cero
  - pagar: equity del Punto 1 vs. umbral del Punto 4
  - apostar-valor: combos del Punto 15 + perfil del Punto 3
  - apostar-farol: salida del Punto 16

DECISIÓN DE DISEÑO: "apostar-valor" y "apostar-farol" son la MISMA
acción física (bet/raise) pero con justificaciones distintas — los
trato como dos candidatos separados en la lista de salida (no un
solo "bet" combinado), porque eso es justo lo que necesita mostrar
el principio de "rangos, no órdenes": el usuario tiene que poder ver
POR QUÉ apostar tendría sentido en cada caso, no una sola cifra
mezclada.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..equity import EquityResult
from ..gto_lite.pot_math import ImpliedOddsAdjustment
from ..board.combos_vs_hand import ComboVsHandResult
from ..bluff_detector.detector import BluffOpportunity


@dataclass
class ActionValueEstimate:
    action: str            # 'fold' | 'call' | 'bet_value' | 'bet_bluff'
    heuristic_value: float   # positivo = razonable, negativo = no se recomienda mostrar como candidato fuerte
    reasoning: str


def estimate_fold(reasoning: str = "Referencia cero — retirarse siempre está disponible como piso") -> ActionValueEstimate:
    return ActionValueEstimate(action="fold", heuristic_value=0.0, reasoning=reasoning)


def estimate_check(reasoning: str = "Referencia cero — chequear no arriesga fichas, siempre disponible como piso") -> ActionValueEstimate:
    return ActionValueEstimate(action="check", heuristic_value=0.0, reasoning=reasoning)


def estimate_call(
    equity_result: EquityResult,
    hero_label: str,
    implied_odds: ImpliedOddsAdjustment,
) -> ActionValueEstimate:
    hero_equity = next(p.equity_pct for p in equity_result.players if p.label == hero_label) / 100.0
    value = hero_equity - implied_odds.adjusted_alpha
    reasoning = (
        f"Equity real ({hero_equity*100:.1f}%, {equity_result.mode}) vs. umbral ajustado "
        f"({implied_odds.adjusted_alpha*100:.1f}%). {implied_odds.reasoning}"
    )
    return ActionValueEstimate(action="call", heuristic_value=value, reasoning=reasoning)


def estimate_bet_value(
    combos_result: ComboVsHandResult,
    villain_continue_rate: float,
) -> ActionValueEstimate:
    """
    villain_continue_rate: fracción [0,1] con la que el rival sigue
    en la mano ante esta apuesta (1 - fold_rate) — vale lo que valga
    apostar por valor solo si el rival efectivamente paga con manos
    peores.
    """
    value = (combos_result.weighted_pct_losing_to_me / 100.0) * villain_continue_rate
    reasoning = (
        f"{combos_result.raw_count_losing_to_me} de {combos_result.raw_count_total} combos posibles "
        f"del rival pierden contra mi mano ({combos_result.weighted_pct_losing_to_me:.1f}% ponderado), "
        f"con una tasa de continuación estimada del {villain_continue_rate*100:.1f}%"
    )
    return ActionValueEstimate(action="bet_value", heuristic_value=value, reasoning=reasoning)


def estimate_bet_bluff(bluff_opportunity: BluffOpportunity) -> ActionValueEstimate:
    value = (bluff_opportunity.estimated_success_pct - bluff_opportunity.min_required_pct) / 100.0
    return ActionValueEstimate(action="bet_bluff", heuristic_value=value, reasoning=bluff_opportunity.reasoning)
