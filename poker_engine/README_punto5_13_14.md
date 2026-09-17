# Puntos 5, 13 y 14 — posición/SPR, validación de datos, y prior poblacional

## Punto 5 — Posición y SPR

```python
from poker_engine.table import determine_position, compute_spr

pos = determine_position(num_players=6, button_seat=3, hero_seat=0)  # Position.EARLY
spr = compute_spr({"hero": 8000, "v1": 3000}, pot_size=1000)          # SPRResult(spr=3.0, category='bajo')
```

**Decisión de diseño clave:** no hardcodeo tablas de nombres de
posición por tamaño de mesa (recordá que anotamos en
`NOTAS_PENDIENTES.md` que la cantidad de jugadores NUNCA está fija,
cambia mano a mano en torneo). En cambio, calculo la posición de
forma genérica: botón/SB/BB son siempre los 3 asientos fijos, y el
resto se reparte en tercios (temprano/medio/tardío) según distancia
a UTG — escala solo a cualquier tamaño de mesa, probado desde
heads-up hasta 9-max, sin ninguna tabla especial por tamaño.

SPR usa la convención estándar: en un pote multi-way, el stack
efectivo es el MÁS CHICO entre los jugadores activos (el primero que
puede quedar all-in).

## Punto 13 — Validación de datos

```python
from poker_engine.validation import validate_hand
issues = validate_hand(hand)  # lista de ValidationIssue(severity, message)
```

**Limitación real e importante, no estaba en tu resumen:** el
resumen menciona "bote no cuadra" como ejemplo, pero el modelo de
datos actual guarda apuestas como FRACCIÓN del bote, no como monto
absoluto, y no lleva stacks/bote real a lo largo de la mano — así que
con los datos disponibles hoy **no se puede validar aritmética real
de bote**. Lo que sí valida: cartas repetidas (board + showdowns),
board incompleto para las calles que tienen acción, valores de orden
duplicados, jugadores referenciados que no existen, alguien actuando
después de haberse retirado, y consistencia de showdown. Es un
subconjunto real de "detectar errores de captura", no el conjunto
completo — para la aritmética de bote hace falta que la futura capa
de captura guarde montos absolutos y stacks iniciales (anotado en
`NOTAS_PENDIENTES.md`).

## Punto 14 (parte A) — Prior poblacional

```python
from poker_engine.knowledge import POPULATION_DEFAULT_STATS, population_informed_keep_fractions
```

**Sobre la fuente de los números:** son valores de referencia
ampliamente citados en software/contenido de análisis de póker (no
una transcripción de ningún libro puntual del roadmap), presentados
como punto de partida razonable — nunca como medición propia ni
verdad revelada. Cuando haya datos reales (Punto 6/9), esos SIEMPRE
pesan más — es justo lo que ya hace el mecanismo EWMA del Punto 9 con
cualquier prior.

**Impacto inmediato en el Punto 2** (tal como pedía tu resumen,
priorizando A por sobre B): reemplacé las constantes arbitrarias del
narrowing genérico (`0.33/0.5/0.7`, que literalmente salieron de la
nada) por valores derivados del factor de agresión poblacional vía
una fórmula propia y documentada. Coincidencia tranquilizadora: dan
`0.355/0.524/0.710`, muy cerca de los valores originales — pero eso
no valida la fórmula, sigue siendo una heurística, lo dejé explícito
en el código.

**Impacto en el Punto 11**: automático, sin tocar código de ese
punto — el Punto 11 usa como "línea GTO" placeholder lo que sea que
produzca el pipeline del Punto 2, así que la mejora se hereda sola.

**Lo que queda pendiente (parte B, explícitamente fuera de alcance
hoy):** el marco de rangos polarizados vs. mergeados post-flop
(extensión del Submódulo A del Punto 4) — tu propio resumen lo prioriza
después de A, así que no lo construyo todavía.

## Tests

- `tests/test_table.py` — 10 tests (Punto 5): botón en cualquier
  tamaño de mesa, heads-up como caso especial, 6-max y 9-max
  verificados asiento por asiento, escalado automático sin tabla
  hardcodeada, SPR multi-way y filtrado por jugadores activos.
- `tests/test_validation.py` — 10 tests (Punto 13): mano sana sin
  falsos positivos, y cada tipo de error metido a propósito
  (detectados todos, confirmado con una mano rota de ejemplo antes de
  formalizar los tests).
- `tests/test_knowledge.py` — 5 tests (Punto 14): rangos razonables
  de los stats poblacionales, la fórmula exacta de keep_fractions, el
  orden lógico (subir siempre angosta más que pagar), y la integración
  real confirmada (no solo que el módulo exista aislado, sino que
  `narrowing.py` del Punto 2 efectivamente usa estos valores).

## Cómo se conectan con el resto del roadmap

- **Punto 5** lo consumen directamente: Punto 4 (tabla de apertura
  según posición/profundidad), Punto 8 (chequeo de coherencia con
  SPR).
- **Punto 13** lo consume directamente: Punto 8 ("debería correr
  antes en cada calle para validar los datos de entrada").
- **Punto 14** lo consumen: Punto 2 (ya conectado), Punto 4
  (Submódulo A, cuando exista), Punto 11 (heredado automáticamente
  vía el Punto 2), Punto 12 (a futuro, teorema fundamental de
  Sklansky como métrica de revisión).
