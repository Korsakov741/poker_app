"""
Punto de entrada público del Punto 17. Decide entre cálculo exacto y
la aproximación por campo reducido, según el tamaño del problema
(benchmarkeado empíricamente, no adivinado — ver README_punto17.md).

DECISIÓN DE DISEÑO A FLAGGEAR — cómo funciona la simplificación para
torneos grandes (el resumen técnico la pide pero no la especifica):

Con muchos jugadores restantes, calcular ICM exacto es carísimo
(pasamos de 0.4s con 14 jugadores a 105s con 25). La solución no es
"ignorar" a los jugadores lejanos — sería matemáticamente incorrecto,
porque cualquiera de ellos puede terminar cobrando un lugar pago y
eso afecta el $EV real de todos los demás. En cambio:

  1. Se mantienen INDIVIDUALES los jugadores relevantes: los de tu
     mesa actual + los N de stack más parecido al tuyo en todo el
     campo (son tus competidores directos más probables por un mismo
     lugar de cobro).
  2. El resto del campo se agrupa en varios "buckets" (jugadores
     ficticios) que suman las fichas reales de los jugadores que
     representan — así el total de fichas del torneo se preserva
     exacto, y la recursión sigue siendo matemáticamente válida (cada
     bucket compite como si fuera un jugador más).
  3. La cantidad de buckets se elige para que el campo reducido tenga
     SIEMPRE más entidades que lugares pagos (con margen) — si no,
     la recursión no podría repartir probabilidad de forma sensata
     entre todos los lugares que sí pagan algo.

LIMITACIÓN A ACEPTAR EXPLÍCITAMENTE: un bucket resuelve más grueso
que la realidad — en la vida real, cuando "alguien del bucket" cae
eliminado, en realidad cae UN jugador real de ese grupo y los demás
siguen jugando con sus fichas intactas; el modelo reducido, en
cambio, trata la eliminación del bucket entero como un solo evento.
Esto es una aproximación deliberada para hacer el cálculo viable, no
un intento de precisión perfecta — coherente con que todo en esta
app es informativo, nunca una instrucción exacta.
"""
from __future__ import annotations
from dataclasses import dataclass

from .model import compute_icm_exact, ICMResult

MAX_EXACT_ENTITIES = 14
MAX_EXACT_PAID_PLACES = 12


def _needs_reduction(n_players: int, n_paid_places: int) -> bool:
    return n_players > MAX_EXACT_ENTITIES or n_paid_places > MAX_EXACT_PAID_PLACES


def build_reduced_field(
    stacks: dict[str, float],
    hero_label: str,
    table_labels: set[str],
    n_paid_places: int,
    n_close: int = 5,
    buffer: int = 3,
) -> tuple[dict[str, float], dict]:
    """
    Devuelve (campo_reducido, detalle_de_buckets). Ver docstring del
    módulo para la justificación de cada paso.
    """
    if hero_label not in stacks:
        raise ValueError(f"hero_label {hero_label!r} no está en stacks")

    kept_labels = {hero_label} | set(table_labels)
    kept_labels &= set(stacks.keys())  # por si algún label de mesa ya no está (bustó)

    hero_stack = stacks[hero_label]
    others = {l: c for l, c in stacks.items() if l not in kept_labels}
    close_sorted = sorted(others.items(), key=lambda kv: abs(kv[1] - hero_stack))
    for label, _ in close_sorted[:n_close]:
        kept_labels.add(label)

    kept = {l: stacks[l] for l in kept_labels}
    rest = {l: c for l, c in stacks.items() if l not in kept_labels}

    detail = {"kept_individually": sorted(kept_labels), "n_rest_players": len(rest)}

    if not rest:
        return kept, detail

    n_buckets = max(1, (n_paid_places + buffer) - len(kept))
    n_buckets = min(n_buckets, len(rest))

    rest_sorted = sorted(rest.items(), key=lambda kv: -kv[1])
    bucket_chips = [0.0] * n_buckets
    bucket_members: list[list[str]] = [[] for _ in range(n_buckets)]
    for i, (label, chips) in enumerate(rest_sorted):
        b = i % n_buckets
        bucket_chips[b] += chips
        bucket_members[b].append(label)

    reduced = dict(kept)
    bucket_labels = []
    for i, chips in enumerate(bucket_chips):
        blabel = f"_resto_del_campo_{i + 1}"
        reduced[blabel] = chips
        bucket_labels.append(blabel)

    detail["n_buckets"] = n_buckets
    detail["bucket_composition"] = dict(zip(bucket_labels, bucket_members))
    return reduced, detail


def compute_icm(
    stacks: dict[str, float],
    payouts: list[float],
    hero_label: str | None = None,
    table_labels: set[str] | None = None,
) -> ICMResult:
    n_paid = sum(1 for p in payouts if p > 0)

    if not _needs_reduction(len(stacks), n_paid):
        ev = compute_icm_exact(stacks, payouts)
        return ICMResult(ev_dollars=ev, mode="exact", n_entities=len(stacks))

    if hero_label is None or table_labels is None:
        raise ValueError(
            f"El campo tiene {len(stacks)} jugadores y/o {n_paid} lugares pagos, "
            f"supera el techo de cálculo exacto ({MAX_EXACT_ENTITIES} jugadores / "
            f"{MAX_EXACT_PAID_PLACES} lugares pagos). Para la aproximación por "
            f"campo reducido hace falta indicar hero_label y table_labels."
        )

    reduced_stacks, detail = build_reduced_field(
        stacks, hero_label, table_labels, n_paid
    )
    payouts_for_reduced = (list(payouts) + [0.0] * len(reduced_stacks))[: len(reduced_stacks)]
    ev_reduced = compute_icm_exact(reduced_stacks, payouts_for_reduced)

    # solo reportamos $EV de entidades reales (no de los buckets, que son ficticios)
    ev_real = {l: v for l, v in ev_reduced.items() if not l.startswith("_resto_del_campo_")}
    for l in stacks:
        if l not in ev_real:
            ev_real[l] = None  # jugador lejano, no calculado individualmente — ver detail

    return ICMResult(
        ev_dollars=ev_real,
        mode="reduced_approximation",
        n_entities=len(reduced_stacks),
        detail=detail,
    )
