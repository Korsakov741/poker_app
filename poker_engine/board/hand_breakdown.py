"""
Extensión del Punto 15 — no cambia nada de `combos_beating_hero`
(que sigue exactamente igual, usado en todos lados tal cual estaba).
Esto es una vista COMPLEMENTARIA: en vez de un solo % de equity, dice
QUÉ TIPO de mano (el "canto": color, escalera, trío...) tiene hero
ahora mismo, qué tipos de mano son más probables en el rango del
rival, y qué cartas por venir podrían completarle algo peligroso.

Todo esto es fuerza ACTUAL contra el board ya repartido (como el
Punto 15), no equity a futuro — por eso no hace falta Monte Carlo acá
tampoco, salvo en "cartas peligrosas", donde sí hay que probar cada
carta que podría salir (pero es barato: nada de simulación, solo
recorrer el rango una vez por cada carta candidata).
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..equity.cards import to_treys_many, FULL_DECK
from ..equity import evaluator
from ..equity.ranges import Range

# nombres en español de las 9 categorías de treys (1=mejor..9=peor)
_CLASS_NAMES_ES = {
    1: "Escalera de color",
    2: "Póker",
    3: "Full",
    4: "Color",
    5: "Escalera",
    6: "Trío",
    7: "Doble par",
    8: "Par",
    9: "Carta alta",
}


@dataclass
class HandTypeBreakdown:
    hero_hand_type: str                      # ej. "Color" — lo que hero TIENE ahora, directo
    villain_top_types: list[tuple[str, float]]  # ej. [("Par", 45.2), ("Color", 20.1), ("Trío", 15.0)] — top 3, ya ordenado
    danger_cards: list[str] = field(default_factory=list)  # ej. ["Cualquier ♥ más completa color en su rango (18% de sus combos)"]


def classify_hero_hand(hero: tuple[str, str], board: list[str]) -> str:
    board_t = to_treys_many(board)
    hero_t = to_treys_many(hero)
    score = evaluator.score(board_t, hero_t)
    return _CLASS_NAMES_ES[evaluator.rank_class(score)]


def villain_type_breakdown(
    board: list[str],
    dead: list[str],
    villain_range: Range,
    hero: tuple[str, str] | None = None,
    top_n: int = 3,
) -> list[tuple[str, float]]:
    """Top N tipos de mano más probables en el rango del rival, por % de peso."""
    excluded = set(board) | set(dead) | (set(hero) if hero else set())
    combos = villain_range.valid_combos(excluded)
    if not combos:
        return []

    board_t = to_treys_many(board)
    weight_by_class: dict[int, float] = {}
    total_weight = 0.0
    for combo in combos:
        combo_t = to_treys_many(combo.cards())
        cls = evaluator.rank_class(evaluator.score(board_t, combo_t))
        weight_by_class[cls] = weight_by_class.get(cls, 0.0) + combo.weight
        total_weight += combo.weight

    if total_weight <= 0:
        return []

    ranked = sorted(weight_by_class.items(), key=lambda kv: kv[1], reverse=True)
    return [
        (_CLASS_NAMES_ES[cls], round(w / total_weight * 100, 1))
        for cls, w in ranked[:top_n]
    ]


# clase 4 (Color) o mejor cuenta como "peligroso" para esta alerta —
# es una elección explícita, no una regla estándar: el umbral es
# ajustable acá si en algún momento no convence.
_DANGER_CLASS_THRESHOLD = 4


def find_danger_cards(
    board: list[str],
    dead: list[str],
    villain_range: Range,
    hero: tuple[str, str] | None = None,
) -> list[str]:
    """
    Para cada palo y rango que todavía puede salir, mide si agregar
    ESA carta al board sube mucho la fracción del rango del rival que
    cae en color/escalera o mejor (comparado con el board actual).
    Devuelve frases cortas y listas para mostrar, no una lista exhaustiva
    carta por carta — agrupa por palo/rango cuando el efecto es el mismo.
    """
    if len(board) not in (3, 4):
        return []  # en el río no hay más cartas por venir; preflop no aplica

    excluded = set(board) | set(dead) | (set(hero) if hero else set())
    combos = villain_range.valid_combos(excluded)
    if not combos:
        return []

    board_t_now = to_treys_many(board)
    baseline_dangerous = 0.0
    total_weight = 0.0
    for combo in combos:
        combo_t = to_treys_many(combo.cards())
        cls = evaluator.rank_class(evaluator.score(board_t_now, combo_t))
        total_weight += combo.weight
        if cls <= _DANGER_CLASS_THRESHOLD:
            baseline_dangerous += combo.weight
    if total_weight <= 0:
        return []
    baseline_pct = baseline_dangerous / total_weight * 100

    remaining = [c for c in FULL_DECK if c not in excluded]

    # agrupar candidatas por PALO (para el color) y por RANGO (para la escalera),
    # probando una carta representativa de cada grupo — si esa sube mucho el
    # peligro, todo el grupo comparte el mismo efecto de palo/rango
    suits_seen = {c[1] for c in remaining}
    ranks_seen = {c[0] for c in remaining}

    results: list[tuple[str, float]] = []  # (frase, pct_peligroso_si_sale)

    for suit in suits_seen:
        sample = next(c for c in remaining if c[1] == suit)
        board_t_next = to_treys_many(board + [sample])
        w_dangerous = 0.0
        w_total = 0.0
        for combo in combos:
            if sample in combo.cards():
                continue
            combo_t = to_treys_many(combo.cards())
            cls = evaluator.rank_class(evaluator.score(board_t_next, combo_t))
            w_total += combo.weight
            if cls <= _DANGER_CLASS_THRESHOLD:
                w_dangerous += combo.weight
        if w_total <= 0:
            continue
        pct = w_dangerous / w_total * 100
        if pct - baseline_pct >= 10:  # solo avisar si sube de forma notoria
            suit_symbol = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}[suit]
            results.append((f"Cualquier {suit_symbol} más sube su rango peligroso a {pct:.0f}%", pct))

    for rank in ranks_seen:
        sample = next(c for c in remaining if c[0] == rank)
        board_t_next = to_treys_many(board + [sample])
        w_dangerous = 0.0
        w_total = 0.0
        for combo in combos:
            if sample in combo.cards():
                continue
            combo_t = to_treys_many(combo.cards())
            cls = evaluator.rank_class(evaluator.score(board_t_next, combo_t))
            w_total += combo.weight
            if cls <= _DANGER_CLASS_THRESHOLD:
                w_dangerous += combo.weight
        if w_total <= 0:
            continue
        pct = w_dangerous / w_total * 100
        if pct - baseline_pct >= 10:
            results.append((f"Un {rank} más sube su rango peligroso a {pct:.0f}%", pct))

    results.sort(key=lambda x: x[1], reverse=True)
    return [phrase for phrase, _ in results[:3]]  # compacto: como mucho 3 avisos


def hand_type_breakdown(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    villain_range: Range,
) -> HandTypeBreakdown:
    return HandTypeBreakdown(
        hero_hand_type=classify_hero_hand(hero, board),
        villain_top_types=villain_type_breakdown(board, dead, villain_range, hero),
        danger_cards=find_danger_cards(board, dead, villain_range, hero),
    )
