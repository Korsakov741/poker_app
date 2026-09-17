"""Punto 8 — Determinación del conjunto de acciones legales."""
from __future__ import annotations


def legal_actions(facing_bet: bool) -> list[str]:
    """
    Sin nada que pagar: check o bet (retirarse no es una acción legal
    cuando no hay nada que pagar). Con algo que pagar: fold, call o
    raise.
    """
    if facing_bet:
        return ["fold", "call", "raise"]
    return ["check", "bet"]
