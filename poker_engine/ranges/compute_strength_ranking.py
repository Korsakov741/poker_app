"""
Script de precómputo (se corre UNA vez, no en cada arranque de la
app): calcula la equity heads-up de cada uno de los 169 tipos de
mano contra un rango 100% al azar, usando el propio motor del
Punto 1 — no se copia de ninguna tabla externa.

Por simetría de palos, alcanza con simular UN combo representativo
por tipo (ej. "As Ks" para AKs) — la equity contra un rango
completamente al azar es idéntica para cualquier combo del mismo
tipo.

Guarda el resultado en ranges/data/strength_ranking.json para que en
tiempo de ejecución sea instantáneo (no hay que resimular 169 tipos
cada vez que arranca la app).
"""
import json
import time
from pathlib import Path

from ..equity import calculate_equity, Range
from .hand_types import ALL_HAND_TYPES, expand_to_combos

OUTPUT_PATH = Path(__file__).parent / "data" / "strength_ranking.json"
SIMS_PER_TYPE = 10_000


def compute_ranking(sims: int = SIMS_PER_TYPE, seed_base: int = 1000) -> dict[str, float]:
    results: dict[str, float] = {}
    t0 = time.time()
    for i, hand_type in enumerate(ALL_HAND_TYPES):
        card1, card2 = expand_to_combos(hand_type)[0]  # un combo representativo alcanza
        res = calculate_equity(
            hero=(card1, card2),
            board=[],
            dead=[],
            opponent_ranges=[Range.random()],
            num_sims=sims,
            seed=seed_base + i,
        )
        results[hand_type] = round(res.players[0].equity_pct, 3)
        if (i + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/169 tipos calculados ({elapsed:.0f}s)")
    return results


def main():
    print(f"Calculando equity vs. rango al azar para los 169 tipos ({SIMS_PER_TYPE} sims c/u)...")
    t0 = time.time()
    ranking = compute_ranking()
    elapsed = time.time() - t0
    print(f"Listo en {elapsed:.1f}s")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(ranking, f, indent=2, sort_keys=True)
    print(f"Guardado en {OUTPUT_PATH}")

    # sanity check rápido: AA debe ser el #1, 72o debe estar cerca del fondo
    ordered = sorted(ranking.items(), key=lambda kv: -kv[1])
    print("\nTop 5:", ordered[:5])
    print("Bottom 5:", ordered[-5:])
    assert ordered[0][0] == "AA", f"AA debería ser el tipo más fuerte, salió {ordered[0][0]}"


if __name__ == "__main__":
    main()
