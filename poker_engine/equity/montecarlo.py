"""
Simulación Monte Carlo — usada en preflop y flop (Punto 1).

DECISIÓN DE DISEÑO A FLAGGEAR (el resumen técnico no especifica el
algoritmo de muestreo, solo el requisito): para repartir una mano a
cada rival en cada simulación respetando SU rango y la remoción de
cartas, hay dos formas estándar:

  (a) Rechazo conjunto: samplear los N rivales de forma independiente
      y, si hay choque de cartas entre cualquiera de ellos, descartar
      TODA la simulación y reintentar.
  (b) Filtrado secuencial: procesar los rivales en orden, y para cada
      uno filtrar su rango a los combos que no chocan con lo ya
      repartido, renormalizar los pesos restantes, y samplear de ahí.

Elegí (b) — filtrado secuencial — porque (a) puede degradar mucho el
rendimiento cuando varios rivales tienen rangos muy angostos y
superpuestos (ej. dos rivales ambos con "solo AA": el rechazo
conjunto puede reintentar miles de veces). (b) nunca falla y es
más rápido, a costa de una dependencia teórica mínima del orden de
procesamiento cuando los rangos se superponen fuertemente — en la
práctica, con los tamaños de rango reales de póker, el sesgo
introducido es despreciable comparado con el margen de error propio
del muestreo Monte Carlo. Si en algún momento esto importa (rangos
extremadamente angostos y superpuestos), se puede promediar sobre
varios órdenes de procesamiento aleatorios — lo dejo como mejora
futura documentada, no bloqueante hoy.
"""
from __future__ import annotations
import random
from dataclasses import dataclass

from .cards import FULL_DECK, to_treys
from .ranges import Range, Combo
from . import evaluator


@dataclass
class SimOutcome:
    outright_wins: list[int]   # ganó solo, sin empate
    tie_events: list[int]      # participó de un empate (informativo, sin dividir)
    equity_sum: list[float]    # crédito de equity correctamente repartido (1 si gana solo, 1/k si empate a k)
    equity_sumsq: list[float]  # suma de (crédito)^2 por jugador, para calcular el intervalo de confianza
    total: int


def run_monte_carlo(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    opponent_ranges: list[Range],
    num_sims: int = 30_000,
    seed: int | None = None,
) -> SimOutcome:
    rng = random.Random(seed)
    n_players = 1 + len(opponent_ranges)
    outright_wins = [0] * n_players
    tie_events = [0] * n_players
    equity_sum = [0.0] * n_players
    equity_sumsq = [0.0] * n_players

    hero_t_base = [to_treys(c) for c in hero]
    board_t_base = [to_treys(c) for c in board]

    for _ in range(num_sims):
        used: set[str] = set(hero) | set(board) | set(dead)
        opp_hands_str: list[tuple[str, str]] = []

        for rng_obj in opponent_ranges:
            combo = rng_obj.sample_one(used, rng)
            opp_hands_str.append(combo.cards())
            used.add(combo.card1)
            used.add(combo.card2)

        remaining_deck = [c for c in FULL_DECK if c not in used]
        rng.shuffle(remaining_deck)
        needed = 5 - len(board)
        full_board_str = board + remaining_deck[:needed]
        full_board_t = [to_treys(c) for c in full_board_str]

        hero_score = evaluator.score(full_board_t, hero_t_base)
        opp_scores = [
            evaluator.score(full_board_t, [to_treys(c) for c in oh])
            for oh in opp_hands_str
        ]
        all_scores = [hero_score] + opp_scores
        best = min(all_scores)
        winners = [i for i, s in enumerate(all_scores) if s == best]

        if len(winners) == 1:
            outright_wins[winners[0]] += 1
            equity_sum[winners[0]] += 1.0
            equity_sumsq[winners[0]] += 1.0  # 1.0**2
        else:
            share = 1.0 / len(winners)
            for w in winners:
                tie_events[w] += 1
                equity_sum[w] += share
                equity_sumsq[w] += share * share
        # los que no ganaron ni empataron aportan 0 a equity_sum/equity_sumsq (no-op)

    return SimOutcome(
        outright_wins=outright_wins,
        tie_events=tie_events,
        equity_sum=equity_sum,
        equity_sumsq=equity_sumsq,
        total=num_sims,
    )
