"""
Punto 7 — Notas cualitativas por jugador.

Deliberadamente simple: el Punto 9 aclara que las notas quedan FUERA
del mecanismo de actualización automática (EWMA) a propósito — no
tienen que decaer solas, las edita el usuario. Así que acá no hay
ninguna lógica de cálculo, solo almacenamiento y consulta.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PlayerNote:
    text: str
    tag: str | None = None          # ej. 'farol', 'tilt', 'sizing-tell'
    hand_id: str | None = None       # referencia a la mano donde se originó, si aplica
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PlayerNotesStore:
    def __init__(self):
        self._notes: dict[str, list[PlayerNote]] = defaultdict(list)

    def add_note(
        self, player: str, text: str, tag: str | None = None, hand_id: str | None = None
    ) -> PlayerNote:
        if not text.strip():
            raise ValueError("La nota no puede estar vacía")
        note = PlayerNote(text=text.strip(), tag=tag, hand_id=hand_id)
        self._notes[player].append(note)
        return note

    def get_notes(self, player: str, tag: str | None = None) -> list[PlayerNote]:
        notes = self._notes.get(player, [])
        if tag is not None:
            notes = [n for n in notes if n.tag == tag]
        return list(notes)  # copia — no exponer la lista interna mutable

    def delete_note(self, player: str, note: PlayerNote) -> bool:
        notes = self._notes.get(player, [])
        if note in notes:
            notes.remove(note)
            return True
        return False

    def known_players(self) -> list[str]:
        return list(self._notes.keys())
