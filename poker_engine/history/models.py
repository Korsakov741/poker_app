"""
Modelo de datos mínimo de una mano jugada — el input que consume el
Punto 6 (y a futuro el Punto 9 para el aprendizaje incremental). No
es el flujo de captura completo de la app (eso es UI, más adelante);
es la estructura de datos que necesita el cálculo de stats.
"""
from __future__ import annotations
from dataclasses import dataclass, field

STREETS = ("preflop", "flop", "turn", "river")
ACTION_TYPES = ("post_blind", "fold", "check", "call", "bet", "raise")


@dataclass
class Action:
    player: str
    street: str
    action_type: str
    order: int
    pot_fraction: float | None = None  # tamaño relativo al bote (solo aplica a bet/raise), ej 0.7 = 70% del bote
    is_bluff: bool | None = None        # flag EXPLÍCITO (no inferido): esta apuesta puntual ¿fue un farol real?
                                          # solo lo sabe el propio jugador que apostó — pensado para las
                                          # propias apuestas de hero (Punto 10), no para inferir sobre rivales

    def __post_init__(self):
        if self.street not in STREETS:
            raise ValueError(f"Calle inválida: {self.street!r}")
        if self.action_type not in ACTION_TYPES:
            raise ValueError(f"Tipo de acción inválido: {self.action_type!r}")
        if self.pot_fraction is not None and self.action_type not in ("bet", "raise"):
            raise ValueError("pot_fraction solo aplica a acciones 'bet' o 'raise'")
        if self.pot_fraction is not None and self.pot_fraction <= 0:
            raise ValueError(f"pot_fraction debe ser positivo, se recibió {self.pot_fraction}")
        if self.is_bluff is not None and self.action_type not in ("bet", "raise"):
            raise ValueError("is_bluff solo aplica a acciones 'bet' o 'raise'")


@dataclass
class HandRecord:
    hand_id: str
    players: list[str]
    board: list[str] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    winners: list[str] = field(default_factory=list)
    showdown: bool = False
    showdown_hands: dict[str, tuple[str, str]] = field(default_factory=dict)  # player -> (carta1, carta2), solo si showdown=True

    def actions_on(self, street: str) -> list[Action]:
        return sorted(
            [a for a in self.actions if a.street == street], key=lambda a: a.order
        )
