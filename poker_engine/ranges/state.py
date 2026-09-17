"""
RangeState — orquesta el pipeline de 4 pasos del Punto 2 para UN
rival, y guarda el historial completo (no sobrescribe), tal como pide
el resumen técnico para uso futuro del Punto 12.

Los 4 pasos del resumen técnico, mapeados acá:
  1. Rango preflop inicial por posición -> initialize_preflop()
  2. Filtrado por bloqueo de cartas      -> se aplica al vuelo en
                                             to_point1_range(), NO se
                                             guarda como snapshot
                                             propio (ver nota abajo)
  3. Narrowing por acción                -> apply_action_narrowing()
  4. Renormalización                     -> aplicada automáticamente
                                             adentro de (3) y de
                                             cualquier ajuste manual

NOTA DE DISEÑO sobre el paso 2 (a flaggear): la remoción de cartas no
se guarda como una entrada de historial separada porque no es una
propiedad de la matriz tipo-por-tipo — depende de qué cartas están
visibles en el momento de la consulta, no de una decisión tomada en
una calle particular. Se recalcula al vuelo cada vez que se pide la
expansión a combos (to_point1_range). Lo que SÍ se guarda en el
historial es cómo evolucionaron los PESOS por tipo (por posición,
por narrowing de acción, por ajuste manual) — eso es lo que tiene
sentido revisar después en el Punto 12.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .matrix import HandTypeMatrix
from .narrowing import NarrowAction, narrow_by_action
from ..equity.ranges import Range


@dataclass
class StreetSnapshot:
    order: int
    street_label: str   # 'preflop', 'flop', 'turn', 'river', etc.
    reason: str            # descripción humana de por qué cambió acá
    matrix: HandTypeMatrix


class RangeState:
    def __init__(self, opponent_label: str):
        self.opponent_label = opponent_label
        self.history: list[StreetSnapshot] = []

    @property
    def current(self) -> HandTypeMatrix:
        if not self.history:
            raise RuntimeError(
                f"RangeState de {self.opponent_label} sin inicializar — "
                f"llamar initialize_preflop() primero"
            )
        return self.history[-1].matrix

    # ---------- paso 1 ----------
    def initialize_preflop(self, matrix: HandTypeMatrix, reason: str) -> None:
        if self.history:
            raise RuntimeError(f"RangeState de {self.opponent_label} ya fue inicializado")
        self.history.append(
            StreetSnapshot(order=0, street_label="preflop", reason=reason, matrix=matrix.copy())
        )

    # ---------- paso 3 + 4 (narrowing genérico + renormalización) ----------
    def apply_action_narrowing(
        self,
        action: NarrowAction,
        street_label: str,
        keep_fraction: float | None = None,
    ) -> None:
        narrowed = narrow_by_action(self.current, action, keep_fraction)
        renormalized = narrowed.scale_max_to_one()
        self.history.append(
            StreetSnapshot(
                order=len(self.history),
                street_label=street_label,
                reason=f"acción del rival: {action.value}",
                matrix=renormalized,
            )
        )

    # ---------- ajuste manual (pintar / top% / notación) ----------
    def apply_manual_adjustment(
        self, matrix: HandTypeMatrix, street_label: str, reason: str = "ajuste manual"
    ) -> None:
        """
        Registra un ajuste manual como una NUEVA entrada de historial
        (nunca pisa la anterior). Renormaliza (paso 4) por consistencia
        con el resto del pipeline.
        """
        renormalized = matrix.scale_max_to_one()
        self.history.append(
            StreetSnapshot(
                order=len(self.history),
                street_label=street_label,
                reason=reason,
                matrix=renormalized,
            )
        )

    # ---------- paso 2 (al vuelo) + puente al Punto 1 ----------
    def to_point1_range(self, excluded_cards: set[str]) -> Range:
        combos = self.current.expand_to_weighted_combos()
        filtered = [
            (c1, c2, w) for c1, c2, w in combos
            if c1 not in excluded_cards and c2 not in excluded_cards
        ]
        if not filtered:
            raise RuntimeError(
                f"El rango de {self.opponent_label} quedó sin combos válidos "
                f"dadas las cartas visibles actuales (board/hero/dead/otros rivales)."
            )
        return Range.from_combos(filtered)

    def history_summary(self) -> list[dict]:
        """Vista legible del historial completo — insumo directo del futuro Punto 12."""
        return [
            {
                "order": s.order,
                "street": s.street_label,
                "reason": s.reason,
                "tipos_activos": len(s.matrix.nonzero_types()),
                "combos_efectivos": round(s.matrix.combo_count_weighted(), 1),
            }
            for s in self.history
        ]
