# Punto 11 — Regla de decisión GTO vs. Explotador

## Uso

```python
from poker_engine.decision import decide_gto_vs_exploit

decision = decide_gto_vs_exploit(
    gto_line=gto_line,           # HandTypeMatrix — placeholder del Punto 2 hasta que exista el Punto 4
    exploit_line=exploit_line,    # HandTypeMatrix — salida real de real_narrow_by_action_ewma (Punto 3/9)
    n_reliable_observations=15,    # confianza real (viene de real_narrow_by_action_ewma)
    confidence_target=20,           # umbral objetivo, ajustable
    self_image_relevance=relevance,  # del Punto 10
    icm_penalty=icm_result,           # del Punto 17, o None en cash game
)
print(decision.blended_range)     # HandTypeMatrix mezclado, lo consume el Punto 8
print(decision.reasoning)          # texto explicativo, también insumo del Punto 8
```

## De dónde salen `gto_line` y `exploit_line` — decisión de diseño

Point 11 no construye estas dos líneas, las RECIBE — mantiene la
lógica de mezcla desacoplada de cómo se arman. Hoy, sin el Punto 4:

- **`gto_line`**: el mismo placeholder que ya usa el Punto 2
  (`placeholder_opening_range` + `narrow_by_action` genérico). El día
  que el Punto 4 exista, reemplaza esos dos placeholders — el Punto
  11 no se entera del cambio, solo recibe un `HandTypeMatrix` mejor.
- **`exploit_line`**: la salida real de `real_narrow_by_action_ewma`
  del Punto 3/9 — esto SÍ es dato real, no placeholder, ya funciona
  hoy.

## Mezcla continua — nunca un interruptor binario

`blend_matrices` interpola linealmente, celda por celda, entre las
dos matrices. Con peso 0.0 da exactamente la línea GTO, con peso 1.0
da exactamente la línea explotadora — verificado con test en ambos
extremos.

## Rampa de confianza

`peso_explotador = mín(1, observaciones_confiables / umbral_objetivo)`
— crece lineal hasta saturar. Con 0 observaciones, peso=0.0: **default
seguro, línea GTO pura**, defendible porque una línea balanceada no
se puede explotar en contra por construcción teórica (tal como pide
el resumen técnico).

## Los dos amortiguadores — constantes elegidas y documentadas

Ninguna de las dos constantes viene fijada por el resumen técnico,
así que las elegí con un criterio conservador (ningún amortiguador
lleva el peso a cero, siempre queda algo de margen para explotar
igual si la lectura es muy fuerte):

- **`SELF_IMAGE_DAMPER_STRENGTH = 0.5`**: un rival que ajusta
  TOTALMENTE (relevancia=1.0, Punto 10) corta el peso explotador a la
  MITAD, no a cero — sigue habiendo margen para explotar aunque el
  rival piense, si la lectura es muy fuerte.
- **`ICM_DAMPER_STRENGTH = 0.7`**: presión de ICM severa (penalty
  grande relativo al EV actual) corta el peso explotador hasta un
  70% — normalizado contra el `ev_before_dollars` del propio
  `ICMPenaltyResult` del Punto 17 para que sea comparable entre
  distintos tamaños de stack/pool. En cash game (`applies=False`) el
  amortiguador es un no-op explícito (factor 1.0), verificado con
  test.

## Razón en texto — no solo el número

Cada `ExploitVsGTODecision` trae un `reasoning` en español que
explica: peso base y de dónde salió, qué hizo cada amortiguador (o si
no aplicó), y el peso final con el % de cada línea — es exactamente
el insumo de explicación que el Punto 8 necesita mostrar junto al
rango, tal como pide el resumen técnico.

## Tests

`tests/test_decision.py` — 13 tests: interpolación lineal exacta en
ambos extremos (peso 0 y peso 1), la rampa de confianza (cero,
saturación, punto medio), el default seguro sin evidencia, ambos
amortiguadores probados con datos reales de los Puntos 10 y 17
(incluyendo el caso "cash game → sin amortiguador ICM"), y que el
texto de razón esté presente y mencione los números clave.

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 4 (línea GTO — hoy placeholder del Punto 2),
  Punto 3 y 9 (desviación y confianza, vía `real_narrow_by_action_ewma`),
  Punto 10 y 17 (los dos amortiguadores, con datos reales).
- **Lo consume directamente:** Punto 8 (motor de decisión final —
  consume tanto `blended_range` como `reasoning`).
