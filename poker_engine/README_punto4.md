# Punto 4 — Capa de teoría tipo GTO-lite

## Uso

```python
from poker_engine.gto_lite import (
    opening_range, vs_open_3bet_range, vs_3bet_continue_range,
    pot_odds, minimum_defense_frequency, bluff_to_value_ratio, implied_odds_adjusted_alpha,
    select_bluff_candidates,
)
from poker_engine.ranges.position_defaults import Position

# Submódulo A
rango = opening_range(Position.BUTTON, num_players=6, spr_category="medio")

# Submódulo B
alpha = pot_odds(bet=50, pot=100)
mdf = minimum_defense_frequency(bet=50, pot=100)
farol, valor = bluff_to_value_ratio(bet=50, pot=100)
ajuste = implied_odds_adjusted_alpha(bet=50, pot=100, villain_profile=perfil_rival)

# selección de farol
candidatos = select_bluff_candidates(mi_rango, board, dead=[], villain_range=rango_rival, top_n=10)
```

## Submódulo A — reemplaza el placeholder del Punto 2

Los % base por posición son los MISMOS que ya tenía el placeholder
del Punto 2 (10/15/25/40/30) — los "oficialicé" como referencia
deep-stack 9-max y les agregué las dos dimensiones que faltaban:

- **Tamaño de mesa**: cada jugador de menos que 9-max ensancha ~8%
  relativo (heurística propia). Probado: mesa más chica siempre da
  rango más ancho (`test_mesa_mas_chica_ensancha`).
- **Profundidad de stack** (usa la categoría de SPR del Punto 5):
  push/fold hasta 3× más ancho que deep — clásico de la teoría de
  push/fold, donde el fold equity domina.

**La BB no tiene "% de apertura"** — actúa último preflop, su
decisión real es defender/completar, no abrir. Lo dejé explícito con
un error claro en vez de inventar un número sin sentido
(`test_bb_no_tiene_porcentaje_de_apertura`).

3-bet range anclada en el 3-bet% poblacional del Punto 14 (~7%, no
una constante inventada). Vs-3bet-continue usa una retención del 35%
del rango de apertura original — constante propia, documentada como
heurística, no un valor de solver real.

## Submódulo B — las cuatro fórmulas de alpha

`pot_odds`, `minimum_defense_frequency`, `bluff_to_value_ratio` son
matemática directa de `alpha = apuesta/(bote+apuesta)` — sin
ambigüedad, verificadas con tests exactos.

**Recordatorio del principio no-negociable #1, explícito en el
código, no solo en un comentario suelto:** MDF y el ratio farol-valor
son frecuencias de RANGO AGREGADO, nunca una instrucción sobre esta
mano puntual — está en el docstring de cada función que las
devuelve.

`implied_odds_adjusted_alpha` es la única de las cuatro que depende
del Punto 3: un rival más pasivo baja el alpha efectivo (mejores
implied odds asumidas). Probado con un caso real construido con el
Punto 6 (`test_implied_odds_rival_pasivo_baja_el_alpha`).

## Selección de manos-farol

Combina dos señales por combo de mi propio rango: **bloqueo**
(cuánto del rango ponderado del rival bloquea esta combinación —
reusa directamente el sistema de pesos del Punto 2) y **falta de
showdown value** (normalizado contra el rango teórico completo de
scores de treys, 1 a 7462 — simplificación documentada: no contra el
rango real alcanzable en ESTE board específico, que sería más caro
de calcular para poco beneficio práctico en un ranking relativo).

Validado con un caso construido a mano: A2s contra un rango rival
que incluye As-Ah bloquea exactamente el 50% del peso del rival (1.0
de 2.0 total) — coincide con el cálculo manual antes de fijar el
test.

## Tests

`tests/test_gto_lite.py` — 17 tests: mesa más chica ensancha, push/fold
mucho más ancho que deep, orden por posición se mantiene, la BB
falla explícito, nunca supera 100%, 3-bet y vs-3bet más angostas que
la apertura propia; las tres fórmulas de alpha exactas, implied odds
sin perfil no ajusta nada, implied odds con rival pasivo real baja el
alpha; selección de farol con y sin blocker, respeta el límite
`top_n`, y rechaza preflop explícito (sin board no hay fuerza actual
que evaluar).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 2 (formato de rango), Punto 1 (evaluador para
  showdown value), Punto 5 (SPR determina la tabla), Punto 14
  (valores poblacionales concretos).
- **Lo consumen directamente:** Punto 2 (rango preflop inicial — este
  módulo reemplaza su placeholder), Punto 11 (línea GTO de la mezcla
  — automático, sin tocar código de Punto 11), Punto 16 (umbral
  mínimo vía `pot_odds`/`bluff_to_value_ratio`, y selección de farol
  reusada directo, sin duplicar).
