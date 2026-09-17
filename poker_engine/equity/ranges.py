"""
Representación de rango que consume el motor de equity (Punto 1).

IMPORTANTE — diseño pensado para el Punto 2 (que todavía no existe):
el Punto 2 promete entregarle al Punto 1 combos YA EXPANDIDOS y YA
pesados (ej. AA -> 6 combos, AKs -> 4 combos), no tipos de mano en
formato matriz 13x13. Por eso `Range` acá adentro es simplemente una
lista de (carta1, carta2, peso). Cuando el Punto 2 se construya, va a
producir objetos `Range` con este mismo formato — el motor de equity
no se toca.

Mientras el Punto 2 no exista, se usa `Range.random()` como
placeholder explícito: "cualquier mano al azar, sin sesgo", tal como
lo autoriza el propio resumen técnico del Punto 1 ("sin esto, solo
puede calcular contra mano al azar").
"""
from __future__ import annotations
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional

from .cards import FULL_DECK, normalize, validate_card


@dataclass(frozen=True)
class Combo:
    card1: str
    card2: str
    weight: float = 1.0

    def __post_init__(self):
        validate_card(self.card1)
        validate_card(self.card2)
        c1, c2 = normalize(self.card1), normalize(self.card2)
        if c1 == c2:
            raise ValueError(f"Combo inválido, misma carta repetida: {c1}")
        # orden canónico para evitar duplicados lógicos (As-Kd == Kd-As)
        object.__setattr__(self, "card1", min(c1, c2))
        object.__setattr__(self, "card2", max(c1, c2))
        if self.weight < 0 or self.weight > 1:
            raise ValueError(f"Peso fuera de rango [0,1]: {self.weight}")

    def cards(self) -> tuple[str, str]:
        return (self.card1, self.card2)


class Range:
    """
    Un rango es una lista de Combos con peso, O el placeholder
    especial `is_random=True` que representa "cualquier mano, sin
    sesgo" — usado hoy porque el Punto 2 todavía no está construido.
    """

    def __init__(self, combos: Optional[list[Combo]] = None, is_random: bool = False):
        if is_random and combos:
            raise ValueError("Un rango no puede ser random y tener combos explícitos a la vez")
        self.is_random = is_random
        self.combos: list[Combo] = combos or []
        if not is_random and not self.combos:
            raise ValueError(
                "Rango vacío: o pasás combos explícitos, o usás Range.random()"
            )

    @classmethod
    def random(cls) -> "Range":
        return cls(is_random=True)

    @classmethod
    def from_combos(cls, combos: list[tuple[str, str, float]]) -> "Range":
        return cls(combos=[Combo(c1, c2, w) for c1, c2, w in combos])

    def valid_combos(self, excluded: set[str]) -> list[Combo]:
        """
        Combos de este rango que no chocan con `excluded` (cartas ya
        usadas por hero/board/dead/otros rivales en esta simulación).
        Si el rango es random, genera dinámicamente todos los combos
        posibles del mazo restante, peso 1.0 cada uno.
        """
        if self.is_random:
            remaining = [c for c in FULL_DECK if c not in excluded]
            return [
                Combo(c1, c2, 1.0) for c1, c2 in combinations(remaining, 2)
            ]
        return [
            c for c in self.combos
            if c.card1 not in excluded and c.card2 not in excluded
        ]

    def estimated_valid_count(self, excluded: set[str]) -> int:
        """
        Tamaño del espacio válido SIN materializar la lista completa
        de combos — clave para rangos random, donde materializar
        implica generar cientos de objetos Combo solo para contarlos.
        Se usa para decidir rápido si un cálculo exacto es viable
        antes de gastar tiempo construyéndolo.
        """
        if self.is_random:
            n = len(FULL_DECK) - len(excluded)
            return n * (n - 1) // 2 if n >= 2 else 0
        return sum(
            1 for c in self.combos
            if c.card1 not in excluded and c.card2 not in excluded
        )

    def sample_one(self, excluded: set[str], rng) -> "Combo":
        """
        Samplea UN combo válido respetando pesos, sin materializar
        toda la lista cuando el rango es random (muestreo directo de
        2 cartas del mazo restante, O(1) en vez de O(n^2)).
        """
        if self.is_random:
            remaining = [c for c in FULL_DECK if c not in excluded]
            if len(remaining) < 2:
                raise RuntimeError("No quedan suficientes cartas para samplear un rango random")
            c1, c2 = rng.sample(remaining, 2)
            return Combo(c1, c2, 1.0)
        valid = self.valid_combos(excluded)
        if not valid:
            raise RuntimeError("Rango sin combos válidos dadas las cartas ya usadas")
        weights = [c.weight for c in valid]
        return rng.choices(valid, weights=weights, k=1)[0]

    def total_combo_count(self) -> int:
        """Tamaño del rango (para decidir MC vs enumeración exacta y para logs)."""
        if self.is_random:
            return len(list(combinations(FULL_DECK, 2)))
        return len(self.combos)
