"""
Ruta central de la app — arma un DecisionPackage con lo que haya
disponible en el pedido. Conecta los 17 puntos del motor cuando los
datos necesarios están presentes; cada pieza se degrada con
gracia (queda afuera, no rompe nada) si falta algo — mismo criterio
que ya usa el motor internamente en todos sus puntos.

El Punto 4 (tablas de apertura) y el Punto 11 (mezcla GTO/Explotador)
necesitan posición y cantidad de jugadores — si `hero_position` y
`num_players` vienen en el pedido, se conectan; si no, se omiten sin
error (se sigue viendo el resto del paquete de decisión igual).
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from poker_engine.equity import calculate_equity
from poker_engine.gto_lite.pot_math import implied_odds_adjusted_alpha
from poker_engine.gto_lite.opening_ranges import opening_range
from poker_engine.board.combos_vs_hand import combos_beating_hero
from poker_engine.profile import build_player_profile
from poker_engine.profile.sizing_tells import pot_bucket
from poker_engine.bluff_detector import detect_bluff_opportunity, MIN_OBSERVATIONS_FOLD_RATE
from poker_engine.icm import SessionMode, TournamentContext, icm_penalty_for_play
from poker_engine.table import compute_spr
from poker_engine.final_decision import build_decision_package
from poker_engine.knowledge import POPULATION_DEFAULT_STATS
from poker_engine.ranges.position_defaults import Position as PositionEnum
from poker_engine.ranges.narrowing import NarrowAction, narrow_by_action
from poker_engine.decision import decide_gto_vs_exploit
from poker_engine.learning.integration import real_narrow_by_action_ewma
from poker_engine.self_image import estimate_relevance

from ..schemas import DecisionRequest
from ..range_conversion import range_spec_to_engine_range, range_spec_to_matrix
from ..state import state, HERO_LABEL
from ..decision_cache import store as store_decision

router = APIRouter(prefix="/api/decision", tags=["decision"])

GTO_EXPLOIT_CONFIDENCE_TARGET = 20  # umbral objetivo de observaciones para el peso explotador pleno (Punto 11)


@router.post("")
def compute_decision(req: DecisionRequest):
    opponent_ranges = {}
    for o in req.opponents:
        opponent_ranges[o.label] = range_spec_to_engine_range(o.range, state)

    equity_result = None
    if opponent_ranges:
        try:
            equity_result = calculate_equity(
                req.hero, req.board, req.dead, list(opponent_ranges.values()), num_sims=req.num_sims,
            )
        except (ValueError, RuntimeError) as e:
            raise HTTPException(400, str(e))

    implied_odds = None
    if req.facing_bet and req.bet and req.pot:
        villain_profile_for_odds = None
        if req.primary_villain:
            villain_profile_for_odds = build_player_profile(req.primary_villain, state.hud_db, state.notes_store)
        # req.pot es el bote ANTES de la apuesta que se está pagando (así lo
        # usan el resto de los cálculos, como el tamaño de apuesta relativo
        # para las tablas de fold-rate). Pero pot_odds necesita el bote CON
        # la apuesta del rival ya adentro — si no, el alpha queda inflado
        # (pide más equity de la que hace falta en realidad). Se corrige acá.
        implied_odds = implied_odds_adjusted_alpha(req.bet, req.pot + req.bet, villain_profile_for_odds)

    primary_range = opponent_ranges.get(req.primary_villain) if req.primary_villain else None
    combos_result = None
    villain_continue_rate = None
    bluff_opportunity = None

    if primary_range is not None and len(req.board) >= 3:
        try:
            combos_result = combos_beating_hero(req.hero, req.board, req.dead, primary_range)
        except (ValueError, RuntimeError):
            combos_result = None

        if req.bet and req.pot:
            bucket = pot_bucket(req.bet / req.pot)
            tracker = state.fold_table.get_tracker(req.primary_villain, req.street, bucket)
            if tracker is not None and tracker.confidence >= MIN_OBSERVATIONS_FOLD_RATE:
                fold_rate = tracker.value
            else:
                fold_rate = POPULATION_DEFAULT_STATS["fold_to_cbet_pct"] / 100.0
            villain_continue_rate = 1.0 - fold_rate

            if req.hero_range is not None:
                hero_matrix = range_spec_to_matrix(req.hero_range, state)
                villain_profile = build_player_profile(req.primary_villain, state.hud_db, state.notes_store)
                try:
                    bluff_opportunity = detect_bluff_opportunity(
                        hero_matrix, req.board, req.dead, primary_range, villain_profile,
                        state.fold_table, state.hero_image_table, req.street, req.bet, req.pot,
                    )
                except (ValueError, RuntimeError):
                    bluff_opportunity = None

    icm_penalty = None
    if req.tournament is not None and req.tournament.villain_label and req.tournament.p_win is not None and req.bet:
        ctx = TournamentContext(
            payouts=req.tournament.payouts, stacks=req.tournament.stacks,
            hero_label=HERO_LABEL, table_labels=set(req.tournament.table_labels),
        )
        session_mode = SessionMode.tournament_mode(ctx)
        try:
            icm_penalty = icm_penalty_for_play(session_mode, req.tournament.villain_label, req.bet, req.tournament.p_win)
        except (ValueError, RuntimeError) as e:
            raise HTTPException(400, f"Error de ICM: {e}")

    spr = None
    if req.stacks:
        try:
            spr = compute_spr(req.stacks, req.pot or 1.0, set(req.active_players) if req.active_players else None)
        except ValueError:
            spr = None

    bet_fraction_of_stack = None
    if req.bet and req.stacks and HERO_LABEL in req.stacks and req.stacks[HERO_LABEL] > 0:
        bet_fraction_of_stack = req.bet / req.stacks[HERO_LABEL]

    # ---------- Punto 4 + Punto 11: tablas de apertura + mezcla GTO/Explotador ----------
    gto_exploit = None
    if req.hero_position and req.num_players and req.primary_villain and primary_range is not None:
        spr_category = spr.category if spr is not None else "medio"
        position_enum = PositionEnum(req.hero_position)
        try:
            gto_line = opening_range(position_enum, req.num_players, spr_category)
        except ValueError:
            gto_line = None

        if gto_line is not None:
            action_type = NarrowAction.RAISE if req.facing_bet else NarrowAction.BET
            if req.street != "preflop":
                # heurística simple: una pasada de narrowing genérico por haber
                # llegado post-flop, además de la que ya aplica la línea explotadora abajo
                gto_line = narrow_by_action(gto_line, action_type)

            exploit_line = gto_line
            n_obs = 0
            if req.bet and req.pot:
                learning_state = state.learning_store.get_state(req.primary_villain)
                exploit_line, adjust_info = real_narrow_by_action_ewma(
                    gto_line, req.primary_villain, req.street, req.bet / req.pot,
                    action_type, learning_state,
                )
                n_obs = adjust_info.get("n_observations", 0)

            villain_profile_full = build_player_profile(req.primary_villain, state.hud_db, state.notes_store)
            relevance = estimate_relevance(villain_profile_full)

            gto_exploit = decide_gto_vs_exploit(
                gto_line=gto_line, exploit_line=exploit_line,
                n_reliable_observations=n_obs, confidence_target=GTO_EXPLOIT_CONFIDENCE_TARGET,
                self_image_relevance=relevance, icm_penalty=icm_penalty,
            )

    package = build_decision_package(
        street=req.street, facing_bet=req.facing_bet, hero_label=HERO_LABEL,
        equity_result=equity_result, implied_odds=implied_odds, combos_result=combos_result,
        villain_continue_rate=villain_continue_rate, bluff_opportunity=bluff_opportunity,
        gto_exploit=gto_exploit, icm_penalty=icm_penalty, spr=spr,
        proposed_bet_fraction_of_stack=bet_fraction_of_stack,
    )

    decision_id = store_decision(package)

    return {
        "decision_id": decision_id,
        "street": package.street,
        "legal_actions": package.legal_actions,
        "blocked_by_validation": package.blocked_by_validation,
        "validation_issues": [{"severity": i.severity, "message": i.message} for i in package.validation_issues],
        "candidates": [
            {
                "action": c.action,
                "heuristic_value": round(c.heuristic_value, 4),
                "top_reasons": c.top_reasons,
            }
            for c in package.candidates
        ],
        "equity": None if equity_result is None else {
            "mode": equity_result.mode,
            "players": [
                {
                    "label": (["hero"] + list(opponent_ranges.keys()))[i] if i < len(opponent_ranges) + 1 else p.label,
                    "equity_pct": round(p.equity_pct, 1), "ci_low": p.ci_low, "ci_high": p.ci_high,
                }
                for i, p in enumerate(equity_result.players)
            ],
        },
        "bluff_opportunity": None if bluff_opportunity is None else {
            "estimated_success_pct": round(bluff_opportunity.estimated_success_pct, 1),
            "min_required_pct": round(bluff_opportunity.min_required_pct, 1),
            "is_above_threshold": bluff_opportunity.is_above_threshold,
            "top_candidates": [
                {"hand_type": c.hand_type, "combined_score": c.combined_score}
                for c in bluff_opportunity.candidate_combos[:5]
            ],
        },
        "gto_exploit": None if gto_exploit is None else {
            "weight_exploit_final": round(gto_exploit.weight_exploit_final, 3),
            "reasoning": gto_exploit.reasoning,
        },
    }
