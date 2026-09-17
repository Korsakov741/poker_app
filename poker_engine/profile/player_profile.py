"""
Punto 3 — Orquestador: junta las piezas (scores + sizing-tells) y
deja lugar explícito para el ajuste manual con las notas del Punto 7,
tal como pide "Depende de: ... punto 7 (notas cualitativas como
ajuste manual sobre el puntaje)".

DECISIÓN DE DISEÑO: las notas son texto libre — no hay forma honesta
de "parsearlas" automáticamente en un número sin inventar NLP que no
pediste. El ajuste manual es exactamente eso: MANUAL. Esta clase
expone las notas junto al perfil calculado para que quien lea el
perfil (vos, o más adelante la UI) decida si corresponde pisar el
puntaje calculado con `override_tightness` / `override_aggression`,
informado por lo que dicen las notas.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..history.hud import HandHistoryDB
from ..history.notes import PlayerNotesStore, PlayerNote
from .scores import compute_behavior_scores, BehaviorScores
from .sizing_tells import SizingTellsTable


@dataclass
class PlayerProfile:
    player: str
    scores: BehaviorScores
    notes: list[PlayerNote]
    tightness_override: float | None = None
    aggression_override: float | None = None

    @property
    def effective_tightness(self) -> float | None:
        return self.tightness_override if self.tightness_override is not None else self.scores.tightness_score

    @property
    def effective_aggression(self) -> float | None:
        return self.aggression_override if self.aggression_override is not None else self.scores.aggression_score

    def override_tightness(self, value: float) -> None:
        if not (0.0 <= value <= 100.0):
            raise ValueError("El override debe estar entre 0 y 100")
        self.tightness_override = value

    def override_aggression(self, value: float) -> None:
        if not (0.0 <= value <= 100.0):
            raise ValueError("El override debe estar entre 0 y 100")
        self.aggression_override = value

    def clear_overrides(self) -> None:
        self.tightness_override = None
        self.aggression_override = None


def build_player_profile(
    player: str,
    hud_db: HandHistoryDB,
    notes_store: PlayerNotesStore,
) -> PlayerProfile:
    stats = hud_db.get_stats(player)
    scores = compute_behavior_scores(stats)
    notes = notes_store.get_notes(player)
    return PlayerProfile(player=player, scores=scores, notes=notes)
