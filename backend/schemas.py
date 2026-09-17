from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class RangeSpec(BaseModel):
    """Las tres formas de entrada manual del Punto 2, más 'random' y 'saved'."""
    method: Literal["notation", "top_percent", "paint", "random", "saved"]
    notation: Optional[str] = None
    top_percent: Optional[float] = None
    paint: Optional[dict[str, float]] = None
    saved_player: Optional[str] = None


class OpponentInput(BaseModel):
    label: str
    range: RangeSpec


class EquityRequest(BaseModel):
    hero: tuple[str, str]
    board: list[str] = Field(default_factory=list)
    dead: list[str] = Field(default_factory=list)
    opponents: list[OpponentInput]
    num_sims: int = 25_000


class TournamentInput(BaseModel):
    payouts: list[float]
    stacks: dict[str, float]
    table_labels: list[str]
    villain_label: Optional[str] = None
    p_win: Optional[float] = None


class DecisionRequest(BaseModel):
    hero: tuple[str, str]
    board: list[str] = Field(default_factory=list)
    dead: list[str] = Field(default_factory=list)
    street: str
    facing_bet: bool
    bet: Optional[float] = None
    pot: Optional[float] = None
    primary_villain: Optional[str] = None
    opponents: list[OpponentInput] = Field(default_factory=list)
    hero_range: Optional[RangeSpec] = None
    tournament: Optional[TournamentInput] = None
    stacks: Optional[dict[str, float]] = None
    active_players: Optional[list[str]] = None
    hero_position: Optional[Literal["early", "middle", "late", "button", "sb", "bb"]] = None
    num_players: Optional[int] = None
    num_sims: int = 20_000


class ActionInput(BaseModel):
    player: str
    street: str
    action_type: str
    order: int
    pot_fraction: Optional[float] = None
    is_bluff: Optional[bool] = None


class HandSubmission(BaseModel):
    hand_id: str
    players: list[str]
    board: list[str] = Field(default_factory=list)
    actions: list[ActionInput]
    winners: list[str] = Field(default_factory=list)
    showdown: bool = False
    showdown_hands: dict[str, tuple[str, str]] = Field(default_factory=dict)


class NoteInput(BaseModel):
    player: str
    text: str
    tag: Optional[str] = None
    hand_id: Optional[str] = None


class RecordActualActionInput(BaseModel):
    decision_id: str
    hand_id: str
    actual_action: str


class SaveRangeInput(BaseModel):
    player: str
    range: RangeSpec


class SuggestRangeInput(BaseModel):
    villain_label: str
    street: str
    pot_fraction: float
    action_type: Literal["call", "bet", "raise"]
    villain_position: Optional[Literal["early", "middle", "late", "button", "sb", "bb"]] = None
    num_players: Optional[int] = None
    spr_category: Literal["push_fold", "bajo", "medio", "profundo"] = "medio"
