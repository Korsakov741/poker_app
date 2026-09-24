"""
Punto 1 — Motor de equity avanzado. Punto de entrada público.

Entrada: mi mano, board, cartas muertas, rango de cada rival (con
pesos, o Range.random() como placeholder mientras el Punto 2 no
exista).
Salida: equity de cada jugador (yo primero, después cada rival en
orden), con:
  - Monte Carlo (preflop/flop): reportado como RANGO de confianza
    (ej. "62.4%–63.6%"), nunca como número puntual.
  - Enumeración exacta (turn/río): reportado como número exacto, sin
    rango, porque no hay muestreo de por medio.

Ningún resultado de este módulo es una instrucción — son puntos de
partida informativos que consume el Punto 8 más adelante junto con el
resto de las capas.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from .cards import check_no_duplicates
from .ranges import Range
from . import montecarlo, exact

Z_95 = 1.959963984540054  # z para intervalo de confianza del 95%

DEFAULT_MC_SIMS = 30_000
FALLBACK_MC_SIMS = 10_000  # cuando el espacio exacto es demasiado grande — Opción A: bajado de 20.000 a 10.000 para más velocidad en esos casos puntuales (varios rivales de rango ancho en turn/río), a costa de un poco de precisión solo ahí


@dataclass
class PlayerEquity:
    label: str              # "hero" o "rival_1", "rival_2", ...
    win_pct: float           # % de manos ganadas en solitario
    tie_pct: float           # % de manos donde participó de un empate (informativo)
    equity_pct: float        # equity real (gana + parte proporcional de empates)
    ci_low: float | None = None   # solo en modo monte_carlo
    ci_high: float | None = None  # solo en modo monte_carlo


@dataclass
class EquityResult:
    mode: str                 # 'monte_carlo' | 'exact' | 'monte_carlo_fallback'
    street: str                # 'preflop' | 'flop' | 'turn' | 'river'
    num_iterations: int
    players: list[PlayerEquity]

    def total_equity_pct(self) -> float:
        """Debe dar ~100% siempre — invariante de sanity check."""
        return sum(p.equity_pct for p in self.players)


def _street_from_board(board: list[str]) -> str:
    n = len(board)
    if n == 0:
        return "preflop"
    if n == 3:
        return "flop"
    if n == 4:
        return "turn"
    if n == 5:
        return "river"
    raise ValueError(f"Board con {n} cartas no es válido (esperado 0, 3, 4 o 5)")


def _labels(n_opponents: int) -> list[str]:
    return ["hero"] + [f"rival_{i+1}" for i in range(n_opponents)]


def _from_monte_carlo(outcome: montecarlo.SimOutcome, labels: list[str]) -> list[PlayerEquity]:
    players = []
    n = outcome.total
    for i, label in enumerate(labels):
        mean = outcome.equity_sum[i] / n
        # Var(X) = E[X^2] - E[X]^2, error estándar de la media = sqrt(Var/n)
        mean_sq = outcome.equity_sumsq[i] / n
        variance = max(mean_sq - mean * mean, 0.0)
        se = math.sqrt(variance / n)
        ci_low = max(0.0, mean - Z_95 * se) * 100
        ci_high = min(1.0, mean + Z_95 * se) * 100
        players.append(
            PlayerEquity(
                label=label,
                win_pct=outcome.outright_wins[i] / n * 100,
                tie_pct=outcome.tie_events[i] / n * 100,
                equity_pct=mean * 100,
                ci_low=round(ci_low, 1),
                ci_high=round(ci_high, 1),
            )
        )
    return players


def _from_exact(outcome: exact.ExactOutcome, labels: list[str]) -> list[PlayerEquity]:
    players = []
    tw = outcome.total_weight
    for i, label in enumerate(labels):
        players.append(
            PlayerEquity(
                label=label,
                win_pct=outcome.outright_win_weight[i] / tw * 100,
                tie_pct=outcome.tie_event_weight[i] / tw * 100,
                equity_pct=outcome.equity_weight[i] / tw * 100,
                ci_low=None,
                ci_high=None,
            )
        )
    return players


def calculate_equity(
    hero: tuple[str, str],
    board: list[str],
    dead: list[str],
    opponent_ranges: list[Range],
    num_sims: int = DEFAULT_MC_SIMS,
    seed: int | None = None,
) -> EquityResult:
    check_no_duplicates(hero, board, dead)
    if not opponent_ranges:
        raise ValueError("Se necesita al menos un rango de rival (o Range.random())")

    street = _street_from_board(board)
    labels = _labels(len(opponent_ranges))

    if street in ("preflop", "flop"):
        outcome = montecarlo.run_monte_carlo(hero, board, dead, opponent_ranges, num_sims, seed)
        return EquityResult(
            mode="monte_carlo",
            street=street,
            num_iterations=outcome.total,
            players=_from_monte_carlo(outcome, labels),
        )

    # turn / river -> intento exacto, con fallback a Monte Carlo si el
    # espacio conjunto es demasiado grande (ver docstring de exact.py)
    try:
        outcome = exact.run_exact(hero, board, dead, opponent_ranges)
        return EquityResult(
            mode="exact",
            street=street,
            num_iterations=1,  # no aplica "iteraciones", es determinístico
            players=_from_exact(outcome, labels),
        )
    except exact.SpaceTooLargeError:
        mc_outcome = montecarlo.run_monte_carlo(
            hero, board, dead, opponent_ranges, FALLBACK_MC_SIMS, seed
        )
        return EquityResult(
            mode="monte_carlo_fallback",
            street=street,
            num_iterations=mc_outcome.total,
            players=_from_monte_carlo(mc_outcome, labels),
        )
