from __future__ import annotations
from fastapi import APIRouter, HTTPException

from poker_engine.history import Action, HandRecord
from poker_engine.validation import validate_hand

from ..schemas import HandSubmission
from ..state import state

router = APIRouter(prefix="/api/hands", tags=["hands"])


@router.post("")
def submit_hand(body: HandSubmission):
    try:
        actions = [
            Action(
                player=a.player, street=a.street, action_type=a.action_type, order=a.order,
                pot_fraction=a.pot_fraction, is_bluff=a.is_bluff,
            )
            for a in body.actions
        ]
        hand = HandRecord(
            hand_id=body.hand_id, players=body.players, board=body.board, actions=actions,
            winners=body.winners, showdown=body.showdown, showdown_hands=body.showdown_hands,
        )
    except ValueError as e:
        raise HTTPException(400, f"Datos de mano inválidos: {e}")

    issues = validate_hand(hand)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        return {
            "accepted": False,
            "issues": [{"severity": i.severity, "message": i.message} for i in issues],
        }

    state.ingest_hand(hand)
    return {
        "accepted": True,
        "issues": [{"severity": i.severity, "message": i.message} for i in issues],
    }


@router.get("/count")
def hand_count():
    return {"count": len(state.hand_records)}
