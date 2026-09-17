# Punto 15 — Combos que vencen mi mano según el board

## Uso

```python
from poker_engine.board import combos_beating_hero
from poker_engine.equity.ranges import Range

resultado = combos_beating_hero(
    hero=("Ah", "Kd"),
    board=["Ac", "7h", "2h"],
    dead=[],
    rival_range=Range.from_combos([("As","Ad",1.0), ("9h","8h",1.0)]),
)
print(resultado.summary())   # "1 de 2 combos posibles me ganan ahora mismo (X% ponderado)"
print(resultado.board_texture.overall)   # 'seco' | 'mojado'
```

Siempre reporta los **dos números** que pide el resumen técnico:
`raw_count_beating_me` / `raw_count_total` (conteo bruto) y
`weighted_pct_beating_me` (ponderado por peso — refleja el narrowing
del Punto 2). Son números distintos a propósito: si un combo que me
gana tiene peso bajo (poco probable según el Punto 2/3), el bruto no
lo sabe pero el ponderado sí — hay un test específico para esto
(`test_combos_pesos_distintos_afectan_ponderado_no_bruto`).

## Textura de board — decisión a flaggear

`board/texture.py` es un módulo separado, sin ninguna dependencia de
rangos ni del evaluador — solo mira las cartas del board, tal como
pide el resumen técnico para que el Punto 16 lo reuse después.

**"Seco" y "mojado" no tienen una definición matemática estándar en
teoría de póker** — es un concepto cualitativo incluso en los libros
de referencia. Armé una heurística propia y documentada:

- **Palos**: rainbow / two_tone (proyecto de color a 2 cartas) /
  wet_flush (3+ del mismo palo, color ya cerca) / monotone.
- **Escaleras**: cuento cuántos rangos del board caben dentro de
  ALGUNA ventana de 5 rangos consecutivos (contando el As como 1 y
  como 14, para la rueda A-2-3-4-5), como proporción del tamaño del
  board. **Bug real que encontré armando esto**: mi primera versión
  usaba un umbral fijo (`conectividad >= 4` para "muy conectado"),
  lo cual hacía IMPOSIBLE que un flop de 3 cartas llegara a esa
  categoría aunque estuviera perfectamente conectado (9-8-7). Lo
  corregí a un umbral proporcional al tamaño del board
  (`conectividad/len(board)`).
- **Pareado**: cualquier board con un rango repetido se cuenta como
  "mojado" en mi criterio — es discutible (un board pareado bajo y
  desconectado, tipo 2-2-7 rainbow, para mucha gente sigue siendo
  "seco" en el sentido de proyectos de color/escalera). Lo dejo así
  porque un par en el board sí agrega posibilidades reales de full
  house que no están en un board sin parear, pero es una decisión de
  criterio, no un hecho objetivo — ajustable si no te cierra.

## Por qué es exacto en cualquier calle (a diferencia del Punto 1)

No hay cartas por venir que simular — es una foto de la fuerza actual
de la mano contra el rango ya narroweado por el Punto 2. Por eso no
usa Monte Carlo en ningún caso, ni siquiera en el flop.

## Tests

`tests/test_board.py` — 11 tests: clasificación de textura en casos
representativos (monotone conectado, rainbow desconectado, pareado,
trío), los dos números del reporte de combos, divergencia entre
bruto y ponderado cuando los pesos difieren, empates clasificados
bien, rechazo explícito de board vacío (preflop no aplica acá), y
conteo exacto de combos posibles con `Range.random()` en el río
(45 cartas restantes → C(45,2) = 990 combos, verificado).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 1 (mismo evaluador de manos), Punto 2 (combos
  exactos con pesos, vía `Range`).
- **Lo consume directamente:** Punto 16 (detector de farol — usa
  tanto los combos que vencen mi mano como el módulo de textura).
