"""
"ICM penalty": el número concreto que van a consumir los
amortiguadores de los puntos 11 y 8. Compara $EV si gano vs. $EV si
pierdo (recalculando el modelo COMPLETO en ambos escenarios, tal como
pide el resumen técnico — nunca cEV simple), contra un equivalente
"ingenuo" que trataría las fichas como si valieran una tasa constante
en dólares. La diferencia entre ambos ES la presión de ICM.

Se muestra siempre como número explícito — nunca se aplica en
silencio, tal como pide el resumen técnico.
"""
from __future__ import annotations
from dataclasses import dataclass

from .session import SessionMode
from .icm import compute_icm


@dataclass
class ICMPenaltyResult:
    applies: bool                          # False en cash game — ICM no aplica
    mode: str | None = None                  # 'exact' | 'reduced_approximation' | None (cash)
    ev_before_dollars: float | None = None
    ev_after_real_dollars: float | None = None       # $EV real, ponderado por p_win, con ICM completo
    naive_linear_ev_dollars: float | None = None      # equivalente ingenuo (fichas = $ a tasa constante)
    icm_penalty_dollars: float | None = None           # naive - real (positivo = ICM castiga más de lo que cEV sugiere)


def icm_penalty_for_play(
    session: SessionMode,
    villain_label: str,
    bet_amount: float,
    p_win: float,
) -> ICMPenaltyResult:
    if not session.is_tournament:
        return ICMPenaltyResult(applies=False)

    if not (0.0 <= p_win <= 1.0):
        raise ValueError("p_win debe estar entre 0 y 1")
    if bet_amount <= 0:
        raise ValueError("bet_amount debe ser positivo")

    ctx = session.tournament
    hero = ctx.hero_label
    stacks = ctx.stacks

    if villain_label not in stacks:
        raise ValueError(f"villain_label {villain_label!r} no está en los stacks de la sesión")
    if hero not in stacks:
        raise ValueError(f"hero_label {hero!r} no está en los stacks de la sesión")

    res_before = compute_icm(stacks, ctx.payouts, hero_label=hero, table_labels=ctx.table_labels)
    ev_before = res_before.ev_dollars[hero]

    stacks_win = dict(stacks)
    stacks_win[hero] = stacks[hero] + bet_amount
    stacks_win[villain_label] = max(0.0, stacks[villain_label] - bet_amount)

    stacks_lose = dict(stacks)
    stacks_lose[hero] = max(0.0, stacks[hero] - bet_amount)
    stacks_lose[villain_label] = stacks[villain_label] + bet_amount

    res_win = compute_icm(stacks_win, ctx.payouts, hero_label=hero, table_labels=ctx.table_labels)
    res_lose = compute_icm(stacks_lose, ctx.payouts, hero_label=hero, table_labels=ctx.table_labels)

    ev_win = res_win.ev_dollars[hero]
    ev_lose = res_lose.ev_dollars[hero]
    ev_after_real = p_win * ev_win + (1 - p_win) * ev_lose

    total_chips = sum(stacks.values())
    total_prize = sum(ctx.payouts)
    dollar_per_chip = (total_prize / total_chips) if total_chips > 0 else 0.0
    chip_ev_delta = p_win * bet_amount - (1 - p_win) * bet_amount
    naive_ev_after = ev_before + chip_ev_delta * dollar_per_chip

    icm_penalty = naive_ev_after - ev_after_real

    return ICMPenaltyResult(
        applies=True,
        mode=res_before.mode,
        ev_before_dollars=ev_before,
        ev_after_real_dollars=ev_after_real,
        naive_linear_ev_dollars=naive_ev_after,
        icm_penalty_dollars=icm_penalty,
    )
