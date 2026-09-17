# Punto 12 — Revisión post-sesión (y cierre del roadmap)

## Uso

```python
from poker_engine.session_review import record_decision, SessionReview, fundamental_theorem_gap

review = SessionReview("sesión 2026-09-15")

# por cada decisión real de la sesión:
rd = record_decision("hand_123", "flop", decision_package, actual_action_taken="call")
review.add(rd)

print(review.summary())
print(review.hands_to_review(top_n=10))    # las que más vale la pena repasar
```

## La pieza que faltaba del principio no-negociable #1

Mientras armaba esto noté algo: el principio no-negociable #1 tenía
DOS mitades — "nunca una orden, siempre rangos" (que ya estaba
construida en todos los puntos) y "poder ingresar la acción real que
tomé, distinta a la sugerida, y recalcular" — esta segunda mitad no
tenía un mecanismo dedicado en ningún punto anterior. Nace acá, en
`RecordedDecision`, porque es exactamente donde el Punto 12 lo
necesita como input — pero conceptualmente cierra un principio que
atraviesa todo el proyecto, no solo este punto.

## Las dos preguntas del roadmap general

- **"Dónde se perdió más valor"**: `value_gap` = valor heurístico del
  mejor candidato del Punto 8 menos el de la acción realmente
  tomada — siempre ≥ 0 por construcción (probado explícito). Sumado
  por sesión y desglosado por calle.
- **"Qué manos revisar"**: `hands_to_review()` ordena por `value_gap`
  descendente — las decisiones que más se alejaron de la mejor
  recomendación, primero.

## El teorema fundamental de Sklansky, codificado con lógica propia

Punto 14 pedía esto como métrica de revisión. La idea del teorema
(jugar distinto de cómo jugarías con información perfecta te
perjudica) se traduce acá en un número concreto: para manos que
llegaron a showdown, comparo la equity que INFORMÓ la decisión real
(contra el rango estimado) contra la que se habría calculado viendo
la mano real del rival — la distancia es la medida. Validado con un
caso construido a mano: creencia optimista de 85% de equity, pero la
mano real del rival (trío de sietes) da 0% de equity real → gap de
-85, exactamente lo esperado.

**No es una transcripción del libro** — es una implementación de la
idea central, en código y lógica propia, tal como exige el principio
no-negociable #2 del proyecto.

## Tests

`tests/test_session_review.py` — 10 tests: coincidencia con la
recomendación, `value_gap` positivo cuando no coincide y nunca
negativo, ranking correcto de manos a revisar, suma total de valor
perdido, tasa de coincidencia (incluyendo sesión vacía → `None`, no
una división por cero), desglose por calle, y el teorema fundamental
con un caso de creencia optimista + rechazo explícito de una mano de
rival imposible (carta repetida con el board).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 8 (el `DecisionPackage` completo de cada calle),
  Punto 9 (el historial guardado en los EWMATracker, disponible para
  análisis de sesión más profundo a futuro), Punto 14 (el teorema
  fundamental como métrica).
- **No lo consume nadie más** — es el último eslabón de la cadena de
  dependencias del roadmap.

---

# Cierre — los 17 puntos del roadmap están construidos

Con este punto, el motor de decisión de póker completo está armado:
**17 subpaquetes, 17 archivos de test, todos pasando, sin ninguna
regresión** a lo largo de toda la sesión de trabajo. Cada README
individual (`README_puntoN.md`) documenta, punto por punto, las
decisiones de diseño que tuve que tomar sin especificación exacta,
los bugs reales que encontré y corregí antes de entregar, y las
limitaciones conscientes que quedaron explícitas en vez de
disimuladas.

Lo que sigue, y que no se construyó en esta sesión porque no era el
objetivo pedido, es la capa de interfaz (la app usable en el celu de
la que hablamos al principio) — ensamblar estos 17 módulos Python
detrás de una API y un frontend mobile-friendly. Los notas pendientes
de esa etapa futura (como la cantidad de jugadores en la mesa)
quedaron en `NOTAS_PENDIENTES.md`, esperando ese momento.
