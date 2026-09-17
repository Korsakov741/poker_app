"""
Punto 9 — Aplica el EWMA a donde corresponde:
  - VPIP y PFR (peso chico, alto volumen) -> vía el Punto 3
  - sizing-tells por (calle, balde) (peso grande, dato escaso) -> vía el Punto 3

Y a donde el resumen técnico dice EXPLÍCITAMENTE que NO corresponde:
  - Punto 6 (stats crudas VPIP%/PFR%/AF% de toda la vida): sigue
    siendo promedio acumulado simple, sin cambios — ya lo es, no
    tocamos hud.py más que para exponer la regla compartida.
  - Punto 7 (notas): fuera del mecanismo automático a propósito, no
    debe decaer solo, lo edita el usuario — no tocamos notes.py.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field

from ..history.models import HandRecord
from ..history.hud import vpip_pfr_flags_for_hand
from ..profile.sizing_tells import pot_bucket, is_strong
from .ewma import EWMATracker, EWMA_WEIGHT_HIGH_VOLUME, EWMA_WEIGHT_SPARSE


@dataclass
class PlayerLearningState:
    player: str
    vpip_ewma: EWMATracker = field(default_factory=lambda: EWMATracker(weight=EWMA_WEIGHT_HIGH_VOLUME))
    pfr_ewma: EWMATracker = field(default_factory=lambda: EWMATracker(weight=EWMA_WEIGHT_HIGH_VOLUME))
    # (calle, balde) -> tracker de sizing-tell para ese balde específico
    sizing_tell_ewmas: dict[tuple[str, str], EWMATracker] = field(default_factory=dict)

    def sizing_tell(self, street: str, bucket: str) -> EWMATracker | None:
        return self.sizing_tell_ewmas.get((street, bucket))

    def get_or_create_sizing_tell(self, street: str, bucket: str) -> EWMATracker:
        key = (street, bucket)
        if key not in self.sizing_tell_ewmas:
            self.sizing_tell_ewmas[key] = EWMATracker(weight=EWMA_WEIGHT_SPARSE)
        return self.sizing_tell_ewmas[key]


class LearningStore:
    def __init__(self):
        self._states: dict[str, PlayerLearningState] = {}

    def _state_for(self, player: str) -> PlayerLearningState:
        if player not in self._states:
            self._states[player] = PlayerLearningState(player=player)
        return self._states[player]

    def get_state(self, player: str) -> PlayerLearningState | None:
        return self._states.get(player)

    def ingest_hand(self, hand: HandRecord) -> None:
        self._ingest_vpip_pfr(hand)
        self._ingest_sizing_tells(hand)

    def _ingest_vpip_pfr(self, hand: HandRecord) -> None:
        for player, (vpip, pfr) in vpip_pfr_flags_for_hand(hand).items():
            state = self._state_for(player)
            state.vpip_ewma.update(1.0 if vpip else 0.0)
            state.pfr_ewma.update(1.0 if pfr else 0.0)

    def _ingest_sizing_tells(self, hand: HandRecord) -> None:
        if not hand.showdown or not hand.showdown_hands or not hand.board:
            return
        for street in ("flop", "turn", "river"):
            street_board = self._board_at_street(hand.board, street)
            if street_board is None:
                continue
            for a in hand.actions_on(street):
                if a.action_type not in ("bet", "raise") or a.pot_fraction is None:
                    continue
                hole = hand.showdown_hands.get(a.player)
                if hole is None:
                    continue
                strong = is_strong(street_board, hole)
                bucket = pot_bucket(a.pot_fraction)
                state = self._state_for(a.player)
                tracker = state.get_or_create_sizing_tell(street, bucket)
                tracker.update(1.0 if strong else 0.0)

    @staticmethod
    def _board_at_street(full_board: list[str], street: str) -> list[str] | None:
        if street == "flop":
            return full_board[:3] if len(full_board) >= 3 else None
        if street == "turn":
            return full_board[:4] if len(full_board) >= 4 else None
        if street == "river":
            return full_board[:5] if len(full_board) >= 5 else None
        return None
