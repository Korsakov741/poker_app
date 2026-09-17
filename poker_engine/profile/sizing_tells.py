"""
Punto 3 — Tabla de sizing-tells por calle: para cada apuesta de un
jugador que llegó a showdown, guarda calle + balde de tamaño relativo
al bote + si la mano era fuerte o débil.

CLASIFIFICACIÓN fuerte/débil — decisión de diseño a flaggear: uso la
categoría de mano de treys (par, dos pares, color, etc.) con un corte
simple: TRÍO O MEJOR = fuerte, DOS PARES O PEOR = débil. Es una
heurística, no tiene en cuenta el contexto del board (un top pair en
un board seco puede ser una mano de valor real; acá se clasificaría
"débil" igual). Elegí un corte simple y documentado antes que
inventar un sistema de fuerza contextual — eso empieza a pisar
terreno del Punto 4 (rangos polarizados/mergeados post-flop, que tu
propio resumen técnico marca como extensión PENDIENTE del Submódulo A
del Punto 4, no algo que resolver acá).
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass

from ..equity.cards import to_treys_many
from ..equity import evaluator
from ..history.models import HandRecord

POT_BUCKETS = ("<33%", "33-66%", "66-100%", "sobreapuesta")

_STRONG_RANK_CLASS_MAX = 6  # treys: 1=escalera color ... 6=trío; 7+=dos pares o peor


def pot_bucket(pot_fraction: float) -> str:
    if pot_fraction < 0.33:
        return "<33%"
    if pot_fraction < 0.66:
        return "33-66%"
    if pot_fraction <= 1.0:
        return "66-100%"
    return "sobreapuesta"


def is_strong(board: list[str], hole_cards: tuple[str, str]) -> bool:
    """Pública — reusada por el Punto 9 (aprendizaje incremental) además de acá."""
    board_t = to_treys_many(board)
    hand_t = to_treys_many(hole_cards)
    score = evaluator.score(board_t, hand_t)
    rank_cls = evaluator.rank_class(score)
    return rank_cls <= _STRONG_RANK_CLASS_MAX


@dataclass
class SizingTellObservation:
    hand_id: str
    street: str
    bucket: str
    was_strong: bool


class SizingTellsTable:
    def __init__(self):
        self._observations: dict[str, list[SizingTellObservation]] = defaultdict(list)

    def ingest_hand(self, hand: HandRecord) -> None:
        if not hand.showdown or not hand.showdown_hands or not hand.board:
            return  # sin showdown (o sin board registrado) no hay forma de saber si era fuerte o débil

        for street in ("flop", "turn", "river"):
            street_board = self._board_at_street(hand.board, street)
            if street_board is None:
                continue
            for a in hand.actions_on(street):
                if a.action_type not in ("bet", "raise") or a.pot_fraction is None:
                    continue
                hole = hand.showdown_hands.get(a.player)
                if hole is None:
                    continue  # este jugador apostó pero no mostró la mano (se retiraron antes, etc.)
                strong = is_strong(street_board, hole)
                self._observations[a.player].append(
                    SizingTellObservation(
                        hand_id=hand.hand_id,
                        street=street,
                        bucket=pot_bucket(a.pot_fraction),
                        was_strong=strong,
                    )
                )

    @staticmethod
    def _board_at_street(full_board: list[str], street: str) -> list[str] | None:
        if street == "flop":
            return full_board[:3] if len(full_board) >= 3 else None
        if street == "turn":
            return full_board[:4] if len(full_board) >= 4 else None
        if street == "river":
            return full_board[:5] if len(full_board) >= 5 else None
        return None

    def strong_rate(self, player: str, street: str, bucket: str) -> tuple[float | None, int]:
        """(tasa_de_manos_fuertes, cantidad_de_observaciones) para ese balde específico."""
        obs = [
            o for o in self._observations.get(player, [])
            if o.street == street and o.bucket == bucket
        ]
        if not obs:
            return None, 0
        strong_count = sum(1 for o in obs if o.was_strong)
        return strong_count / len(obs), len(obs)

    def all_observations(self, player: str) -> list[SizingTellObservation]:
        return list(self._observations.get(player, []))
