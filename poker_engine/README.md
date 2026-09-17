# Punto 1 — Motor de equity avanzado

Primer módulo del motor de decisión de póker. Evaluador de manos +
simulación (Monte Carlo en preflop/flop, enumeración exacta en
turn/río), tal como lo define el resumen técnico del roadmap.

## Uso

```python
from poker_engine.equity import calculate_equity, Range

resultado = calculate_equity(
    hero=("Ah", "Kh"),
    board=["Qh", "Jh", "2c"],       # [] en preflop, 3/4/5 cartas según calle
    dead=[],                          # cartas muertas conocidas
    opponent_ranges=[
        Range.random(),                                    # placeholder hasta que exista el Punto 2
        Range.from_combos([("As","Ac",1.0), ("Ks","Kc",0.7)]),  # rango manual pesado
    ],
    num_sims=30_000,                  # solo importa en preflop/flop
)

for jugador in resultado.players:
    print(jugador.label, jugador.equity_pct, jugador.ci_low, jugador.ci_high)
```

Salida (`EquityResult`):
- `mode`: `'monte_carlo'` (preflop/flop), `'exact'` (turn/río), o
  `'monte_carlo_fallback'` (turn/río cuando el espacio conjunto es
  demasiado grande para enumerar — ver más abajo).
- Por jugador: `win_pct` (ganó solo), `tie_pct` (participó de un
  empate, informativo), `equity_pct` (el número real a usar — ya
  reparte los empates correctamente), y `ci_low`/`ci_high` **solo**
  en Monte Carlo (en modo exacto son `None`, porque no hay muestreo).

Esto ya respeta el principio no-negociable #1 del proyecto: nunca se
devuelve una orden, siempre un rango (Monte Carlo) o un número exacto
sin ambigüedad de ejecución (turn/río) — la decisión la toma el
Punto 8 más adelante, combinando esto con el resto de las capas.

## Decisiones de diseño (flaggeadas explícitamente, tal como pediste)

1. **Algoritmo de muestreo en Monte Carlo — filtrado secuencial, no
   rechazo conjunto.** El resumen técnico exige remoción de cartas
   entre rivales pero no especifica el algoritmo. Elegí filtrar el
   rango de cada rival contra lo ya repartido y renormalizar, en vez
   de rechazar toda la simulación ante cualquier choque. Motivo:
   rechazo conjunto puede colgarse cuando varios rivales tienen
   rangos angostos y superpuestos (ej. dos rivales ambos "solo AA").
   El costo es una dependencia teórica mínima del orden de
   procesamiento cuando los rangos se superponen mucho — despreciable
   frente al margen de error propio de Monte Carlo. Documentado en el
   docstring de `montecarlo.py`.

2. **Techo al espacio de enumeración exacta + fallback automático a
   Monte Carlo.** Enumerar exactamente el turn/río es rápido con 1-3
   rivales y rangos razonables, pero explota combinatoriamente con
   muchos rivales de rango ancho (ej. 5 rivales random en turn puede
   superar varios cientos de millones de combinaciones). Puse un
   techo (`MAX_JOINT_SPACE = 3,000,000`); si se supera, el motor
   principal cae automáticamente a Monte Carlo con 100,000
   iteraciones y lo marca explícito como `mode='monte_carlo_fallback'`
   — nunca se devuelve un resultado exacto que en realidad no lo es,
   ni se cuelga el cálculo. Mismo patrón de diseño que ya usaste vos
   para ICM en torneos grandes (Punto 17).

3. **Intervalo de confianza vía aproximación normal (CLT), no
   binomial exacto.** La "equity" por simulación no es un 0/1 puro
   (los empates reparten crédito fraccionario, ej. 1/3 en un empate a
   tres bandas), así que un intervalo binomial clásico no aplica
   directo. Se acumula suma y suma de cuadrados por jugador durante
   la simulación y se calcula el error estándar de la media
   (`sqrt(Var/n)`), con intervalo al 95% (`z=1.96`). Es el enfoque
   estándar para variables acotadas en [0,1] con muestras grandes
   (30k+ sims cae cómodo dentro de las condiciones de aplicabilidad
   del CLT).

4. **Bug encontrado y corregido durante el testing:** la primera
   versión sumaba un "empate completo" a cada jugador empatado en vez
   de dividir 1/k entre los k empatados — rompía la invariante de que
   las equities tienen que sumar 100%, que es exactamente lo que el
   resumen técnico pedía verificar con el test de 3+ rivales. Quedó
   corregido y cubierto por test antes de entregar esto.

5. **Fix de performance durante el testing:** la primera versión del
   rango `Range.random()` regeneraba todas las combinaciones posibles
   del mazo restante (cientos de objetos) en cada simulación
   individual, lo cual colgaba el cálculo con varios rivales random.
   Se corrigió para samplear directo 2 cartas del mazo restante sin
   materializar la lista completa. Con el fix, 30k simulaciones con 3
   rivales random en el flop corren en ~2.3s — razonable para uso en
   vivo desde el celular, aunque queda como optimización futura
   (vectorizar con numpy) si hace falta más velocidad más adelante.
   No lo hice ahora para no optimizar prematuramente sin el resto del
   sistema construido.

## Qué es placeholder hoy (y se reemplaza solo cuando construyamos el Punto 2)

`Range.random()` representa "cualquier mano, sin sesgo" — es
exactamente lo que el propio resumen técnico del Punto 1 autoriza
como comportamiento mientras el Punto 2 no exista ("sin esto, solo
puede calcular contra mano al azar"). El día que construyamos el
Punto 2, va a producir objetos `Range.from_combos([...])` con pesos
reales — el motor de equity **no se toca**, porque el formato de
entrada ya está diseñado para eso desde ahora (combos ya expandidos y
pesados, no tipos de mano en formato matriz 13x13 — esa expansión es
responsabilidad del Punto 2, no de este módulo).

## Qué NO se construyó todavía (a propósito)

- Nada de historial, perfiles de rival, ni narrowing automático de
  rangos por acción — eso es Punto 2 (heurísticas) y Punto 3
  (perfiles reales). Este módulo es, como pide el resumen técnico,
  "módulo puro y aislado".
- Nada de interfaz (ni web ni celu) — ver nota de arquitectura más
  abajo.
- Optimización de velocidad más allá de lo que ya corre en ~2s por
  consulta (ver decisión #5 arriba).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 2 (rangos reales, cuando exista — hoy usa el
  placeholder `Range.random()`).
- **Lo consumen directamente:** Punto 2 (comparte el evaluador de
  `evaluator.py`), Punto 15 (combos que vencen mi mano — mismo
  evaluador), Punto 4 (pot odds/implied odds necesitan equity real,
  no solo `alpha`), Punto 8 (motor de decisión final).

## Tests

- `tests/test_removal_multiway.py` — el test explícito que pedía el
  resumen técnico: 3+ rivales con rangos que se superponen a
  propósito en las mismas cartas, verificando que las equities suman
  ~100% contando empates bien correctamente (en Monte Carlo Y en modo
  exacto), más un chequeo directo de que nunca se reparte una carta
  duplicada.
- `tests/test_engine.py` — valores de referencia conocidos de teoría
  de póker (AA vs mano al azar ≈85.2%, AA vs KK ≈82.4%, coinflip real
  AK vs pareja baja), cartas muertas que vacían un rango (debe fallar
  explícito, no dar un número silenciosamente incorrecto), pesos que
  sesgan la equity de forma proporcional, y el mecanismo de fallback
  a Monte Carlo cuando el espacio exacto es demasiado grande.

Correr todo:
```bash
python3 poker_engine/tests/test_removal_multiway.py
python3 poker_engine/tests/test_engine.py
```

## Nota de arquitectura (aplica a todo el proyecto, no solo este punto)

Este módulo y los que sigan se construyen como paquetes Python puros,
testeados de forma aislada, sin atarlos a ninguna interfaz todavía.
Cuando tengamos suficientes puntos construidos como para que una UI
tenga sentido, se exponen detrás de una API liviana (FastAPI) con un
frontend web mobile-friendly, para uso desde el navegador del celu
sin instalar nada nativo. Se avisa explícitamente cuando arranque esa
etapa.
