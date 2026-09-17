"""
Punto 11 — Núcleo: mezcla CONTINUA (nunca un interruptor binario ni
umbrales duros con if/else), rampa de confianza, dos amortiguadores,
y generación de la razón en texto.

recomendación = (peso_explotador × línea_explotadora) + ((1 − peso_explotador) × línea_GTO)
"""
from __future__ import annotations
from dataclasses import dataclass

from ..ranges.hand_types import ALL_HAND_TYPES
from ..ranges.matrix import HandTypeMatrix
from ..icm.penalty import ICMPenaltyResult
from ..self_image.relevance import RelevanceEstimate

# constantes ajustables, documentadas explícitamente (el resumen
# técnico no las fija con un número, solo pide que existan)
SELF_IMAGE_DAMPER_STRENGTH = 0.5   # un rival que ajusta TOTALMENTE (relevance=1.0) corta el peso explotador a la mitad, no a cero
ICM_DAMPER_STRENGTH = 0.7           # presión de ICM severa corta el peso explotador hasta un 70%, nunca a cero


def blend_matrices(gto: HandTypeMatrix, exploit: HandTypeMatrix, weight_exploit: float) -> HandTypeMatrix:
    if not (0.0 <= weight_exploit <= 1.0):
        raise ValueError("weight_exploit debe estar entre 0.0 y 1.0")
    result = HandTypeMatrix()
    for t in ALL_HAND_TYPES:
        g = gto.get_weight(t)
        e = exploit.get_weight(t)
        result.set_weight(t, weight_exploit * e + (1 - weight_exploit) * g)
    return result


def exploit_weight_from_confidence(n_reliable_observations: int, confidence_target: int) -> float:
    """
    Rampa: crece linealmente con la confianza hasta saturar en 1.0.
    Con 0 observaciones da 0.0 -> default seguro, línea GTO pura
    (defendible porque, por construcción teórica, una línea
    balanceada no se puede explotar en contra).
    """
    if confidence_target <= 0:
        raise ValueError("confidence_target debe ser positivo")
    return min(1.0, max(0.0, n_reliable_observations / confidence_target))


def _damper_self_image(relevance: RelevanceEstimate | None) -> tuple[float, str]:
    if relevance is None:
        return 1.0, "sin dato de imagen propia -> sin amortiguador"
    factor = 1.0 - relevance.weight * SELF_IMAGE_DAMPER_STRENGTH
    reason = (
        f"amortiguador por imagen propia: rival con relevancia {relevance.weight:.2f} "
        f"({relevance.source}) -> peso explotador ×{factor:.2f}"
    )
    return factor, reason


def _damper_icm(icm_penalty: ICMPenaltyResult | None) -> tuple[float, str]:
    if icm_penalty is None or not icm_penalty.applies:
        return 1.0, "sin presión de ICM (cash game o sin dato) -> sin amortiguador"
    ev_ref = max(abs(icm_penalty.ev_before_dollars or 0.0), 1e-9)
    pressure_ratio = min(1.0, abs(icm_penalty.icm_penalty_dollars or 0.0) / ev_ref)
    factor = 1.0 - pressure_ratio * ICM_DAMPER_STRENGTH
    reason = (
        f"amortiguador por presión de ICM: penalty ${icm_penalty.icm_penalty_dollars:.2f} "
        f"sobre ${icm_penalty.ev_before_dollars:.2f} de EV -> peso explotador ×{factor:.2f}"
    )
    return factor, reason


@dataclass
class ExploitVsGTODecision:
    blended_range: HandTypeMatrix
    weight_exploit_raw: float               # antes de amortiguadores
    weight_exploit_final: float               # el que efectivamente se usó
    damper_self_image: float
    damper_icm: float
    reasoning: str


def decide_gto_vs_exploit(
    gto_line: HandTypeMatrix,
    exploit_line: HandTypeMatrix,
    n_reliable_observations: int,
    confidence_target: int,
    self_image_relevance: RelevanceEstimate | None = None,
    icm_penalty: ICMPenaltyResult | None = None,
) -> ExploitVsGTODecision:
    raw_weight = exploit_weight_from_confidence(n_reliable_observations, confidence_target)

    damper_img, reason_img = _damper_self_image(self_image_relevance)
    damper_icm_val, reason_icm = _damper_icm(icm_penalty)

    final_weight = max(0.0, min(1.0, raw_weight * damper_img * damper_icm_val))
    blended = blend_matrices(gto_line, exploit_line, final_weight)

    reasoning = (
        f"Peso explotador base: {raw_weight:.2f} "
        f"({n_reliable_observations} observaciones confiables / umbral {confidence_target}). "
        f"{reason_img}. {reason_icm}. "
        f"Peso explotador final: {final_weight:.2f} "
        f"({final_weight*100:.0f}% línea explotadora, {(1-final_weight)*100:.0f}% línea GTO)."
    )

    return ExploitVsGTODecision(
        blended_range=blended,
        weight_exploit_raw=raw_weight,
        weight_exploit_final=final_weight,
        damper_self_image=damper_img,
        damper_icm=damper_icm_val,
        reasoning=reasoning,
    )
