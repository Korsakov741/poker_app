# Punto 9 — Aprendizaje incremental

## Uso

```python
from poker_engine.learning import LearningStore, compute_behavior_scores_ewma, real_narrow_by_action_ewma
from poker_engine.history import HandHistoryDB

db = HandHistoryDB()
learning = LearningStore()

# cada vez que cierra una mano:
db.ingest_hand(hand)
learning.ingest_hand(hand)

state = learning.get_state("villain_1")   # None si todavía no jugó ninguna mano
scores = compute_behavior_scores_ewma("villain_1", state, db.get_stats("villain_1"))
```

No es un módulo con lógica de negocio propia — es la disciplina de
actualización que aplica a los puntos 3 y 6, tal como aclara el
resumen técnico. En la práctica:

- **Sí se tocan** (vía nuevas funciones, sin romper las viejas):
  VPIP/PFR y sizing-tells del Punto 3.
- **No se toca el Punto 6**: las stats de toda la vida
  (`HandHistoryDB.get_stats`) siguen siendo acumulado simple, sin
  cambios — es lo que pide el resumen técnico explícitamente.
- **No se toca el Punto 7**: las notas siguen siendo 100% manuales,
  ni un EWMA les pasa cerca.

## Dos pesos distintos, confirmados con matemática exacta

- `EWMA_WEIGHT_HIGH_VOLUME = 0.03` para VPIP/PFR (se actualizan casi
  cada mano).
- `EWMA_WEIGHT_SPARSE = 0.20` para sizing-tells (solo en showdown).

Verifiqué la fórmula contra un cálculo cerrado antes de confiar en el
código: con peso chico, tras *n* observaciones de 0 empezando en 1.0,
el valor converge a exactamente `(1-peso)^n` — lo comprobé
(`test_ewma_converge_lento_con_peso_chico_matematicamente_verificado`)
y también con un caso más largo (150 manos) para confirmar que
efectivamente converge, solo que lento.

**Corrección real que tuve que hacerme a mí mismo armando esto:** mi
primera prueba de "el EWMA detecta un cambio de comportamiento"
usaba solo 20 manos (10 antiguas + 10 nuevas) y esperaba ver un
cambio grande — con peso 0.03 el valor apenas se movió de 1.0 a
0.737. Al principio lo iba a reportar como si estuviera mal, pero
verifiqué la matemática (`0.97^10 = 0.737`, exacto) y confirmé que es
el comportamiento CORRECTO y buscado — peso chico reacciona lento a
propósito, es la decisión de diseño del resumen técnico, no un bug.
Lo corregí antes de escribir el test final, usando 150 manos para que
la convergencia sea visible y quede bien demostrada.

## Contador de confianza — sin decaimiento

Crece +1 por cada observación nueva, nunca baja — es cantidad de
evidencia acumulada, no el valor en sí, tal como pide el resumen
técnico. Lo usan tanto `compute_behavior_scores_ewma` (como tamaño de
muestra) como `real_narrow_by_action_ewma` (para decidir si hay
confianza suficiente, mismo umbral `MIN_OBSERVATIONS=7` del Punto 3).

## Historial completo — no solo el último valor

Cada tracker guarda `history: list[float]` con un valor por
observación — barato de implementar (ya estaba ahí, no hubo que
agregar nada extra), y es justo el insumo que va a necesitar el
futuro Punto 12 (revisión post-sesión).

## El efecto real, demostrado con un test

`test_sizing_tell_ewma_reacciona_mas_rapido_que_promedio_plano`: con
10 manos históricas de "esta apuesta siempre es fuerte" seguidas de 3
manos nuevas de "esta apuesta ahora es débil" (empezó a farolear ese
tamaño), el promedio plano del Punto 3 original apenas se mueve
(10/13 ≈ 77%, las 3 nuevas pesan lo mismo que las 10 viejas) — el
EWMA con peso grande (0.20) ya bajó bastante más, reflejando el
cambio reciente mucho más rápido. Es la razón de ser de todo este
punto.

## Tests

`tests/test_learning.py` — 12 tests: la fórmula EWMA exacta, el
contador de confianza sin decaimiento, el historial completo, rechazo
de observaciones fuera de rango, la convergencia lenta verificada
matemáticamente, detección de un cambio de comportamiento real con
suficiente volumen, fallback al Punto 3 plano cuando todavía no hay
estado de aprendizaje, y el caso central (sizing-tell EWMA reacciona
más rápido que el promedio plano).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 3 y Punto 6 (son los que actualiza).
- **Lo consumen directamente:** Punto 10 (mismo mecanismo EWMA,
  distinta constante de decaimiento — reusa `EWMATracker` tal cual),
  Punto 12 (revisión post-sesión — usa el `history` guardado en cada
  tracker).
