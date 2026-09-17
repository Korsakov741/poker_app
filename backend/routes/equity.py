from __future__ import annotations
from fastapi import APIRouter, HTTPException

from poker_engine.equity import calculate_equity

from ..schemas import EquityRequest
from ..range_conversion import range_spec_to_engine_range
from ..state import state

router = APIRouter(prefix="/api/equity", tags=["equity"])


@router.post("")
def compute_equity(req: EquityRequest):
    try:
        opponent_ranges = [range_spec_to_engine_range(o.range, state) for o in req.opponents]
        result = calculate_equity(
            hero=req.hero, board=req.board, dead=req.dead,
            opponent_ranges=opponent_ranges, num_sims=req.num_sims,
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))

    labels = ["hero"] + [o.label for o in req.opponents]
    return {
        "mode": result.mode,
        "street": result.street,
        "num_iterations": result.num_iterations,
        "players": [
            {
                "label": labels[i] if i < len(labels) else p.label,
                "win_pct": round(p.win_pct, 2),
                "tie_pct": round(p.tie_pct, 2),
                "equity_pct": round(p.equity_pct, 2),
                "ci_low": p.ci_low,
                "ci_high": p.ci_high,
            }
            for i, p in enumerate(result.players)
        ],
        "total_equity_pct": round(result.total_equity_pct(), 2),
    }
