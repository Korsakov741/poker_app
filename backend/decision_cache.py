"""
Cache en memoria de los DecisionPackage recientes — permite que el
frontend pida "registrar qué hice realmente" sin tener que
reenviar todo el paquete de vuelta. No necesita persistir a disco:
si el proceso se reinicia, se pierden los paquetes sin registrar
todavía (aceptable, es solo el puente entre "ver la recomendación" y
"decir qué hice" dentro de la misma sesión de uso).
"""
from __future__ import annotations
import uuid

from poker_engine.final_decision import DecisionPackage

_cache: dict[str, DecisionPackage] = {}
_MAX_SIZE = 500


def store(package: DecisionPackage) -> str:
    if len(_cache) > _MAX_SIZE:
        # descartar las más viejas (dict mantiene orden de inserción en Python moderno)
        oldest = next(iter(_cache))
        del _cache[oldest]
    decision_id = str(uuid.uuid4())
    _cache[decision_id] = package
    return decision_id


def get(decision_id: str) -> DecisionPackage | None:
    return _cache.get(decision_id)
