# Punto 2 — Rangos de rivales (matriz 13x13)

## Uso

```python
from poker_engine.ranges import (
    RangeState, HandTypeMatrix, NarrowAction,
    Position, placeholder_opening_range, recompute_equity,
)

# --- Tres formas de entrada manual ---
m1 = HandTypeMatrix()                      # (a) pintar en la grilla
m1.set_weight("AKs", 1.0)
m1.set_weight("QQ", 0.5)

m2 = HandTypeMatrix.from_top_percent(15)    # (b) top % (equity real, calculada por nosotros)

m3 = HandTypeMatrix.from_notation("22+, A9s+, KJo+, AKo:0.5")  # (c) notación abreviada

# --- Pipeline de 4 pasos para un rival ---
rs = RangeState("villain_1")
rs.initialize_preflop(placeholder_opening_range(Position.BUTTON), reason="apertura BTN")  # paso 1
rs.apply_action_narrowing(NarrowAction.RAISE, street_label="flop")                          # pasos 3+4

# --- Ajuste manual (dispara recálculo, nunca queda aislado) ---
rs.apply_manual_adjustment(HandTypeMatrix.from_notation("AA,KK,QQ"), street_label="flop",
                             reason="ajusté a mano porque no creo el narrowing genérico acá")

# --- Puente al Punto 1 (paso 2 + equity, siempre fresco, sin caché) ---
resultado = recompute_equity(
    hero=("Kd", "Kc"), board=["Ks", "7h", "2c"], dead=[],
    range_states=[rs],
)
```

## Los tres métodos de entrada manual — los tres completos, ninguno placeholder

- **Pintar en la grilla**: `matrix.set_weight(tipo, peso)` / `matrix.paint({...})`.
- **Top %**: `HandTypeMatrix.from_top_percent(pct)`. El ranking de
  fuerza detrás NO es una tabla copiada de ningún lado — la
  calculamos nosotros mismos corriendo el motor del Punto 1 (equity
  real heads-up vs. mano al azar) para los 169 tipos. Ver
  `compute_strength_ranking.py` y `data/strength_ranking.json`. El %
  se mide en **combos reales**, no en casilleros de la grilla (AA
  pesa 6 combos, AKo pesa 12 — un "top 15%" que contara casilleros
  en vez de combos estaría mal).
- **Notación abreviada**: `HandTypeMatrix.from_notation("22+, A9s+, KJo+")`.
  Soporta `+`, rangos `A-B` con mismo tope, y peso opcional por token
  (`AKo:0.5`). Documenté explícitamente qué NO soporta (rangos de
  conectores con distinto tope, tipo `98s-54s`) — tira error claro en
  vez de adivinar.

## Lo que hay que flaggear explícitamente (dos placeholders, marcados en el código)

1. **`position_defaults.py` — placeholder del Punto 4.** El resumen
   técnico dice que el rango preflop inicial por posición es "input
   externo, del punto 4", que todavía no existe. Puse una función
   `placeholder_opening_range(posicion)` con un % genérico por
   posición (EARLY 10%, BUTTON 40%, etc.) sin considerar profundidad
   de stack, cantidad de jugadores ni acción previa — eso es trabajo
   real del Punto 4. Está marcado con un docstring bien visible y
   diseñado para reemplazarse sin tocar el resto del Punto 2.

2. **`narrowing.py` — placeholder del Punto 3.** El resumen técnico
   autoriza explícitamente "heurísticas genéricas por defecto" acá
   ("una subida reduce al tercio superior de manos" es literal del
   documento). Implementé: RAISE→top 33%, BET→top 50%, CALL→top 70%
   de la masa de combos actual, corte duro sin suavizado. **Limitación
   que encontré armando esto y que el resumen no menciona:** el
   ranking usado para ordenar "qué es el tercio superior" es el
   ranking PREFLOP (equity vs. azar). Post-flop ese ranking ya no es
   exacto — no sabe leer el board (76s puede ser la mejor mano
   posible en un board 5-6-7 y este módulo lo sigue tratando como
   "mano floja"). Es una simplificación consciente, documentada en el
   docstring, que el Punto 3 real va a resolver con datos de
   comportamiento observado en vez de esta tabla estática.

## Los 4 pasos del pipeline, tal como los pide el resumen técnico

1. **Rango preflop inicial por posición** → `RangeState.initialize_preflop()`
2. **Filtrado por bloqueo de cartas** → se aplica al vuelo en
   `to_point1_range()`/`recompute_equity()`, NO se guarda como entrada
   de historial separada. Decisión de diseño: la remoción depende de
   qué cartas están visibles en el momento de la consulta, no es una
   propiedad de la matriz tipo-por-tipo que tenga sentido "congelar"
   en una calle — se recalcula siempre fresca.
3. **Narrowing por acción** → `RangeState.apply_action_narrowing()`
4. **Renormalización** → `HandTypeMatrix.scale_max_to_one()`, aplicada
   automáticamente después de cualquier narrowing o ajuste manual.
   Interpretación elegida para "renormalizar" (el resumen no la
   define matemáticamente): reescalar para que el peso máximo vuelva
   a ser 1.0, así el tipo de mano más fuerte que sobrevive el filtro
   siempre queda tratado como "plenamente en el rango" en vez de
   arrastrar un peso decreciente arbitrario tras varios filtros
   sucesivos.

## Historial por calle (para el futuro Punto 12)

`RangeState.history` es una lista que **nunca se sobrescribe** — cada
paso del pipeline agrega una entrada nueva (`StreetSnapshot`) con la
matriz completa de ese momento, la calle, y la razón del cambio.
`RangeState.history_summary()` da una vista legible para debugging.

## Recálculo inmediato de equity (principio no-negociable #1)

`recompute_equity()` no cachea nada — cada llamada expande los
`RangeState` actuales a combos, filtra por remoción, y llama de
nuevo al Punto 1 desde cero. Esto garantiza por diseño que "cualquier
ajuste manual dispara recálculo inmediato": no existe ningún
resultado viejo que pueda quedar desactualizado, porque no se guarda
ninguno. Cuando exista la interfaz (Punto 8 en adelante), cada edición
en la UI simplemente vuelve a llamar esta función.

## Tests

`tests/test_ranges.py` — 22 tests: expansión de combos (sin
duplicados ni faltantes en los 1326 combos posibles), simetría de la
grilla, notación (casos válidos + casos que deben fallar explícito),
renormalización, narrowing (nunca agrega tipos, siempre reduce),
historial (nunca se pisa), y integración completa con el Punto 1
(la suma de equities sigue dando ~100% en escenarios multi-rival, y
un ajuste manual efectivamente cambia el resultado recalculado).

Encontré y corregí un error propio en uno de mis tests durante el
desarrollo (no en el motor): asumí que AA le gana más a un rango
angosto de solo KK que a un rango amplio — es al revés (AA gana más
contra un rango amplio con manos débiles mezcladas). Lo corregí tras
verificar el número real, no al revés.

Correr todo:
```bash
python3 poker_engine/tests/test_ranges.py
```

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 1 (comparte evaluador, vía `recompute_equity`),
  Punto 4 (rango preflop inicial — hoy placeholder).
- **Lo consumen directamente:** Punto 1 (input directo, vía
  `to_point1_range`), Punto 15 (combos exactos con pesos — mismo
  `expand_to_weighted_combos`), Punto 3 (a futuro, reemplaza
  `narrowing.py` entero sin tocar `state.py`).
