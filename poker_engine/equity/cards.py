"""
Utilidades de cartas para el motor de equity (Punto 1).

Notación estándar usada en TODO el sistema (no solo acá): string de 2
caracteres, rango + palo. Rango en 23456789TJQKA, palo en shdc
(spades, hearts, diamonds, clubs). Ej: "As", "Td", "2h".

Este módulo es la única capa que sabe que por debajo usamos `treys`
para evaluar manos. Si el día de mañana cambiamos de librería de
evaluación, solo se toca este archivo y evaluator.py.
"""
from __future__ import annotations
from typing import Iterable
from treys import Card as _TreysCard

RANKS = "23456789TJQKA"
SUITS = "shdc"

FULL_DECK: list[str] = [r + s for r in RANKS for s in SUITS]
assert len(FULL_DECK) == 52


def validate_card(card: str) -> None:
    if not isinstance(card, str) or len(card) != 2:
        raise ValueError(f"Carta inválida: {card!r} (formato esperado 'As', 'Td', etc.)")
    rank, suit = card[0].upper(), card[1].lower()
    if rank not in RANKS or suit not in SUITS:
        raise ValueError(f"Carta inválida: {card!r} (formato esperado 'As', 'Td', etc.)")


def normalize(card: str) -> str:
    """Normaliza a rango-mayúscula + palo-minúscula, ej 'as' -> 'As'."""
    validate_card(card)
    return card[0].upper() + card[1].lower()


def to_treys(card: str) -> int:
    return _TreysCard.new(normalize(card))


def to_treys_many(cards: Iterable[str]) -> list[int]:
    return [to_treys(c) for c in cards]


def check_no_duplicates(*groups: Iterable[str]) -> None:
    """
    Valida que no haya cartas repetidas entre (y dentro de) los grupos
    dados. Se llama en el borde de entrada del motor (hero, board,
    dead cards) — la validación de remoción DENTRO de la simulación
    (contra rangos de rivales) la hace cada simulador por separado,
    porque ahí las cartas de rivales cambian en cada iteración.
    """
    seen: dict[str, str] = {}
    for group_name, cards in zip(
        [f"grupo_{i}" for i in range(len(groups))], groups
    ):
        for c in cards:
            n = normalize(c)
            if n in seen:
                raise ValueError(
                    f"Carta duplicada detectada: {n} aparece más de una vez "
                    f"entre las cartas fijas (hero/board/dead)."
                )
            seen[n] = group_name
