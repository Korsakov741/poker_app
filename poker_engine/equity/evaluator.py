"""
Evaluador de manos — wrapper sobre `treys` (implementación probada
tipo Cactus Kev con tabla de búsqueda precalculada, tal como pide el
resumen técnico del Punto 1: "no reinventarlo").
"""
from treys import Evaluator as _TreysEvaluator

_evaluator = _TreysEvaluator()


def score(board: list[int], hand: list[int]) -> int:
    """
    Evalúa una mano de 5, 6 o 7 cartas (board + hand combinados).
    Convención de treys: SCORE MÁS BAJO = MANO MÁS FUERTE.
    """
    return _evaluator.evaluate(board, hand)


def rank_class(s: int) -> int:
    """
    Categoría numérica de la mano (convención treys: 1=escalera
    color, ..., 9=carta alta — menor número = mano más fuerte).
    """
    return _evaluator.get_rank_class(s)


def rank_class_name(s: int) -> str:
    """Nombre legible de la categoría de mano (ej. 'Two Pair')."""
    return _evaluator.class_to_string(_evaluator.get_rank_class(s))
