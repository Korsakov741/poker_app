from __future__ import annotations
from fastapi import APIRouter, HTTPException

from poker_engine.ranges import matrix_position, ALL_HAND_TYPES, HandTypeMatrix
from poker_engine.ranges.position_defaults import Position as PositionEnum
from poker_engine.ranges.narrowing import NarrowAction
from poker_engine.gto_lite.opening_ranges import opening_range
from poker_engine.learning.integration import real_narrow_by_action_ewma

from ..schemas import RangeSpec, SaveRangeInput, SuggestRangeInput
from ..range_conversion import range_spec_to_matrix
from ..state import state

router = APIRouter(prefix="/api/ranges", tags=["ranges"])


@router.post("/preview")
def preview_range(spec: RangeSpec):
    """Devuelve la matriz 13x13 completa (para pintar la grilla en el frontend)."""
    m = range_spec_to_matrix(spec, state)
    grid = {}
    for t in ALL_HAND_TYPES:
        row, col = matrix_position(t)
        grid[t] = {"weight": m.get_weight(t), "row": row, "col": col}
    return {"grid": grid, "combo_count": round(m.combo_count_weighted(), 1)}


@router.post("/save")
def save_range(body: SaveRangeInput):
    m = range_spec_to_matrix(body.range, state)
    weights = {t: w for t, w in m.nonzero_types().items()}
    state.save_range(body.player, weights)
    return {"saved": True, "player": body.player, "combo_count": round(m.combo_count_weighted(), 1)}


@router.get("/saved/{player}")
def get_saved_range(player: str):
    if player not in state.saved_ranges:
        raise HTTPException(404, f"No hay rango guardado para {player!r}")
    return {"player": player, "weights": state.saved_ranges[player]}


@router.get("/saved")
def list_saved_ranges():
    return {"players": list(state.saved_ranges.keys())}


@router.post("/suggest")
def suggest_range(body: SuggestRangeInput):
    """
    Sugiere un punto de partida para el rango de un rival, en vez de
    dejar al usuario escribiendo todo a ciegas: arranca de una tabla
    de apertura por posición (Punto 4) si hay posición cargada — si
    no, arranca de "cualquier mano" sin sesgo — y la angosta según la
    acción real que ese rival tomó (con datos reales de él si ya hay
    historial, si no con la heurística genérica del Punto 2/3).
    """
    if body.villain_position and body.num_players:
        try:
            base = opening_range(PositionEnum(body.villain_position), body.num_players, body.spr_category)
        except ValueError as e:
            raise HTTPException(400, str(e))
        position_informed = True
    else:
        base = HandTypeMatrix.from_top_percent(100)  # sin posición del rival -> sin sesgo, arranca de "cualquier mano"
        position_informed = False

    action_enum = NarrowAction.RAISE if body.action_type in ("raise", "bet") else NarrowAction.CALL
    learning_state = state.learning_store.get_state(body.villain_label)

    try:
        narrowed, info = real_narrow_by_action_ewma(
            base, body.villain_label, body.street, body.pot_fraction, action_enum, learning_state,
        )
    except (ValueError, ZeroDivisionError) as e:
        raise HTTPException(400, str(e))

    return {
        "weights": narrowed.nonzero_types(),
        "combo_count": round(narrowed.combo_count_weighted(), 1),
        "source": info["source"],  # 'real_sizing_tell_ewma' | 'generic_placeholder'
        "n_observations": info.get("n_observations", 0),
        "position_informed": position_informed,
    }
