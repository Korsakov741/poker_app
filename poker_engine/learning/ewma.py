"""
Punto 9 — El mecanismo de actualización en sí (no lógica de negocio
propia, tal como aclara el resumen técnico). Un EWMATracker por cada
cantidad que se quiere seguir con "más peso a lo reciente" en vez de
promedio acumulado plano.

nuevo_promedio = (peso × valor_nuevo) + ((1 − peso) × promedio_anterior)
"""
from __future__ import annotations
from dataclasses import dataclass, field

# dos configuraciones de peso, tal como pide el resumen técnico —
# nunca una sola constante para todo
EWMA_WEIGHT_HIGH_VOLUME = 0.03   # VPIP, PFR — se actualizan casi cada mano
EWMA_WEIGHT_SPARSE = 0.20         # sizing-tells — solo en showdown, dato escaso


@dataclass
class EWMATracker:
    weight: float
    value: float | None = None
    confidence: int = 0                     # crece +1 por observación, SIN decaimiento
    history: list[float] = field(default_factory=list)  # un valor por observación, no solo el último

    def update(self, new_observation: float) -> None:
        if not (0.0 <= new_observation <= 1.0):
            raise ValueError("Las observaciones de este tracker son señales 0/1 (o fracciones en [0,1])")
        if self.value is None:
            self.value = new_observation  # primera observación: arranca directo en ese valor
        else:
            self.value = self.weight * new_observation + (1 - self.weight) * self.value
        self.confidence += 1
        self.history.append(self.value)
