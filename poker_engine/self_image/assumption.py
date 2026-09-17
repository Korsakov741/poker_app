"""
Punto 10 — Orquestador final. Toda salida de acá es una suposición
sobre cómo un rival razonable podría estar leyendo a hero — nunca un
hecho objetivo como un showdown real del Punto 3. El campo `caveat`
no es decorativo: cualquier UI que consuma esto tiene que mostrarlo,
no solo el número.
"""
from __future__ import annotations
from dataclasses import dataclass

from .image_table import HeroImageTable, SELF_IMAGE_WEIGHT
from .relevance import estimate_relevance, RelevanceEstimate
from ..profile.player_profile import PlayerProfile
from ..profile.sizing_tells import pot_bucket

CAVEAT_TEXT = (
    "Esto es una suposición sobre cómo un rival razonable podría estar "
    "leyendo a hero en este momento — no un hecho objetivo. A diferencia "
    "de los showdowns reales del Punto 3, acá no hay forma de saber qué "
    "piensa el rival de verdad."
)


@dataclass
class SelfImageAssumption:
    street: str
    bucket: str
    hero_strong_rate_ewma: float | None    # qué tan seguido, ÚLTIMAMENTE, hero mostró fuerza con este tamaño
    hero_bluff_rate_ewma: float | None       # qué tan seguido, ÚLTIMAMENTE, hero mostró un farol EXPLÍCITO con este tamaño
    n_observations_strong: int
    n_observations_bluff: int
    villain_relevance: RelevanceEstimate      # cuánto le importa a ESTE rival puntual
    adjusted_credibility: float | None         # ver docstring de la función
    caveat: str = CAVEAT_TEXT


def get_self_image_assumption(
    hero_image_table: HeroImageTable,
    street: str,
    pot_fraction: float,
    villain_profile: PlayerProfile,
    manual_relevance_override: float | None = None,
) -> SelfImageAssumption:
    """
    `adjusted_credibility`: qué tan creíble debería verse, PARA ESTE
    RIVAL PUNTUAL, una apuesta de hero de este tamaño en esta calle —
    combina qué tan seguido hero mostró fuerza ahí (si mostró fuerza
    seguido, una apuesta similar ahora es más creíble como valor) con
    cuánto le importa a este rival la imagen de hero (`villain_relevance`).
    Si el rival no ajusta nada (relevance≈0), da igual la imagen de
    hero — por eso se multiplican, no se promedian.
    """
    bucket = pot_bucket(pot_fraction)
    state = hero_image_table.get_bucket(street, bucket)
    relevance = estimate_relevance(villain_profile, manual_relevance_override)

    if state is None or state.strong_rate.value is None:
        return SelfImageAssumption(
            street=street, bucket=bucket,
            hero_strong_rate_ewma=None, hero_bluff_rate_ewma=None,
            n_observations_strong=0, n_observations_bluff=0,
            villain_relevance=relevance, adjusted_credibility=None,
        )

    adjusted = state.strong_rate.value * relevance.weight

    return SelfImageAssumption(
        street=street, bucket=bucket,
        hero_strong_rate_ewma=state.strong_rate.value,
        hero_bluff_rate_ewma=state.bluff_rate.value,
        n_observations_strong=state.strong_rate.confidence,
        n_observations_bluff=state.bluff_rate.confidence,
        villain_relevance=relevance,
        adjusted_credibility=adjusted,
    )
