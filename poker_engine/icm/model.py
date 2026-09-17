"""
Punto 17 — Núcleo del modelo ICM (Malmuth-Harville).

P(jugador i termina 1° entre un conjunto S) = stack_i / suma(stacks de S)
P(jugador i termina en el lugar p, p>1, entre S) =
    suma sobre cada rival j en S: P(j termina 1° en S) * P(i termina en el lugar p-1 entre S-{j})

Recursión estándar, con memoización sobre (subconjunto, lugar) para
que sea rápida — sin memoización es factorialmente costosa.
"""
from __future__ import annotations
from dataclasses import dataclass


def _place_probabilities(
    remaining: tuple[tuple[str, float], ...], place: int, memo: dict
) -> dict[str, float]:
    key = (remaining, place)
    if key in memo:
        return memo[key]

    total = sum(c for _, c in remaining)
    if place == 1:
        result = {label: chips / total for label, chips in remaining}
    else:
        result = {label: 0.0 for label, _ in remaining}
        for idx, (label_j, chips_j) in enumerate(remaining):
            p_j = chips_j / total
            reduced = tuple(sorted(remaining[:idx] + remaining[idx + 1:]))
            sub = _place_probabilities(reduced, place - 1, memo)
            for label_i, prob_i in sub.items():
                result[label_i] += p_j * prob_i

    memo[key] = result
    return result


@dataclass
class ICMResult:
    ev_dollars: dict[str, float]
    mode: str  # 'exact' | 'reduced_approximation'
    n_entities: int   # cuántas entidades (jugadores reales + buckets) se usaron en la recursión
    detail: dict | None = None  # info extra (ej. composición de buckets) si mode == 'reduced_approximation'

    def total(self) -> float:
        return sum(self.ev_dollars.values())


def compute_icm_exact(stacks: dict[str, float], payouts: list[float]) -> dict[str, float]:
    """
    Cálculo EXACTO, sin aproximaciones. Usar directo solo cuando la
    cantidad de jugadores es manejable (ver icm.py para el techo).
    """
    active = {l: c for l, c in stacks.items() if c > 0}
    ev = {l: 0.0 for l in stacks}  # busted (stack<=0) quedan en 0.0
    if not active:
        return ev

    remaining = tuple(sorted(active.items()))
    memo: dict = {}
    n_places = min(len(payouts), len(remaining))

    for place in range(1, n_places + 1):
        payout = payouts[place - 1] if place - 1 < len(payouts) else 0.0
        if payout == 0.0:
            continue  # no aporta nada al EV, no hace falta calcular esa recursión
        probs = _place_probabilities(remaining, place, memo)
        for label, p in probs.items():
            ev[label] += p * payout

    return ev
