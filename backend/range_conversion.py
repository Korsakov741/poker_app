from __future__ import annotations
from fastapi import HTTPException

from poker_engine.ranges import HandTypeMatrix
from poker_engine.equity.ranges import Range
from poker_engine.ranges.notation import NotationError

from .schemas import RangeSpec
from .state import AppState


def range_spec_to_matrix(spec: RangeSpec, state: AppState) -> HandTypeMatrix:
    try:
        if spec.method == "notation":
            if not spec.notation:
                raise HTTPException(400, "Falta 'notation'")
            return HandTypeMatrix.from_notation(spec.notation)
        if spec.method == "top_percent":
            if spec.top_percent is None:
                raise HTTPException(400, "Falta 'top_percent'")
            return HandTypeMatrix.from_top_percent(spec.top_percent)
        if spec.method == "paint":
            if not spec.paint:
                raise HTTPException(400, "Falta 'paint'")
            m = HandTypeMatrix()
            m.paint(spec.paint)
            return m
        if spec.method == "saved":
            if not spec.saved_player or spec.saved_player not in state.saved_ranges:
                raise HTTPException(404, f"No hay rango guardado para {spec.saved_player!r}")
            m = HandTypeMatrix()
            m.paint(state.saved_ranges[spec.saved_player])
            return m
        raise HTTPException(400, f"Método de rango inválido: {spec.method!r} (usar 'random' no pasa por acá)")
    except NotationError as e:
        raise HTTPException(400, f"Notación inválida: {e}")
    except ValueError as e:
        raise HTTPException(400, str(e))


def range_spec_to_engine_range(spec: RangeSpec, state: AppState) -> Range:
    if spec.method == "random":
        return Range.random()
    matrix = range_spec_to_matrix(spec, state)
    combos = matrix.expand_to_weighted_combos()
    if not combos:
        raise HTTPException(400, "El rango especificado quedó vacío")
    return Range.from_combos(combos)
