"""
Punto 14 — Base de conocimiento teórica codificada.

Esta es la primera pieza concreta (A): un prior poblacional por
defecto, priorizado explícitamente antes que (B) según tu propio
resumen técnico ("impacto inmediato en dos puntos ya construidos —
2 y 11 — vs. mejora de un punto que ya funciona razonablemente — 4").

IMPORTANTE SOBRE LA FUENTE: estos números son valores de referencia
de población AMPLIAMENTE citados en software y contenido de
entrenamiento de póker (trackers, HUDs, literatura de estrategia en
general) — no son una transcripción de ningún libro puntual, y no
pretenden tener precisión científica. Son un punto de partida
razonable, no un hecho medido por esta app. Cuando haya volumen real
de datos propios (vía el Punto 6/9), esos datos reales SIEMPRE deben
pesar más que este prior — esto es exactamente lo que ya hace el
Punto 9 (el prior es el arranque antes de la primera observación, el
EWMA lo va reemplazando con evidencia real mano a mano).

Conceptos codificados acá con lógica y palabras propias — NUNCA
transcriptos ni parafraseados de cerca de ningún libro de los
mencionados en el roadmap (Sklansky, Chen & Ankenman, Brokos, Janda,
Miller): son solo números de referencia + la lógica de cómo se usan,
no explicaciones redactadas de ningún autor.
"""
from __future__ import annotations

# valores de referencia poblacionales — rangos ampliamente citados en
# software/análisis de póker para partidas de cash online full-ring;
# torneos y otros formatos varían, pero sirven como punto de partida
# razonable hasta tener datos propios
POPULATION_DEFAULT_STATS = {
    "vpip_pct": 24.0,
    "pfr_pct": 17.0,
    "threebet_pct": 7.0,
    "fold_to_cbet_pct": 48.0,
    "aggression_factor": 2.2,
}


def population_informed_keep_fractions() -> dict[str, float]:
    """
    Deriva keep_fractions para el narrowing genérico del Punto 2 a
    partir del factor de agresión poblacional, en vez de constantes
    arbitrarias sin ningún respaldo (que es lo que había antes).

    LÓGICA (propia, no de ningún libro): a mayor factor de agresión
    poblacional, una acción agresiva (subir/apostar) es más COMÚN en
    la población general y por lo tanto MENOS informativa sobre la
    fuerza real de la mano — así que el rango se angosta MENOS. Cada
    tipo de acción usa una constante de saturación distinta, reflejando
    que una subida es una señal más fuerte que un pago, sin importar
    la agresión poblacional de base:
        keep_fraction = AF_poblacional / (AF_poblacional + saturación_de_la_acción)

    Nota honesta: con AF=2.2, esta fórmula da valores muy parecidos a
    las constantes arbitrarias originales del Punto 2 (0.33/0.5/0.7).
    Es una coincidencia tranquilizadora, no evidencia de que la
    fórmula sea la "correcta" — sigue siendo una heurística, no algo
    derivado rigurosamente.
    """
    af = POPULATION_DEFAULT_STATS["aggression_factor"]
    return {
        "raise": af / (af + 4.0),
        "bet": af / (af + 2.0),
        "call": af / (af + 0.9),
    }
