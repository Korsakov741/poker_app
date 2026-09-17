"""
Punto 10 — Imagen propia. Espejo del Punto 3 (sizing-tells por
calle) pero aplicado a las manos que HERO mismo mostró, con un peso
EWMA más alto y decaimiento más rápido: el resumen técnico pide
"efecto fuerte 5-10 manos, casi disuelto a partir de 20-30", constante
ajustable manualmente (no hay volumen de datos suficiente sobre uno
mismo como para calcularla objetivamente).

Elegí peso=0.15 — verificado matemáticamente antes de fijarlo:
  (1-0.15)^7  ≈ 0.32  -> a los 7 manos todavía queda ~32% del efecto viejo ("efecto fuerte 5-10 manos")
  (1-0.15)^25 ≈ 0.017 -> a los 25 manos casi no queda nada ("casi disuelto a partir de 20-30")
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field

from ..history.models import HandRecord
from ..profile.sizing_tells import pot_bucket, is_strong
from ..learning.ewma import EWMATracker

# constante ajustable manualmente, tal como pide el resumen técnico —
# no se calcula objetivamente por falta de volumen de datos propios
SELF_IMAGE_WEIGHT = 0.15


@dataclass
class ImageBucketState:
    strong_rate: EWMATracker = field(default_factory=lambda: EWMATracker(weight=SELF_IMAGE_WEIGHT))
    bluff_rate: EWMATracker = field(default_factory=lambda: EWMATracker(weight=SELF_IMAGE_WEIGHT))


class HeroImageTable:
    """
    Sigue las manos que HERO mostró (por street+balde), igual que el
    Punto 3 hace con los rivales — pero acá además se distingue
    explícitamente el farol visto (no es lo mismo mostrar cualquier
    mano que mostrar un farol: un farol visto pesa más en cómo un
    rival razonable debería ajustar su lectura de hero).
    """

    def __init__(self, hero_label: str):
        self.hero_label = hero_label
        self._buckets: dict[tuple[str, str], ImageBucketState] = defaultdict(ImageBucketState)

    def ingest_hand(self, hand: HandRecord) -> None:
        if not hand.showdown or not hand.showdown_hands or not hand.board:
            return
        hole = hand.showdown_hands.get(self.hero_label)
        if hole is None:
            return

        for street in ("flop", "turn", "river"):
            street_board = self._board_at_street(hand.board, street)
            if street_board is None:
                continue
            for a in hand.actions_on(street):
                if a.player != self.hero_label or a.action_type not in ("bet", "raise"):
                    continue
                if a.pot_fraction is None:
                    continue
                bucket = pot_bucket(a.pot_fraction)
                state = self._buckets[(street, bucket)]

                strong = is_strong(street_board, hole)
                state.strong_rate.update(1.0 if strong else 0.0)

                # el farol es un flag EXPLÍCITO (no inferido de la fuerza de
                # la mano) — si no se marcó, no se cuenta ninguna observación
                # de farol para esta apuesta puntual (dato faltante, no "no
                # fue farol")
                if a.is_bluff is not None:
                    state.bluff_rate.update(1.0 if a.is_bluff else 0.0)

    @staticmethod
    def _board_at_street(full_board: list[str], street: str) -> list[str] | None:
        if street == "flop":
            return full_board[:3] if len(full_board) >= 3 else None
        if street == "turn":
            return full_board[:4] if len(full_board) >= 4 else None
        if street == "river":
            return full_board[:5] if len(full_board) >= 5 else None
        return None

    def get_bucket(self, street: str, bucket: str) -> ImageBucketState | None:
        return self._buckets.get((street, bucket))
