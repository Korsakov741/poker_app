# Punto 17 — ICM (Independent Chip Model)

## Uso

```python
from poker_engine.icm import SessionMode, TournamentContext, icm_penalty_for_play

ctx = TournamentContext(
    payouts=[500, 300, 200],   # payouts[0] = 1er puesto, etc.
    stacks={"hero": 15000, "v1": 3000, "v2": 25000, "v3": 8000, "v4": 12000},
    hero_label="hero",
    table_labels={"v1", "v2", "v3", "v4"},
)
session = SessionMode.tournament_mode(ctx)

# evaluar un all-in marginal (55% de ganar) contra v4
resultado = icm_penalty_for_play(session, villain_label="v4", bet_amount=10000, p_win=0.55)
print(resultado.icm_penalty_dollars)   # positivo = el modelo ingenuo (cEV) sobrestima el valor real
```

En cash game, `SessionMode.cash_game()` hace que `icm_penalty_for_play`
devuelva `applies=False` sin calcular nada — el interruptor es binario,
tal como pide el resumen técnico (a diferencia de la mezcla continua
del Punto 11).

## El modelo (Malmuth-Harville) — validado contra un ejemplo calculado a mano

```
P(gana 1° entre un grupo) = stack_propio / suma_stacks_del_grupo
P(termina en el lugar p>1) = Σ_rivales [ P(rival gana 1°) × P(termina en el lugar p-1 sin ese rival) ]
```

Antes de escribir el test, calculé a mano el ejemplo clásico de 3
jugadores (stacks 5000/3000/2000, pagos 50/30/20) y me dio
38.393/32.75/28.857 — el código da exactamente eso
(`test_ejemplo_clasico_3_jugadores`).

## Decisión de diseño: la simplificación para torneos grandes

Benchmarkeé el costo real antes de fijar cualquier techo (no adiviné
un número):

| jugadores | lugares pagos | tiempo |
|---|---|---|
| 14 | 9 | 0.4s |
| 14 | 12 | 1.1s |
| 18 | 9 | 14s |
| 25 | 9 | 105s |

Techo elegido: **14 jugadores / 12 lugares pagos** — cubre cómodamente
cualquier mesa final. Más allá de eso, se activa la aproximación por
**campo reducido**:

1. Se mantienen individuales: el hero, su mesa actual, y los N
   jugadores de todo el campo con stack más parecido al del hero (son
   sus competidores más directos por un mismo lugar de cobro).
2. El resto del campo se agrupa en varios "buckets" (jugadores
   ficticios) que suman las fichas reales que representan — el total
   de fichas del torneo se preserva exacto.
3. La cantidad de buckets se elige para que el campo reducido tenga
   siempre más entidades que lugares pagos, con margen — si no, la
   recursión no podría repartir probabilidad de forma sensata entre
   todos los lugares que pagan.

**Limitación aceptada explícitamente:** un bucket resuelve más grueso
que la realidad. En la vida real, cuando "alguien del bucket" es
eliminado, en verdad cae UN jugador real de ese grupo y los demás
siguen con sus fichas intactas — el modelo reducido trata la
eliminación del bucket entero como un solo evento. Es una aproximación
deliberada para que el cálculo sea viable, coherente con que todo en
esta app es informativo, nunca una instrucción exacta. Los jugadores
dentro de un bucket no tienen $EV individual calculable (el resultado
los marca con `None`, no con un número inventado).

## ICM penalty

Compara **dos escenarios completos** (ganar la mano / perderla),
recalculando el modelo ICM entero en cada uno — nunca cEV simple, tal
como exige el resumen técnico — y los pondera por la probabilidad real
de ganar (que viene del Punto 1). Esto se compara contra un
equivalente "ingenuo": tratar las fichas como si valieran una tasa
constante en dólares (`pool total / fichas totales`). La diferencia
ES la presión de ICM.

Validé el signo y la magnitud con dos casos opuestos:
- **All-in marginal (55%) cerca de la burbuja** (5 jugadores, paga 3):
  el modelo ingenuo dice que el $EV sube; el ICM real dice que en
  realidad **baja** — el clásico caso de una jugada +cEV que es
  -$EV real por presión de burbuja. `icm_penalty_dollars` da positivo,
  como corresponde.
- **Winner-take-all** (un solo lugar pago): el penalty da
  prácticamente cero, porque no hay "lugares que proteger" — el $EV
  en dólares es simplemente proporcional al stack, sin presión de
  ICM posible.

## Tests

`tests/test_icm.py` — 14 tests: el ejemplo clásico calculado a mano,
suma del EV = pool total, jugador bustado con EV=0, winner-take-all
como caso trivial de control, activación correcta de la reducción con
campos grandes (y preservación exacta de fichas totales en el campo
reducido), rechazo explícito cuando falta hero/mesa para la
aproximación, el interruptor binario cash/torneo, y los dos casos de
validación del ICM penalty (burbuja vs. winner-take-all).

## Cómo se conecta con el resto del roadmap

- **Consume:** metadata de sesión (modo torneo), stacks de todos los
  jugadores restantes, estructura de pago — ninguno de estos es otro
  punto del motor, por eso este fue el único punto difícil que se
  pudo construir sin esperar a nada más.
- **Lo consumen directamente:** Punto 4 (tablas de apertura/push-fold
  específicas de torneo — a futuro), Punto 11 y Punto 8 (amortiguador
  de peso explotador y restricción estructural — `icm_penalty_dollars`
  es exactamente el número que van a usar), Punto 5 (profundidad de
  stack cerca de burbuja).
