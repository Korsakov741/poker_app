"""
Estado de la aplicación — un único objeto en memoria (proceso
single-user, pensado para uso personal, no multi-tenant).

DISEÑO DE PERSISTENCIA: en vez de serializar cada estructura derivada
(EWMATracker, HandHistoryDB, etc. — muchas no son triviales de volcar
a JSON tal cual), guardo solo la fuente de verdad cruda: la lista de
HandRecord ya jugadas + las notas del Punto 7 + los rangos manuales
guardados por jugador. Al arrancar, se RE-INGESTA todo el historial
crudo a través de los mismos `ingest_hand()` de cada punto — así el
estado derivado (HUD, EWMA, sizing-tells, etc.) siempre se reconstruye
de manera consistente, sin tener que mantener sincronizados varios
formatos de serialización distintos.
"""
from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path

from poker_engine.history import Action, HandRecord, HandHistoryDB, PlayerNotesStore
from poker_engine.learning import LearningStore
from poker_engine.bluff_detector import FoldToBetTable
from poker_engine.self_image import HeroImageTable
from poker_engine.profile.sizing_tells import SizingTellsTable
from poker_engine.ranges import RangeState
from poker_engine.session_review import SessionReview

HERO_LABEL = "hero"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HANDS_FILE = DATA_DIR / "hands.json"
NOTES_FILE = DATA_DIR / "notes.json"


class AppState:
    def __init__(self):
        self.hand_records: list[HandRecord] = []
        self.notes_store = PlayerNotesStore()

        self.hud_db = HandHistoryDB()
        self.learning_store = LearningStore()
        self.fold_table = FoldToBetTable()
        self.hero_image_table = HeroImageTable(hero_label=HERO_LABEL)
        self.sizing_tells = SizingTellsTable()
        self.session_review = SessionReview("sesión actual")

        # rangos manuales guardados por jugador (Punto 2) — se guardan
        # aparte porque son ENTRADA del usuario, no algo derivado de manos
        self.saved_ranges: dict[str, dict[str, float]] = {}

        self._load()

    # ---------- ingesta ----------
    def ingest_hand(self, hand: HandRecord, save: bool = True) -> None:
        self.hand_records.append(hand)
        self.hud_db.ingest_hand(hand)
        self.learning_store.ingest_hand(hand)
        self.fold_table.ingest_hand(hand)
        self.hero_image_table.ingest_hand(hand)
        self.sizing_tells.ingest_hand(hand)
        if save:
            self._save()

    # ---------- persistencia ----------
    def _load(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if HANDS_FILE.exists():
            raw = json.loads(HANDS_FILE.read_text())
            for hd in raw:
                actions = [Action(**a) for a in hd["actions"]]
                hand = HandRecord(
                    hand_id=hd["hand_id"], players=hd["players"], board=hd.get("board", []),
                    actions=actions, winners=hd.get("winners", []), showdown=hd.get("showdown", False),
                    showdown_hands={k: tuple(v) for k, v in hd.get("showdown_hands", {}).items()},
                )
                self.ingest_hand(hand, save=False)  # re-ingesta sin re-guardar (ya está guardado)

        if NOTES_FILE.exists():
            raw_notes = json.loads(NOTES_FILE.read_text())
            for player, notes in raw_notes.items():
                for n in notes:
                    self.notes_store.add_note(player, n["text"], tag=n.get("tag"), hand_id=n.get("hand_id"))

    def _save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        serializable = []
        for h in self.hand_records:
            d = asdict(h)
            serializable.append(d)
        HANDS_FILE.write_text(json.dumps(serializable, indent=2))
        self._save_notes()

    def _save_notes(self) -> None:
        out = {}
        for player in self.notes_store.known_players():
            out[player] = [
                {"text": n.text, "tag": n.tag, "hand_id": n.hand_id}
                for n in self.notes_store.get_notes(player)
            ]
        NOTES_FILE.write_text(json.dumps(out, indent=2))

    def save_range(self, player: str, weights: dict[str, float]) -> None:
        self.saved_ranges[player] = weights


# instancia única del proceso
state = AppState()
