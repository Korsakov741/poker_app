"""
Punto 10 — El ajuste de imagen NO se aplica parejo a todos los
rivales (tal como exige el resumen técnico): se cruza con el perfil
del Punto 3 para estimar si ESE rival puntual es de los que ajustan
su juego según lo que ve, o si es pasivo/no observador.

DECISIÓN DE DISEÑO A FLAGGEAR: no existe ningún stat directo de
"cuán observador es un jugador" en los puntos ya construidos — el
resumen técnico pide cruzar con el Punto 3 pero no dice con qué
fórmula. Uso el `aggression_score` del Punto 3 como proxy: jugadores
más agresivos tienden a pensar más activamente en rangos y ajustar
más seguido según lo que ven; jugadores muy pasivos ("calling
station") suelen jugar su propia mano sin ajustar mucho por imagen.
Es una heurística razonable, NO un hecho — por eso el resultado de
este módulo siempre se marca como suposición (ver assumption.py). El
Punto 7 (notas) permite pisar esta estimación a mano cuando el
usuario tiene mejor información que la heurística.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..profile.player_profile import PlayerProfile


@dataclass
class RelevanceEstimate:
    weight: float          # 0.0 = no ajusta nada por imagen, 1.0 = ajusta totalmente
    source: str              # 'aggression_proxy' | 'manual_override'
    based_on_aggression: float | None = None


def estimate_relevance(
    villain_profile: PlayerProfile,
    manual_override: float | None = None,
) -> RelevanceEstimate:
    if manual_override is not None:
        if not (0.0 <= manual_override <= 1.0):
            raise ValueError("manual_override debe estar entre 0.0 y 1.0")
        return RelevanceEstimate(weight=manual_override, source="manual_override")

    aggression = villain_profile.effective_aggression
    if aggression is None:
        # sin datos de este rival todavía -> asunción neutral, ni "asume que ajusta"
        # ni "asume que no ajusta" -- punto medio explícito, no un valor inventado
        return RelevanceEstimate(weight=0.5, source="aggression_proxy", based_on_aggression=None)

    return RelevanceEstimate(
        weight=aggression / 100.0,
        source="aggression_proxy",
        based_on_aggression=aggression,
    )
