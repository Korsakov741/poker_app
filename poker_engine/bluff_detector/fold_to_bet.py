"""
Punto 16 — Señal (A): frecuencia histórica de rendición del rival
ante una apuesta de un tamaño específico, por calle+balde.

GAP QUE ENCONTRÉ ARMANDO ESTO (no estaba resuelto por ningún punto
anterior): el Punto 6 tiene fold-to-cbet, pero SOLO para la
continuation bet específica (agresor preflop abriendo el flop), no
para cualquier apuesta en cualquier calle, y sin segmentar por
tamaño. El Punto 9 tiene sizing-tells, pero rastrean la FUERZA de la
mano del que APUESTA, no si el que ENFRENTA la apuesta se retira. Acá
hace falta lo tercero: fold-rate de quien ENFRENTA, segmentado por
calle+balde — así que armo un tracker nuevo, chico, reusando
directamente el `EWMATracker` del Punto 9 (mismo mecanismo, no lo
reinvento).

Peso elegido: HIGH_VOLUME (0.03) del Punto 9, no el SPARSE (0.20) —
a diferencia de las sizing-tells, esto NO necesita showdown (con solo
ver si alguien se retira ya hay una observación), así que hay mucho
más volumen de datos disponible, igual que VPIP/PFR.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field

from ..history.models import HandRecord
from ..profile.sizing_tells import pot_bucket
from ..learning.ewma import EWMATracker, EWMA_WEIGHT_HIGH_VOLUME


class FoldToBetTable:
    def __init__(self):
        self._trackers: dict[tuple[str, str, str], EWMATracker] = defaultdict(
            lambda: EWMATracker(weight=EWMA_WEIGHT_HIGH_VOLUME)
        )

    def ingest_hand(self, hand: HandRecord) -> None:
        for street in ("preflop", "flop", "turn", "river"):
            actions = hand.actions_on(street)
            i = 0
            while i < len(actions):
                a = actions[i]
                if a.action_type in ("bet", "raise") and a.pot_fraction is not None:
                    bucket = pot_bucket(a.pot_fraction)
                    j = i + 1
                    while j < len(actions):
                        resp = actions[j]
                        if resp.action_type == "raise":
                            break  # a partir de acá se enfrenta la subida, no esta apuesta
                        if resp.action_type in ("fold", "call"):
                            key = (resp.player, street, bucket)
                            self._trackers[key].update(1.0 if resp.action_type == "fold" else 0.0)
                        j += 1
                i += 1

    def get_tracker(self, player: str, street: str, bucket: str) -> EWMATracker | None:
        key = (player, street, bucket)
        return self._trackers.get(key)
