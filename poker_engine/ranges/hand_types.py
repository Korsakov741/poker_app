"""
Los 169 tipos de mano preflop (matriz 13x13) y su expansión a combos
exactos. Base de todo el Punto 2.

Convención de notación de tipo (estándar en la industria del póker,
no inventada acá): 2 caracteres de rango + sufijo, rango más fuerte
primero.
  - Par:      "AA", "KK", ..., "22"                (13 tipos)
  - Suited:   "AKs", "AQs", ..., "32s"              (78 tipos)
  - Offsuit:  "AKo", "AQo", ..., "32o"               (78 tipos)
Total: 169.
"""
from __future__ import annotations
from itertools import combinations, product

from ..equity.cards import RANKS, SUITS, FULL_DECK

# Orden descendente para la grilla visual (A arriba, 2 abajo) — el
# orden ascendente de cards.py (RANKS) es al revés, lo invertimos acá
# porque a nadie le sirve una grilla con el As abajo a la derecha.
RANKS_DESC = RANKS[::-1]  # "AKQJT98765432"


def _rank_index(rank: str) -> int:
    """0 = As (más fuerte), 12 = 2 (más débil)."""
    return RANKS_DESC.index(rank)


def all_hand_types() -> list[str]:
    """Los 169 tipos, en cualquier orden (no asumir orden de grilla)."""
    types = []
    for r in RANKS_DESC:
        types.append(r + r)  # par
    for r1, r2 in combinations(RANKS_DESC, 2):  # r1 siempre más fuerte que r2
        types.append(r1 + r2 + "s")
        types.append(r1 + r2 + "o")
    return types


ALL_HAND_TYPES: list[str] = all_hand_types()
assert len(ALL_HAND_TYPES) == 169, f"Se esperaban 169 tipos, hay {len(ALL_HAND_TYPES)}"
_VALID_TYPES = set(ALL_HAND_TYPES)


def validate_hand_type(hand_type: str) -> None:
    if hand_type not in _VALID_TYPES:
        raise ValueError(f"Tipo de mano inválido: {hand_type!r}")


def is_pair(hand_type: str) -> bool:
    validate_hand_type(hand_type)
    return len(hand_type) == 2


def matrix_position(hand_type: str) -> tuple[int, int]:
    """
    (fila, columna) en la grilla 13x13, convención estándar:
    diagonal = pares, arriba de la diagonal = suited, abajo = offsuit.
    fila/columna 0 = As, 12 = 2.
    """
    validate_hand_type(hand_type)
    if is_pair(hand_type):
        i = _rank_index(hand_type[0])
        return (i, i)
    r1, r2, suit_flag = hand_type[0], hand_type[1], hand_type[2]
    i1, i2 = _rank_index(r1), _rank_index(r2)
    # r1 siempre es el rango más fuerte (índice menor) por construcción de all_hand_types
    if suit_flag == "s":
        return (i1, i2)  # arriba de la diagonal: fila=rango fuerte, col=rango débil
    else:
        return (i2, i1)  # abajo de la diagonal: espejado


def expand_to_combos(hand_type: str) -> list[tuple[str, str]]:
    """
    Expande un tipo de mano a sus combos exactos con cartas concretas.
    AA -> 6 combos, AKs -> 4 combos, AKo -> 12 combos.
    NO aplica remoción de cartas todavía (eso es responsabilidad del
    paso 2 del pipeline, en state.py) — acá se devuelve el universo
    teórico completo del tipo.
    """
    validate_hand_type(hand_type)
    if is_pair(hand_type):
        rank = hand_type[0]
        cards = [rank + s for s in SUITS]
        return list(combinations(cards, 2))  # C(4,2) = 6

    r1, r2, suit_flag = hand_type[0], hand_type[1], hand_type[2]
    if suit_flag == "s":
        return [(r1 + s, r2 + s) for s in SUITS]  # 4 combos, mismo palo
    else:
        return [
            (r1 + s1, r2 + s2)
            for s1, s2 in product(SUITS, SUITS)
            if s1 != s2
        ]  # 16 - 4 = 12 combos


def hand_type_from_combo(card1: str, card2: str) -> str:
    """Función inversa: dado un combo concreto, qué tipo de mano es."""
    r1, s1 = card1[0], card1[1]
    r2, s2 = card2[0], card2[1]
    if r1 == r2:
        return r1 + r2
    # ordenar por fuerza (rango más fuerte primero)
    if _rank_index(r1) > _rank_index(r2):
        r1, r2 = r2, r1
        s1, s2 = s2, s1
    suit_flag = "s" if s1 == s2 else "o"
    return r1 + r2 + suit_flag


def combo_count(hand_type: str) -> int:
    validate_hand_type(hand_type)
    if is_pair(hand_type):
        return 6
    return 4 if hand_type.endswith("s") else 12


assert sum(combo_count(t) for t in ALL_HAND_TYPES) == 52 * 51 // 2, "el total de combos debe ser C(52,2)=1326"
