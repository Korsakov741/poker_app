"""
Punto 4 — Submódulo B (dinámico, se recalcula en cada decisión):
cuatro fórmulas derivadas de alpha = apuesta/(bote+apuesta).

IMPORTANTE (principio no-negociable #1 del proyecto): MDF y el ratio
farol-valor son frecuencias de RANGO AGREGADO, no instrucciones para
esta mano puntual — se documenta explícito en cada función que las
devuelve, tal como exige el resumen técnico.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..profile.player_profile import PlayerProfile

IMPLIED_ODDS_MAX_REDUCTION = 0.3  # con el rival más pasivo posible, el alpha efectivo baja hasta un 30%


def pot_odds(bet: float, pot: float) -> float:
    """alpha = apuesta / (bote + apuesta). Fracción de equity mínima necesaria para que pagar sea rentable."""
    if bet <= 0 or pot < 0:
        raise ValueError("bet debe ser positivo, pot no puede ser negativo")
    return bet / (pot + bet)


def minimum_defense_frequency(bet: float, pot: float) -> float:
    """
    MDF = 1 - alpha. Frecuencia AGREGADA con la que el RANGO debería
    continuar para que el rival no pueda farolear con ganancia
    garantizada — NO es una instrucción sobre esta mano puntual.
    """
    return 1.0 - pot_odds(bet, pot)


def bluff_to_value_ratio(bet: float, pot: float) -> tuple[float, float]:
    """
    Ratio farol:valor = alpha : (1-alpha) — frecuencia AGREGADA de
    combos de farol que el RANGO de apuesta debería tener por cada
    combo de valor para estar balanceado. NO es una instrucción sobre
    qué hacer con esta mano puntual.
    """
    alpha = pot_odds(bet, pot)
    return (alpha, 1.0 - alpha)


@dataclass
class ImpliedOddsAdjustment:
    raw_alpha: float
    adjusted_alpha: float
    reasoning: str


def implied_odds_adjusted_alpha(
    bet: float, pot: float, villain_profile: PlayerProfile | None
) -> ImpliedOddsAdjustment:
    """
    Ajuste CUALITATIVO hacia abajo del alpha, dependiendo del perfil
    del Punto 3: un rival más pasivo (aggression_score bajo) tiende a
    pagar más seguido en calles futuras con manos hechas — mejores
    implied odds, así que el alpha EFECTIVO necesario baja (el call
    se vuelve más barato en términos reales, no solo de esta calle).
    """
    raw_alpha = pot_odds(bet, pot)

    if villain_profile is None or villain_profile.effective_aggression is None:
        return ImpliedOddsAdjustment(
            raw_alpha=raw_alpha, adjusted_alpha=raw_alpha,
            reasoning="sin perfil de rival -> sin ajuste, se usa pot odds tal cual",
        )

    passivity = 1.0 - villain_profile.effective_aggression / 100.0
    reduction_factor = 1.0 - (passivity * IMPLIED_ODDS_MAX_REDUCTION)
    adjusted = raw_alpha * reduction_factor

    return ImpliedOddsAdjustment(
        raw_alpha=raw_alpha, adjusted_alpha=adjusted,
        reasoning=(
            f"rival con pasividad {passivity:.2f} (aggression_score={villain_profile.effective_aggression:.0f}) "
            f"-> alpha ajustado de {raw_alpha:.3f} a {adjusted:.3f} (mejores implied odds asumidas)"
        ),
    )
