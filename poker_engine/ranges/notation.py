"""
Parser de notación abreviada de rangos — el método de entrada manual
(c) del Punto 2. Notación estándar de la industria (estilo
PokerStove/Equilab), NO inventada acá, pero documento explícitamente
el subconjunto soportado porque varía un poco entre herramientas.

SOPORTADO:
  - Tipo exacto:              "AKs", "TT", "72o"
  - "+" en pares:              "77+"           -> 77,88,99,TT,JJ,QQ,KK,AA
  - "+" en suited/offsuit
    (mismo rango top,
    sube el kicker):           "A9s+"          -> A9s,ATs,AJs,AQs,AKs
                                "KJo+"          -> KJo,KQo
  - Rango entre dos tipos
    del mismo rango top:       "A9s-A5s"       -> A5s,A6s,A7s,A8s,A9s
                                "77-99"         -> 77,88,99
  - Peso explícito opcional
    por token:                 "AKo:0.5"       -> AKo con peso 0.5 (default 1.0)
  - Separador: coma. Espacios se ignoran.

NO SOPORTADO (se levanta un error claro, no se adivina):
  - Rangos de conectores con distinto rango top: "98s-54s"
  - Notación de rango completo tipo "ATs+, KTs+" combinado con gaps
    (esto sí funciona, cada token es independiente — lo que NO
    funciona es un ÚNICO token que mezcle tops distintos)
"""
from __future__ import annotations
import re

from .hand_types import ALL_HAND_TYPES, RANKS_DESC, is_pair, validate_hand_type

_VALID_TYPES = set(ALL_HAND_TYPES)


class NotationError(ValueError):
    pass


def _rank_idx(r: str) -> int:
    return RANKS_DESC.index(r)


def _parse_token(token: str) -> list[tuple[str, float]]:
    """Devuelve [(hand_type, weight), ...] para un solo token."""
    token = token.strip()
    if not token:
        return []

    weight = 1.0
    if ":" in token:
        token, weight_str = token.split(":", 1)
        token = token.strip()
        try:
            weight = float(weight_str.strip())
        except ValueError:
            raise NotationError(f"Peso inválido en token {token!r}: {weight_str!r}")
        if not (0.0 <= weight <= 1.0):
            raise NotationError(f"Peso fuera de rango [0,1] en token: {token}:{weight_str}")

    # --- Rango entre dos tipos: "A9s-A5s" o "77-99" ---
    if "-" in token:
        left, right = [t.strip() for t in token.split("-", 1)]
        return _parse_range(left, right, weight)

    # --- "+" ---
    if token.endswith("+"):
        base = token[:-1]
        return _parse_plus(base, weight)

    # --- tipo exacto ---
    t = _normalize_type_str(token)
    validate_hand_type(t)
    return [(t, weight)]


def _normalize_type_str(s: str) -> str:
    """Acepta 'aks', 'AKS', 'AK' (asume offsuit si no se especifica... no, exigimos explícito)."""
    s = s.strip()
    if len(s) == 2:
        # par, ej "TT" — o el usuario se olvidó del sufijo en suited/offsuit
        if s[0] == s[1]:
            return s.upper()
        raise NotationError(
            f"Falta sufijo 's' u 'o' en {s!r} (¿quisiste decir '{s.upper()}s' o '{s.upper()}o'?)"
        )
    if len(s) == 3:
        r1, r2, suit = s[0].upper(), s[1].upper(), s[2].lower()
        if suit not in ("s", "o"):
            raise NotationError(f"Sufijo inválido en {s!r}, debe ser 's' u 'o'")
        # normalizar orden: rango más fuerte primero
        if _rank_idx(r1) > _rank_idx(r2):
            r1, r2 = r2, r1
        return r1 + r2 + suit
    raise NotationError(f"Token con formato inválido: {s!r}")


def _parse_plus(base: str, weight: float) -> list[tuple[str, float]]:
    base_t = _normalize_type_str(base)
    validate_hand_type(base_t)

    if is_pair(base_t):
        start_idx = _rank_idx(base_t[0])
        # pares van de ese rango hacia arriba (más fuertes = índice menor)
        ranks = RANKS_DESC[:start_idx + 1]
        return [(r + r, weight) for r in ranks]

    top, kicker, suit = base_t[0], base_t[1], base_t[2]
    top_idx = _rank_idx(top)
    kicker_idx = _rank_idx(kicker)
    if kicker_idx <= top_idx:
        raise NotationError(f"Token inválido para '+': {base!r}")
    # kicker sube (índice baja) hasta quedar justo debajo del top
    result = []
    for idx in range(kicker_idx, top_idx, -1):
        r2 = RANKS_DESC[idx]
        result.append((top + r2 + suit, weight))
    return result


def _parse_range(left: str, right: str, weight: float) -> list[tuple[str, float]]:
    left_t = _normalize_type_str(left)
    right_t = _normalize_type_str(right)
    validate_hand_type(left_t)
    validate_hand_type(right_t)

    if is_pair(left_t) != is_pair(right_t):
        raise NotationError(f"No se puede mezclar par con no-par en un rango: {left}-{right}")

    if is_pair(left_t):
        i1, i2 = _rank_idx(left_t[0]), _rank_idx(right_t[0])
        lo, hi = min(i1, i2), max(i1, i2)
        return [(RANKS_DESC[i] + RANKS_DESC[i], weight) for i in range(lo, hi + 1)]

    # no-par: exigir mismo "top" y mismo sufijo (soportado); si no, error explícito
    if left_t[0] != right_t[0] or left_t[2] != right_t[2]:
        raise NotationError(
            f"Rango no soportado: {left}-{right} — este parser solo soporta rangos "
            f"que comparten el mismo rango top y el mismo sufijo (s/o). "
            f"Rangos de conectores con distinto top (ej. '98s-54s') no están soportados."
        )
    top = left_t[0]
    suit = left_t[2]
    i1, i2 = _rank_idx(left_t[1]), _rank_idx(right_t[1])
    lo, hi = min(i1, i2), max(i1, i2)
    top_idx = _rank_idx(top)
    result = []
    for idx in range(lo, hi + 1):
        if idx == top_idx:
            continue  # evitar generar el "par" por accidente
        result.append((top + RANKS_DESC[idx] + suit, weight))
    return result


def parse_notation(notation: str) -> dict[str, float]:
    """
    Parsea una notación completa tipo "22+, A9s+, KJo+" y devuelve un
    dict {tipo: peso}. Si un tipo aparece en más de un token, se
    queda con el peso MÁS ALTO (no se suman ni se pisan a ciegas).
    """
    result: dict[str, float] = {}
    for raw_token in notation.split(","):
        for hand_type, weight in _parse_token(raw_token):
            if hand_type in result:
                result[hand_type] = max(result[hand_type], weight)
            else:
                result[hand_type] = weight
    return result
