"""
Interruptor explícito activo/inactivo según metadata de sesión. A
diferencia del Punto 11 (mezcla continua GTO/Explotador), acá SÍ
corresponde un binario — la diferencia cash/torneo es categórica, tal
como lo aclara el propio resumen técnico.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TournamentContext:
    payouts: list[float]              # payouts[0] = 1er puesto, etc.
    stacks: dict[str, float]            # todos los jugadores restantes
    hero_label: str
    table_labels: set[str]               # jugadores en la mesa actual del hero


@dataclass
class SessionMode:
    is_tournament: bool
    tournament: TournamentContext | None = None

    def __post_init__(self):
        if self.is_tournament and self.tournament is None:
            raise ValueError("is_tournament=True requiere pasar tournament=TournamentContext(...)")
        if not self.is_tournament and self.tournament is not None:
            raise ValueError("is_tournament=False no debería traer un TournamentContext")

    @classmethod
    def cash_game(cls) -> "SessionMode":
        return cls(is_tournament=False)

    @classmethod
    def tournament_mode(cls, context: TournamentContext) -> "SessionMode":
        return cls(is_tournament=True, tournament=context)
