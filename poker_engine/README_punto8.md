# Punto 8 — Motor de decisión final

## Uso

```python
from poker_engine.final_decision import build_decision_package

paquete = build_decision_package(
    street="flop", facing_bet=True, hero_label="hero",
    equity_result=equity,             # Punto 1
    implied_odds=implied,               # Punto 4
    combos_result=combos,                # Punto 15
    villain_continue_rate=0.5,
    bluff_opportunity=bluff_op,           # Punto 16
    gto_exploit=gto_exploit_decision,      # Punto 11 (opcional)
    icm_penalty=icm_result,                 # Punto 17 (opcional, None en cash)
    spr=spr_result,                          # Punto 5 (opcional)
    proposed_bet_fraction_of_stack=0.3,
    hand_so_far=hand_actual,                   # Punto 13 corre automático si se pasa
)

for c in paquete.candidates:       # TODAS las acciones, ordenadas — nunca una sola elegida
    print(c.action, c.heuristic_value, c.top_reasons)
```

## Diseño: ensamblador final, no recalculador

`build_decision_package` recibe los resultados YA CALCULADOS de cada
punto anterior, no los recalcula — mantiene a Point 8 como una capa
de ensamblaje limpia en vez de una función-dios con 40 parámetros de
bajo nivel. Cada punto sigue siendo responsable de su propio cálculo;
Point 8 solo los combina.

## Los cuatro tipos de estimación, tal como pide el resumen técnico

- **`fold`**: referencia cero, siempre disponible como piso.
- **`call`**: equity real del Punto 1 vs. el umbral AJUSTADO del
  Punto 4 (implied odds, no pot odds crudas).
- **`bet_value`**: combos que pierden contra mi mano (Punto 15) ×
  tasa de continuación estimada del rival.
- **`bet_bluff`**: salida directa del Punto 16, sin reimplementar
  nada.

**Decisión de diseño:** `bet_value` y `bet_bluff` son la MISMA acción
física (apostar) pero se muestran como candidatos SEPARADOS — el
usuario tiene que poder ver la justificación de cada uno por
separado, no una cifra mezclada, para no contradecir el principio de
"rangos, no órdenes".

## La capa de ajuste, en el orden de prioridad EXACTO que pide el resumen

1. **GTO/Explotador (Punto 11)**: solo atenúa `bet_value`/`bet_bluff`
   (las que dependen de una lectura del rival) — nunca toca
   `fold`/`call`, que ya están ancladas en matemática real, no en una
   lectura explotable. Probado explícito
   (`test_gto_exploit_no_toca_fold_ni_call`).
2. **ICM (Punto 17)**: penaliza cualquier acción que arriesgue fichas
   (`call`, `bet_value`, `bet_bluff`) en torneo — nunca `fold`
   (retirarse no arriesga nada) ni en cash game (no-op verificado).
3. **Coherencia con SPR (Punto 5)**: la ÚLTIMA palabra, estructural —
   en zona push/fold, marca (no oculta) cualquier apuesta que no sea
   prácticamente all-in como estructuralmente incoherente.

## Punto 13 corre primero, automático

Si se pasa `hand_so_far`, la validación del Punto 13 corre ANTES de
construir nada — `blocked_by_validation=True` si hay errores graves,
sin que eso impida ver el resto del paquete (la información sigue
ahí, solo marcada como no confiable).

## El "paquete de decisión" — insumo del futuro Punto 12

`DecisionPackage` guarda TODO — no solo lo que se termina mostrando:
la calle, las acciones legales, cada candidato con su detalle
completo de ajustes, y los issues de validación. Es exactamente lo
que el resumen técnico pide guardar para la revisión post-sesión del
Punto 12.

## Tests

`tests/test_final_decision.py` — 15 tests: acciones legales según el
contexto, cada estimador base con su fórmula exacta verificada, cada
capa de ajuste probada en aislamiento (incluyendo que NO toque lo que
no debería tocar — fold/call para el amortiguador GTO, fold para el
ICM, cash game sin efecto), coherencia SPR marca correctamente según
si la apuesta propuesta es casi-all-in o no, y la integración
completa: candidatos ordenados, fold siempre presente, bloqueo por
validación funcionando, y sin apuesta enfrente no aparecen
fold/call.

## Cómo se conecta con el resto del roadmap

- **Consume:** prácticamente todo — Puntos 1, 2, 3, 4, 5, 9, 10, 11,
  13, 15, 16, 17.
- **Lo consume directamente:** Punto 12 (revisión post-sesión — usa
  el `DecisionPackage` completo de cada calle, no solo el resultado
  mostrado).
