# Puntos 6 y 7 — HUD histórico y notas cualitativas

## Punto 6 — Base de datos histórica (HUD)

```python
from poker_engine.history import Action, HandRecord, HandHistoryDB

hand = HandRecord(
    hand_id="h1", players=["A","B","C"],
    actions=[
        Action("A","preflop","post_blind",0), Action("B","preflop","post_blind",1),
        Action("C","preflop","raise",2), Action("A","preflop","fold",3),
        Action("B","preflop","raise",4), Action("C","preflop","call",5),
        Action("B","flop","bet",6), Action("C","flop","fold",7),
    ],
    winners=["B"],
)

db = HandHistoryDB()
db.ingest_hand(hand)
stats = db.get_stats("C")   # PlayerHUDStats: vpip_pct, pfr_pct, threebet_pct, fold_to_cbet_pct, aggression_factor...
```

### Definiciones exactas usadas (documentadas porque varían entre HUDs)

- **VPIP**: puso fichas de forma voluntaria preflop (pagar o subir).
  Postear ciega no cuenta.
- **PFR**: subió preflop, incluye el open.
- **3-bet%**: de las manos donde su PRIMERA acción preflop enfrentó
  exactamente una subida previa (oportunidad real de 3-betear), en
  cuántas subió. El jugador que abrió no tiene "oportunidad de
  3-bet" en esa mano — es una categoría distinta (facing-a-3bet, no
  implementada, no la pedía el resumen).
- **Fold-to-cbet%**: de las manos donde enfrentó una continuation bet
  (el agresor preflop abre apostando el flop), en cuántas se retiró.
  Bug real que encontré armando el test: mi primera versión cortaba
  la cadena de "quién enfrenta el cbet" ANTES de registrar que el
  jugador que SUBIÓ el cbet también lo había enfrentado — quedaba
  con 0 datos en vez de "lo enfrentó y no se retiró". Corregido y
  cubierto por test (`test_raise_corta_la_cadena_de_fold_to_cbet`).
- **Factor de agresión (AF)**: (apuestas+subidas)/pagos, medido
  **solo post-flop** — decisión de convención explícita, hay HUDs
  que lo miden en todas las calles y da un número distinto.

### Con poca muestra, `None` — nunca 0.0 falso

Si un jugador nunca tuvo la oportunidad de 3-betear en la muestra
que tenés, `threebet_pct` es `None`, no `0.0`. Reportar `0.0` sería
una mentira estadística (implicaría "nunca lo hace" cuando en
realidad "no hay dato"). Esto es justo lo que el Punto 3 necesita
para decidir cuándo confiar en un stat (su propio resumen técnico
pide "no usar un tell hasta tener un mínimo de observaciones").

## Punto 7 — Notas cualitativas

```python
from poker_engine.history import PlayerNotesStore

store = PlayerNotesStore()
store.add_note("rival_1", "Sobre-apuesta cuando tiene el nut flush", tag="sizing-tell")
store.get_notes("rival_1")                    # todas
store.get_notes("rival_1", tag="sizing-tell")  # filtradas
```

Deliberadamente simple, tal como exige el resumen técnico del Punto 9:
las notas quedan FUERA de cualquier mecanismo de decaimiento
automático — no hay EWMA ni lógica de cálculo acá, solo
almacenamiento y consulta. Las edita el usuario, punto.

## Tests

`tests/test_history.py` — 11 tests: VPIP/PFR con casos verificados a
mano, 3-bet% (incluyendo que el que abre no tiene "oportunidad"),
fold-to-cbet con el caso de la subida que corta la cadena (donde
encontré el bug), ausencia de c-bet cuando el agresor chequea,
factor de agresión con una mano de 3 calles, `None` en vez de `0.0`
con poca muestra, y las notas (agregar, filtrar por tag, rechazo de
nota vacía, no exponer la lista interna mutable).

## Cómo se conectan con el resto del roadmap

- **No dependen de ningún otro punto del motor** — son la fuente de
  datos crudos.
- **Los consume directamente:** Punto 3 (perfil de rival — stats
  crudas del 6 + notas del 7 como ajuste manual), Punto 9
  (aprendizaje incremental — actualiza el 6 con EWMA, deja el 7
  afuera a propósito).
