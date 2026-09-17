# Punto 10 — Imagen propia

## Uso

```python
from poker_engine.self_image import HeroImageTable, get_self_image_assumption
from poker_engine.profile import build_player_profile

image = HeroImageTable(hero_label="hero")
# image.ingest_hand(hand) por cada mano con showdown donde hero mostró

perfil_villain = build_player_profile("villain_1", db, notes)
asuncion = get_self_image_assumption(image, "flop", pot_fraction=0.7, villain_profile=perfil_villain)

print(asuncion.adjusted_credibility)   # cuánto debería pesar la imagen de hero PARA ESTE rival puntual
print(asuncion.caveat)                   # siempre presente, nunca opcional
```

## Espejo del Punto 3, con dos diferencias reales

1. **Flag explícito de farol** (`Action.is_bluff`): extendí el
   modelo de datos otra vez (retrocompatible, confirmado con los
   tests del 6/7/3/9 antes de seguir). No se infiere de la fuerza de
   la mano — solo el jugador que apostó sabe si fue un farol real; si
   no se marcó el flag, esa observación simplemente no cuenta para
   `bluff_rate` (dato faltante, no "no fue farol").
2. **EWMA más rápido**: peso `0.15` en vez del `0.03`/`0.20` del
   Punto 9. Verificado matemáticamente antes de fijarlo:
   `(1-0.15)^7 ≈ 0.32` (efecto fuerte a los 5-10 manos) y
   `(1-0.15)^25 ≈ 0.017` (casi disuelto a los 20-30) — coincide con
   lo que pide el resumen técnico.

## El cruce obligatorio con el Punto 3 — decisión de diseño a flaggear

El resumen técnico pide cruzar con el perfil del rival para saber si
ese rival "realmente ajusta según lo que ve", pero no da una fórmula.
Usé el `aggression_score` del Punto 3 como proxy (jugadores más
agresivos tienden a pensar más en rangos y ajustar más; los muy
pasivos suelen jugar su propia mano sin mirar mucho la imagen del
rival) — es una heurística razonable, no un hecho, por eso el
resultado final siempre lleva el `caveat` explícito. Sin datos de ese
rival todavía, doy **0.5 (punto medio) en vez de inventar** un sesgo
hacia "asume que ajusta" o "asume que no ajusta".

`Punto 7` entra acá como override manual: si las notas te dicen que
ESE rival puntual sí lee mucho (o no lee nada), `manual_override` pisa
el proxy — mismo patrón de "no parsear texto libre automáticamente"
que ya usé en el Punto 3.

## Por qué se multiplica, no se promedia

`adjusted_credibility = hero_strong_rate_ewma × relevance_weight`. Si
un rival tiene relevancia 0 (no ajusta nada), da igual lo agresiva o
mentirosa que haya sido la imagen real de hero — a ESE rival puntual
no le importa. Probado explícitamente
(`test_assumption_credibilidad_es_cero_si_rival_no_ajusta`): imagen
de hero fuerte (>90%) pero credibilidad ajustada exactamente 0 cuando
`relevance=0`.

## Nunca un hecho — siempre una suposición

Todo `SelfImageAssumption` lleva un campo `caveat` no opcional. Es
justo lo que pide el resumen técnico: "toda salida de este punto se
presenta como asunción razonable, nunca como hecho".

## Tests

`tests/test_self_image.py` — 10 tests: EWMA de fuerza con manos
reales, el flag de farol solo cuenta cuando está explícito (no
inferido), la fórmula EWMA exacta verificada a mano, manos sin
showdown no se registran, el proxy de relevancia usa el Punto 3
correctamente, el override manual lo pisa, el punto medio explícito
sin datos, el caveat siempre presente, y el caso central (rival que
no ajusta → credibilidad cero sin importar la imagen real).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 9 (mismo `EWMATracker`, otra constante), Punto 3
  y Punto 7 (perfil del rival + notas, para la relevancia).
- **Lo consumen directamente:** Punto 11 (razón legítima para
  desviarse de GTO), Punto 16 (credibilidad de la historia de las
  apuestas propias — `adjusted_credibility` es exactamente ese
  insumo).
