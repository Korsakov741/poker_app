from __future__ import annotations
from fastapi import APIRouter, HTTPException

from poker_engine.profile import build_player_profile

from ..schemas import NoteInput
from ..state import state

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/{player}/profile")
def get_profile(player: str):
    profile = build_player_profile(player, state.hud_db, state.notes_store)
    stats = state.hud_db.get_stats(player)
    return {
        "player": player,
        "hands_dealt": stats.hands_dealt,
        "vpip_pct": stats.vpip_pct,
        "pfr_pct": stats.pfr_pct,
        "threebet_pct": stats.threebet_pct,
        "fold_to_cbet_pct": stats.fold_to_cbet_pct,
        "aggression_factor": stats.aggression_factor,
        "tightness_score": profile.effective_tightness,
        "aggression_score": profile.effective_aggression,
        "notes": [{"text": n.text, "tag": n.tag} for n in profile.notes],
    }


@router.get("")
def list_players():
    return {"players": state.hud_db.known_players()}


@router.post("/notes")
def add_note(body: NoteInput):
    note = state.notes_store.add_note(body.player, body.text, tag=body.tag, hand_id=body.hand_id)
    state._save_notes()
    return {"added": True, "player": body.player, "text": note.text}


@router.get("/{player}/notes")
def get_notes(player: str):
    notes = state.notes_store.get_notes(player)
    return {"player": player, "notes": [{"text": n.text, "tag": n.tag} for n in notes]}
