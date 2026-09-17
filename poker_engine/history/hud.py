"""
Punto 6 — Base de datos histórica de manos por jugador (estilo HUD).

Definiciones estándar de la industria (no inventadas acá, pero
documento la convención exacta elegida porque varían un poco entre
softwares de HUD):

  - VPIP: % de manos donde el jugador puso fichas de forma voluntaria
    preflop (pagar o subir) — postear ciega NO cuenta.
  - PFR: % de manos donde el jugador subió preflop (incluye el open).
  - 3-bet%: de las manos donde el jugador tuvo la OPORTUNIDAD de
    3-betear (su primera acción preflop enfrenta exactamente UNA
    subida previa), en cuántas efectivamente subió.
  - Fold-to-cbet%: de las manos donde el jugador enfrentó una
    continuation bet (el agresor preflop apuesta primero en el flop),
    en cuántas se retiró. Solo cuenta reacciones directas a ESA
    apuesta — una vez que alguien sube, dejo de contar "enfrenta el
    cbet" para los que actúan después (están enfrentando la subida,
    no el cbet original).
  - Factor de agresión (AF): (apuestas + subidas) / pagos, medido
    SOLO post-flop (convención elegida, hay softwares que lo miden en
    todas las calles — lo documento porque cambia el número).
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field

from .models import HandRecord


@dataclass
class _RawPlayerStats:
    hands_dealt: int = 0
    vpip_count: int = 0
    pfr_count: int = 0
    threebet_opportunities: int = 0
    threebet_count: int = 0
    cbet_faced: int = 0
    cbet_folded: int = 0
    postflop_bets: int = 0
    postflop_raises: int = 0
    postflop_calls: int = 0


@dataclass
class PlayerHUDStats:
    player: str
    hands_dealt: int
    vpip_pct: float | None
    pfr_pct: float | None
    threebet_pct: float | None
    threebet_opportunities: int
    fold_to_cbet_pct: float | None
    cbet_faced: int
    aggression_factor: float | None
    postflop_actions_sampled: int


def _pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator * 100


def vpip_pfr_flags_for_hand(hand: HandRecord) -> dict[str, tuple[bool, bool]]:
    """
    Señal binaria por jugador para ESTA mano puntual: (hizo_vpip,
    hizo_pfr). Función compartida — el Punto 6 la usa para el
    acumulado simple (get_stats), el Punto 9 la reusa para la señal
    por-mano que alimenta el EWMA. La REGLA vive en un solo lugar.
    """
    preflop = hand.actions_on("preflop")
    by_player: dict[str, list] = defaultdict(list)
    for a in preflop:
        by_player[a.player].append(a)

    flags: dict[str, tuple[bool, bool]] = {}
    for player in hand.players:
        acts = by_player.get(player, [])
        vpip = any(a.action_type in ("call", "bet", "raise") for a in acts)
        pfr = any(a.action_type in ("bet", "raise") for a in acts)
        flags[player] = (vpip, pfr)
    return flags


class HandHistoryDB:
    def __init__(self):
        self._stats: dict[str, _RawPlayerStats] = defaultdict(_RawPlayerStats)

    def ingest_hand(self, hand: HandRecord) -> None:
        for p in hand.players:
            self._stats[p].hands_dealt += 1
        self._process_vpip_pfr(hand)
        self._process_threebet(hand)
        self._process_cbet(hand)
        self._process_aggression(hand)

    # ---------- VPIP / PFR ----------
    def _process_vpip_pfr(self, hand: HandRecord) -> None:
        for player, (vpip, pfr) in vpip_pfr_flags_for_hand(hand).items():
            if vpip:
                self._stats[player].vpip_count += 1
            if pfr:
                self._stats[player].pfr_count += 1

    # ---------- 3-bet ----------
    def _process_threebet(self, hand: HandRecord) -> None:
        preflop = [a for a in hand.actions_on("preflop") if a.action_type != "post_blind"]
        raises_so_far = 0
        seen_players: set[str] = set()
        for a in preflop:
            if a.player not in seen_players:
                seen_players.add(a.player)
                if raises_so_far == 1:
                    self._stats[a.player].threebet_opportunities += 1
                    if a.action_type == "raise":
                        self._stats[a.player].threebet_count += 1
            if a.action_type == "raise":
                raises_so_far += 1

    # ---------- fold-to-cbet ----------
    def _process_cbet(self, hand: HandRecord) -> None:
        preflop_aggressor = None
        for a in hand.actions_on("preflop"):
            if a.action_type in ("bet", "raise"):
                preflop_aggressor = a.player
        if preflop_aggressor is None:
            return

        flop = hand.actions_on("flop")
        if not flop:
            return
        first = flop[0]
        if not (first.player == preflop_aggressor and first.action_type == "bet"):
            return  # no hubo c-bet (el agresor preflop no fue quien abrió el flop apostando)

        for a in flop[1:]:
            if a.action_type in ("fold", "call", "raise"):
                self._stats[a.player].cbet_faced += 1
                if a.action_type == "fold":
                    self._stats[a.player].cbet_folded += 1
            if a.action_type == "raise":
                break  # a partir de acá los que siguen enfrentan la subida, no el cbet original

    # ---------- factor de agresión (post-flop) ----------
    def _process_aggression(self, hand: HandRecord) -> None:
        for street in ("flop", "turn", "river"):
            for a in hand.actions_on(street):
                if a.action_type == "bet":
                    self._stats[a.player].postflop_bets += 1
                elif a.action_type == "raise":
                    self._stats[a.player].postflop_raises += 1
                elif a.action_type == "call":
                    self._stats[a.player].postflop_calls += 1

    def get_stats(self, player: str) -> PlayerHUDStats:
        s = self._stats[player]
        bets_raises = s.postflop_bets + s.postflop_raises
        af = (bets_raises / s.postflop_calls) if s.postflop_calls > 0 else None
        return PlayerHUDStats(
            player=player,
            hands_dealt=s.hands_dealt,
            vpip_pct=_pct(s.vpip_count, s.hands_dealt),
            pfr_pct=_pct(s.pfr_count, s.hands_dealt),
            threebet_pct=_pct(s.threebet_count, s.threebet_opportunities),
            threebet_opportunities=s.threebet_opportunities,
            fold_to_cbet_pct=_pct(s.cbet_folded, s.cbet_faced),
            cbet_faced=s.cbet_faced,
            aggression_factor=af,
            postflop_actions_sampled=bets_raises + s.postflop_calls,
        )

    def known_players(self) -> list[str]:
        return list(self._stats.keys())
