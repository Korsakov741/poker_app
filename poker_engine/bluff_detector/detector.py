"""
Punto 16 — Orquestador: combinador JERÁRQUICO de tres señales (no un
promedio simple, tal como exige el resumen técnico), comparado
siempre contra el umbral mínimo del Punto 4.

JERARQUÍA (decisión de diseño, el resumen pide "jerárquico" pero no
da la fórmula): (A) es la base — el dato empírico real de este rival
puntual (o el prior poblacional si no hay confianza suficiente). (B)
y (C) son AJUSTES MULTIPLICATIVOS sobre esa base, no términos que se
promedian aparte — reflejan "cuánto más/menos creíble es ESTE farol
puntual dado el board y mi historia", no una frecuencia propia
independiente. Constantes de fuerza de cada ajuste documentadas
explícitamente, siguiendo el mismo patrón ya usado en los
amortiguadores del Punto 11.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..profile.sizing_tells import pot_bucket
from ..profile.player_profile import PlayerProfile
from ..self_image.image_table import HeroImageTable
from ..self_image.assumption import get_self_image_assumption
from ..ranges.matrix import HandTypeMatrix
from ..equity.ranges import Range
from ..gto_lite.pot_math import pot_odds
from ..gto_lite.bluff_selection import select_bluff_candidates, BluffCandidate
from ..knowledge.population_defaults import POPULATION_DEFAULT_STATS
from .fold_to_bet import FoldToBetTable
from .range_advantage import range_advantage

MIN_OBSERVATIONS_FOLD_RATE = 7   # mismo criterio que el Punto 3
RANGE_ADVANTAGE_STRENGTH = 0.6     # cuánto pesa el ajuste (B) sobre la base
CREDIBILITY_STRENGTH = 0.6           # cuánto pesa el ajuste (C) sobre la base


@dataclass
class BluffOpportunity:
    estimated_success_pct: float        # estimación final, SIEMPRE informativa, nunca una orden
    min_required_pct: float                # alpha del Punto 4 — el umbral mínimo para que valga la pena
    is_above_threshold: bool
    signal_a_source: str                    # 'real_data' | 'population_prior'
    signal_a_value: float
    signal_b_range_advantage: float | None
    signal_c_credibility: float | None
    candidate_combos: list[BluffCandidate]
    reasoning: str


def detect_bluff_opportunity(
    hero_range: HandTypeMatrix,
    board: list[str],
    dead: list[str],
    villain_range: Range,
    villain_profile: PlayerProfile,
    fold_table: FoldToBetTable,
    hero_image_table: HeroImageTable,
    street: str,
    bet: float,
    pot: float,
    top_n_candidates: int = 5,
) -> BluffOpportunity:
    bucket = pot_bucket(bet / pot if pot > 0 else 1.0)

    # ---------- señal (A): base empírica, con respaldo poblacional del Punto 14 ----------
    tracker = fold_table.get_tracker(villain_profile.player, street, bucket)

    if tracker is not None and tracker.confidence >= MIN_OBSERVATIONS_FOLD_RATE:
        signal_a = tracker.value
        signal_a_source = "real_data"
    else:
        signal_a = POPULATION_DEFAULT_STATS["fold_to_cbet_pct"] / 100.0
        signal_a_source = "population_prior"

    # ---------- señal (B): ventaja de rango en el board ----------
    try:
        adv = range_advantage(hero_range, board, dead, villain_range)
        signal_b = adv.my_range_win_rate
    except Exception:
        signal_b = None  # no bloquea el resto del cálculo, solo no ajusta por esto

    # ---------- señal (C): credibilidad de mi historia (Punto 10) ----------
    assumption = get_self_image_assumption(
        hero_image_table, street, bet / pot if pot > 0 else 1.0, villain_profile
    )
    signal_c = assumption.adjusted_credibility  # puede ser None si no hay datos de imagen todavía

    # ---------- combinación jerárquica ----------
    estimate = signal_a
    if signal_b is not None:
        estimate *= 1.0 + (signal_b - 0.5) * RANGE_ADVANTAGE_STRENGTH
    if signal_c is not None:
        estimate *= 1.0 + (signal_c - 0.5) * CREDIBILITY_STRENGTH
    estimate = max(0.0, min(1.0, estimate))

    # ---------- comparación obligatoria contra el umbral del Punto 4 ----------
    # 'pot' acá es el bote ANTES de la apuesta de hero (correcto para el
    # bucket de arriba), pero pot_odds necesita el bote CON esa apuesta ya
    # adentro para que el alpha (umbral mínimo de éxito) no quede inflado.
    alpha = pot_odds(bet, pot + bet)

    candidates = select_bluff_candidates(hero_range, board, dead, villain_range, top_n=top_n_candidates)

    reasoning = (
        f"Señal (A) base: {signal_a*100:.1f}% ({signal_a_source}"
        + (f", {tracker.confidence} obs." if tracker else "")
        + f"). Ajuste (B) ventaja de rango: "
        + (f"{signal_b*100:.1f}%" if signal_b is not None else "sin dato")
        + f". Ajuste (C) credibilidad propia: "
        + (f"{signal_c*100:.1f}%" if signal_c is not None else "sin dato")
        + f". Estimación final: {estimate*100:.1f}% vs. umbral mínimo {alpha*100:.1f}% "
        + f"({'SUPERA' if estimate > alpha else 'NO supera'} el umbral)."
    )

    return BluffOpportunity(
        estimated_success_pct=estimate * 100,
        min_required_pct=alpha * 100,
        is_above_threshold=estimate > alpha,
        signal_a_source=signal_a_source,
        signal_a_value=signal_a,
        signal_b_range_advantage=signal_b,
        signal_c_credibility=signal_c,
        candidate_combos=candidates,
        reasoning=reasoning,
    )
