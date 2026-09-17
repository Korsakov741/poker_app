from __future__ import annotations
from fastapi import APIRouter, HTTPException

from poker_engine.session_review import record_decision

from ..schemas import RecordActualActionInput
from ..state import state
from ..decision_cache import get as get_cached_decision

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/record-action")
def record_actual_action(body: RecordActualActionInput):
    package = get_cached_decision(body.decision_id)
    if package is None:
        raise HTTPException(404, "No se encontró ese paquete de decisión (¿pasó mucho tiempo? se descartan los más viejos)")
    rd = record_decision(body.hand_id, package.street, package, body.actual_action)
    state.session_review.add(rd)
    return {
        "matched_recommendation": rd.matched_top_recommendation,
        "value_gap": round(rd.value_gap, 4),
        "best_recommendation": rd.best_recommendation,
    }


@router.get("/review")
def get_review():
    return state.session_review.summary()


@router.get("/review/hands-to-review")
def hands_to_review(top_n: int = 10):
    decisions = state.session_review.hands_to_review(top_n)
    return {
        "hands": [
            {
                "hand_id": d.hand_id, "street": d.street,
                "actual_action": d.actual_action_taken,
                "best_recommendation": d.best_recommendation,
                "value_gap": round(d.value_gap, 4),
            }
            for d in decisions
        ]
    }
