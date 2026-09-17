# Punto 16 — Detector de oportunidades de farol

## Uso

```python
from poker_engine.bluff_detector import FoldToBetTable, detect_bluff_opportunity
from poker_engine.self_image import HeroImageTable

fold_table = FoldToBetTable()   # nuevo — ver más abajo por qué hacía falta
image = HeroImageTable(hero_label="hero")
# fold_table.ingest_hand(hand) / image.ingest_hand(hand) por cada mano

oportunidad = detect_bluff_opportunity(
    hero_range=mi_rango_representado, board=board, dead=[],
    villain_range=rango_del_rival, villain_profile=perfil_rival,
    fold_table=fold_table, hero_image_table=image,
    street="flop", bet=130, pot=100,
)
print(oportunidad.reasoning)
print(oportunidad.is_above_threshold)      # nunca una orden, solo si supera el umbral informativo
print(oportunidad.candidate_combos)          # reusa directo la selección del Punto 4
```

## El gap que encontré antes de poder empezar

Este punto necesita "frecuencia histórica de rendición del rival en
ese balde calle+tamaño" — y ESO específicamente no existía todavía:
el Punto 6 tiene fold-to-cbet pero solo para la continuation bet
concreta, sin segmentar por tamaño; el Punto 9 rastrea la fuerza de
la mano de quien APUESTA, no si quien ENFRENTA se retira. Armé
`FoldToBetTable`, un tracker nuevo y chico que reusa directo el
`EWMATracker` del Punto 9 (mismo mecanismo, peso HIGH_VOLUME porque a
diferencia de las sizing-tells esto no necesita showdown — cualquier
apuesta enfrentada ya es una observación válida).

## Las tres señales — combinadas jerárquicamente, no promediadas

- **(A) Base empírica**: `FoldToBetTable`, con el mismo criterio de
  confianza mínima del Punto 3 (7 observaciones) — si no hay
  suficientes, cae al prior poblacional del Punto 14
  (`fold_to_cbet_pct≈48%`), nunca a un 50% inventado a ciegas. Es
  justo lo que pide el resumen técnico: "más importante acá que en
  otros puntos porque un farol mal calibrado es una de las decisiones
  más costosas".
- **(B) Ventaja de rango en el board**: compara mi rango representado
  contra el del rival en fuerza ACTUAL sobre este board (no equity a
  futuro — misma filosofía que el Punto 15). Validado con un caso
  extremo: mi rango de aire (72o, A2s) contra un rango del rival con
  sets garantizados da exactamente 0% — nunca gano, matemáticamente
  correcto.
- **(C) Credibilidad**: reusa directo `get_self_image_assumption` del
  Punto 10, sin duplicar nada.

(A) es la base; (B) y (C) son ajustes MULTIPLICATIVOS sobre esa base
(constantes de fuerza documentadas, mismo patrón que los
amortiguadores del Punto 11) — decisión de diseño porque el resumen
pide "jerárquico" sin dar la fórmula exacta.

## El umbral del Punto 4 — siempre presente, nunca oculto

Cada `BluffOpportunity` trae `min_required_pct` (el `alpha` del Punto
4) junto con la estimación — nunca se muestra la estimación aislada,
tal como exige el resumen técnico.

## Reuso, no duplicación

`candidate_combos` es literalmente la salida de
`select_bluff_candidates` del Punto 4, sin reimplementar nada — el
resumen técnico lo pide explícito ("reutiliza sin duplicar").

## Tests

`tests/test_bluff_detector.py` — 9 tests: el tracker nuevo registra
retiros y corta la cadena ante una subida (igual que el Punto 6),
ventaja de rango con un caso extremo verificable a mano, rechazo
explícito cuando no queda ningún par válido, techo de costo con un
rango completo, uso de dato real vs. caída al prior poblacional según
la confianza, el umbral siempre presente en el resultado, y los
candidatos de farol correctamente incluidos.

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 6 y 9 (dato empírico + confianza, vía el
  `FoldToBetTable` nuevo), Punto 2 y 15 (rangos y textura),
  Punto 10 (credibilidad), Punto 4 (umbral + selección de combos,
  reusados directo), Punto 14 (respaldo poblacional).
- **Lo consume directamente:** Punto 8 (la acción "subir-farol" solo
  aparece como candidata si `is_above_threshold` es `True`).
