"""
Enumeración exacta — usada en turn y río (Punto 1).

En turn (4 cartas de board conocidas) hay que promediar sobre todas
las cartas de río posibles Y sobre todos los combos válidos de cada
rival, ponderando por el peso de cada combo dentro de su rango
(los combos NO tienen probabilidades a priori iguales entre sí; el
peso del Punto 2 ya codifica cuánto pertenece cada combo al rango).
En río (5 cartas conocidas) no hay más cartas por enumerar: solo se
promedia sobre los combos válidos de cada rival.

DECISIÓN DE DISEÑO A FLAGGEAR: la enumeración conjunta (producto
cartesiano de los combos válidos de TODOS los rivales, más la carta
de río si aplica) puede explotar combinatoriamente con muchos
rivales y rangos anchos (ej. 3 rivales x 40 combos x 44 cartas de río
≈ 2.8M evaluaciones — rápido; pero 5 rivales x 60 combos ya se va a
cientos de millones). Puse un techo (`MAX_JOINT_SPACE`) — si el
espacio conjunto lo supera, la función lanza `SpaceTooLargeError` en
vez de colgarse, y el motor principal (engine.py) hace fallback a
Monte Carlo con muchas iteraciones, dejándolo explícito en el
resultado (`mode='monte_carlo_fallback'`). Esto es exactamente el
mismo patrón de diseño que ya usaste vos en el Punto 17 para torneos
grandes: simplificar antes de que el cálculo completo se vuelva
inviable, no como optimización tardía.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product

from .cards import FULL_DECK, to_treys
from .ranges import Range, Combo
from . import evaluator

MAX_JOINT_SPACE = 3_000_000


class SpaceTooLargeError(Exception):
    pass


@dataclass
class ExactOutcome:
    outright_win_weight: list[float]  # peso donde ganó solo, sin empate
    tie_event_weight: list[float]     # peso donde participó de un empate (informativo, sin dividir)
    equity_weight: list[float]        # crédito repartido correctamente (peso completo si gana solo, peso/k si empate a k)
    total_weight: float


def run_exact(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    opponent_ranges: list[Range],
) -> ExactOutcome:
    if len(board) not in (4, 5):
        raise ValueError("run_exact solo aplica a turn (4 cartas) o río (5 cartas)")

    base_used = set(hero) | set(board) | set(dead)
    need_river = len(board) == 4
    num_river_options = (len(FULL_DECK) - len(base_used)) if need_river else 1

    # Paso 1: ESTIMAR el tamaño sin materializar combos (barato incluso
    # para rangos random, que si no habría que generar cientos de
    # objetos Combo solo para terminar descartando todo el cálculo).
    quick_counts = [rng_obj.estimated_valid_count(base_used) for rng_obj in opponent_ranges]
    for i, count in enumerate(quick_counts):
        if count == 0:
            raise RuntimeError(
                f"El rival #{i+1} no tiene ningún combo válido dado el "
                f"board/hero/dead cards actuales."
            )
    estimated = num_river_options
    for count in quick_counts:
        estimated *= count
    if estimated > MAX_JOINT_SPACE:
        raise SpaceTooLargeError(
            f"Espacio conjunto estimado ({estimated:,}) supera el techo "
            f"({MAX_JOINT_SPACE:,}). Fallback a Monte Carlo recomendado."
        )

    # Paso 2: recién acá materializamos las listas reales (ya sabemos
    # que el volumen es manejable).
    opponent_valid = [rng_obj.valid_combos(base_used) for rng_obj in opponent_ranges]
    river_candidates = [c for c in FULL_DECK if c not in base_used] if need_river else [None]

    n_players = 1 + len(opponent_ranges)
    outright_win_weight = [0.0] * n_players
    tie_event_weight = [0.0] * n_players
    equity_weight = [0.0] * n_players
    total_weight = 0.0

    hero_t = [to_treys(c) for c in hero]

    # Producto cartesiano de: combo elegido por cada rival x carta de río (si aplica).
    for combo_assignment in product(*opponent_valid):
        # Remoción cruzada entre rivales dentro de esta combinación puntual.
        used_cards = set(base_used)
        conflict = False
        for combo in combo_assignment:
            if combo.card1 in used_cards or combo.card2 in used_cards:
                conflict = True
                break
            used_cards.add(combo.card1)
            used_cards.add(combo.card2)
        if conflict:
            continue  # combinación inválida (dos rivales compartirían una carta)

        weight_product = 1.0
        for combo in combo_assignment:
            weight_product *= combo.weight
        if weight_product <= 0:
            continue

        if need_river:
            valid_rivers = [r for r in river_candidates if r not in used_cards]
        else:
            valid_rivers = [None]

        for river_card in valid_rivers:
            full_board_str = board + ([river_card] if river_card else [])
            full_board_t = [to_treys(c) for c in full_board_str]

            hero_score = evaluator.score(full_board_t, hero_t)
            opp_scores = [
                evaluator.score(full_board_t, [to_treys(c) for c in combo.cards()])
                for combo in combo_assignment
            ]
            all_scores = [hero_score] + opp_scores
            best = min(all_scores)
            winners = [i for i, s in enumerate(all_scores) if s == best]

            total_weight += weight_product
            if len(winners) == 1:
                outright_win_weight[winners[0]] += weight_product
                equity_weight[winners[0]] += weight_product
            else:
                share = weight_product / len(winners)
                for w in winners:
                    tie_event_weight[w] += weight_product
                    equity_weight[w] += share

    if total_weight == 0:
        raise RuntimeError(
            "No se encontró ninguna combinación válida (todos los combos de "
            "los rivales chocan entre sí dado el board actual). Revisar rangos."
        )

    return ExactOutcome(
        outright_win_weight=outright_win_weight,
        tie_event_weight=tie_event_weight,
        equity_weight=equity_weight,
        total_weight=total_weight,
    )
