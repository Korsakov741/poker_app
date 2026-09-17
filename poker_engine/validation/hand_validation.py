"""
Punto 13 — Validación de datos: detectar errores de captura en vivo.

LIMITACIÓN A FLAGGEAR (importante, no está en el resumen técnico):
el resumen menciona "bote no cuadra" como ejemplo de error a
detectar, pero el modelo de datos actual (`HandRecord`/`Action`)
guarda el tamaño de apuesta como FRACCIÓN del bote (`pot_fraction`),
no como monto absoluto, y no lleva un registro de stacks/bote real a
lo largo de la mano. Con los datos disponibles HOY no se puede
validar aritmética real de bote (para eso hace falta que la capa de
captura, todavía no construida, guarde montos absolutos y stacks
iniciales — quedó anotado en NOTAS_PENDIENTES.md). Lo que SÍ se
puede validar con lo que hay: consistencia estructural y lógica de
la mano. Es un subconjunto real de "detectar errores de captura", no
el conjunto completo que promete el resumen.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..history.models import HandRecord


@dataclass
class ValidationIssue:
    severity: str    # 'error' (dato roto, no se puede confiar en la mano) | 'warning' (raro pero posible)
    message: str


def validate_hand(hand: HandRecord) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues += _validate_no_duplicate_cards(hand)
    issues += _validate_board_length_vs_actions(hand)
    issues += _validate_no_duplicate_action_order(hand)
    issues += _validate_players_referenced_exist(hand)
    issues += _validate_folded_players_dont_act_again(hand)
    issues += _validate_showdown_consistency(hand)
    return issues


def _validate_no_duplicate_cards(hand: HandRecord) -> list[ValidationIssue]:
    issues = []
    seen: dict[str, str] = {}

    def _check(card: str, source: str):
        c = card.upper()[0] + card.lower()[1]
        if c in seen and seen[c] != source:
            issues.append(ValidationIssue(
                "error", f"Carta repetida: {c} aparece en {seen[c]} y también en {source}"
            ))
        seen.setdefault(c, source)

    for c in hand.board:
        _check(c, "board")
    for player, cards in hand.showdown_hands.items():
        for c in cards:
            _check(c, f"showdown de {player}")
    return issues


def _validate_board_length_vs_actions(hand: HandRecord) -> list[ValidationIssue]:
    issues = []
    has_flop = bool(hand.actions_on("flop"))
    has_turn = bool(hand.actions_on("turn"))
    has_river = bool(hand.actions_on("river"))

    if has_flop and len(hand.board) < 3:
        issues.append(ValidationIssue("error", f"Hay acciones en el flop pero el board tiene {len(hand.board)} cartas (mínimo 3)"))
    if has_turn and len(hand.board) < 4:
        issues.append(ValidationIssue("error", f"Hay acciones en el turn pero el board tiene {len(hand.board)} cartas (mínimo 4)"))
    if has_river and len(hand.board) < 5:
        issues.append(ValidationIssue("error", f"Hay acciones en el río pero el board tiene {len(hand.board)} cartas (mínimo 5)"))
    return issues


def _validate_no_duplicate_action_order(hand: HandRecord) -> list[ValidationIssue]:
    orders = [a.order for a in hand.actions]
    dupes = {o for o in orders if orders.count(o) > 1}
    if dupes:
        return [ValidationIssue("error", f"Valores de 'order' repetidos entre acciones: {sorted(dupes)} (el orden cronológico debe ser único)")]
    return []


def _validate_players_referenced_exist(hand: HandRecord) -> list[ValidationIssue]:
    issues = []
    known = set(hand.players)
    for a in hand.actions:
        if a.player not in known:
            issues.append(ValidationIssue("error", f"Acción de {a.player!r}, que no está en hand.players"))
    for w in hand.winners:
        if w not in known:
            issues.append(ValidationIssue("error", f"Ganador {w!r} no está en hand.players"))
    for p in hand.showdown_hands:
        if p not in known:
            issues.append(ValidationIssue("error", f"Mano de showdown de {p!r}, que no está en hand.players"))
    return issues


def _validate_folded_players_dont_act_again(hand: HandRecord) -> list[ValidationIssue]:
    issues = []
    all_actions_sorted = sorted(hand.actions, key=lambda a: a.order)
    folded_at: dict[str, int] = {}
    for a in all_actions_sorted:
        if a.player in folded_at and a.order > folded_at[a.player]:
            issues.append(ValidationIssue(
                "error",
                f"{a.player} actúa de nuevo ({a.action_type} en {a.street}, orden {a.order}) "
                f"después de haberse retirado (orden {folded_at[a.player]})",
            ))
        if a.action_type == "fold":
            folded_at[a.player] = a.order
    return issues


def _validate_showdown_consistency(hand: HandRecord) -> list[ValidationIssue]:
    issues = []
    if hand.showdown and not hand.showdown_hands:
        issues.append(ValidationIssue("warning", "showdown=True pero no se registró ninguna mano mostrada"))
    if not hand.showdown and hand.showdown_hands:
        issues.append(ValidationIssue("warning", "hay manos de showdown registradas pero showdown=False"))
    if not hand.winners:
        issues.append(ValidationIssue("warning", "la mano no tiene ningún ganador registrado"))
    return issues
