# Punto 3 — Perfil de rival por comportamiento

## Uso

```python
from poker_engine.history import HandHistoryDB, PlayerNotesStore
from poker_engine.profile import build_player_profile, real_narrow_by_action, SizingTellsTable
from poker_engine.ranges import NarrowAction, HandTypeMatrix

db = HandHistoryDB()          # ingestar manos (Punto 6)
notes = PlayerNotesStore()     # notas (Punto 7)
tells = SizingTellsTable()      # sizing-tells (nuevo acá)
# ... db.ingest_hand(hand), tells.ingest_hand(hand), notes.add_note(...) por cada mano jugada

perfil = build_player_profile("villain_1", db, notes)
print(perfil.effective_tightness, perfil.effective_aggression)

# reemplazo real del narrowing genérico del Punto 2:
matriz_angostada, info = real_narrow_by_action(
    HandTypeMatrix.from_top_percent(40), "villain_1", "flop",
    pot_fraction=1.2, action=NarrowAction.BET, sizing_tells=tells,
)
```

## Extensión al modelo de datos (retrocompatible)

Para las sizing-tells hacía falta información que el Punto 6 no
necesitaba: tamaño de apuesta relativo al bote y cartas mostradas en
showdown. Extendí `history/models.py` (`Action.pot_fraction`,
`HandRecord.board`, `HandRecord.showdown_hands`) con campos opcionales
— los 11 tests del Punto 6/7 siguen pasando sin tocarlos, confirmado
antes de seguir.

## Los dos ejes continuos

`tightness_score` (100=muy tight, 0=muy loose) es el complemento
directo del VPIP — es literalmente la definición del eje.
`aggression_score` combina PFR/VPIP (agresión preflop) y factor de
agresión postflop, promediando lo que haya disponible.

**Limitación real que encontré armando esto (no estaba en tu
resumen):** la escala es un complemento lineal directo, NO está
calibrada contra una distribución poblacional real de jugadores. El
VPIP promedio real de una mesa suele rondar 20-25%, no 50% — así que
con esta escala cruda, casi todos los jugadores reales van a caer en
la mitad "tight" del rango (65-85), aunque sean promedio. Una escala
bien calibrada centraría el "50" en el VPIP poblacional típico, no en
VPIP=50%. No inventé esa calibración porque necesitaría datos
poblacionales reales de respaldo — es exactamente lo que tu propio
Punto 14 promete aportar ("perfil de población por defecto, de
Miller") como prior mejor que la heurística actual.

## Sizing-tells: clasificación fuerte/débil

Uso la categoría de mano de treys con corte simple: **trío o mejor =
fuerte, dos pares o peor = débil**. Es una heurística que no lee el
board — un top pair en un board seco puede ser una mano de valor
real y acá se clasifica igual "débil". No armé un sistema de fuerza
contextual porque eso empieza a pisar terreno del Punto 4 (rangos
polarizados/mergeados post-flop), que vos mismo marcaste como
extensión PENDIENTE del Submódulo A del Punto 4 — no algo para
resolver silenciosamente acá adentro.

## La función de ajuste de rango real — reemplazo directo del Punto 2

`real_narrow_by_action()` tiene la MISMA firma de entrada/salida que
el placeholder `narrow_by_action` del Punto 2 (matriz → matriz), así
que `state.py` del Punto 2 no se entera del cambio cuando lo
conectemos. Umbral de confianza: **7 observaciones de showdown**
mínimo en ese balde específico (mitad del rango 5-10 que sugería tu
resumen), si no, cae al placeholder genérico — nunca inventa un
ajuste con poca evidencia.

**Limitación real, más importante que la anterior:** la
infraestructura actual del Punto 2 (`HandTypeMatrix` +
`narrow_by_action`) solo sabe expresar "quedate con el X% superior
por fuerza" — no puede representar "este jugador tiende a farolear
con este tamaño" como un sesgo hacia manos DÉBILES específicas. Lo
que esta función SÍ mejora respecto del placeholder genérico: el X%
ya no es una constante fija (33/50/70%) sino que sale de datos reales
de ESE jugador en ESE balde. Pero si el historial muestra que un
tamaño de apuesta casi nunca es fuerte (posible farol), lo único que
puede hacer es angostar MENOS (dejar el rango más ancho) — no puede
apuntar específicamente a las manos débiles. Representar eso bien es
un problema de representación de rango más profundo (polarizado vs.
mergeado), que es justo la extensión pendiente que marca tu Punto 14.
Hay un test específico para esto
(`test_narrowing_real_angosta_menos_si_el_tell_es_debil`).

## Notas como ajuste MANUAL (no automático)

Las notas del Punto 7 son texto libre — no hay forma honesta de
parsearlas en un número sin inventar NLP que no pediste.
`PlayerProfile` expone las notas junto a los scores calculados, y
`override_tightness()`/`override_aggression()` dejan que quien lea el
perfil (vos, o a futuro la UI) pise el número calculado si las notas
lo justifican — el valor calculado no se pierde, `clear_overrides()`
lo recupera.

## Tests

`tests/test_profile.py` — 13 tests: arquetipos conocidos (nit,
calling station) dan scores coherentes, sin datos da `None` (nunca un
número inventado), clasificación de baldes de sizing, strong_rate con
muestras puras y mezcladas, manos sin showdown no se registran,
fallback al genérico con poca muestra, uso del tell real con muestra
suficiente, y el caso específico de la limitación (tell débil angosta
menos que uno fuerte). Más los tests de override manual (pisa,
recupera, rechaza fuera de rango).

## Cómo se conecta con el resto del roadmap

- **Consume:** Punto 6 (stats crudas, sin duplicar el cálculo), Punto
  7 (notas, como ajuste manual explícito).
- **Lo consumen directamente:** Punto 2 (`real_narrow_by_action`
  reemplaza el placeholder de `narrowing.py`), Punto 9 (mecanismo de
  actualización — todavía no conectado, es el próximo paso natural),
  Punto 11 (nivel de confianza para decidir cuánto desviarse de GTO —
  el `n_observations` que expone `real_narrow_by_action` es
  exactamente ese insumo).
