"""Statistica minima, senza dipendenze, per non sovrainterpretare pochi task.

- `wilson`: intervallo di confidenza al 95% per una proporzione (k successi su n). A differenza
  dell'intervallo "normale" funziona bene con n piccolo e con proporzioni vicine a 0 o 100%.
- `mcnemar_exact`: test esatto per confrontare DUE run sugli stessi task. Conta solo i task che
  cambiano esito (b = migliorati, c = peggiorati) e chiede: se non ci fosse alcuna differenza reale,
  quanto è probabile uno squilibrio così? Con pochi task discordanti il p-value resta alto.
"""
from __future__ import annotations

from math import comb, sqrt


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b: int, c: int) -> float:
    """p-value a due code del test esatto (binomiale con p = 0,5) su b + c task discordanti."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def fmt_ci(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%, IC 95% {100 * lo:.0f}–{100 * hi:.0f}%)" if n else "—"


def cohen_kappa(both_pass: int, a_only: int, b_only: int, both_fail: int) -> float | None:
    """Accordo tra due valutatori binari oltre quello dovuto al caso (1 = perfetto, 0 = come tirare una moneta).
    a_only = passato solo per A; b_only = passato solo per B. None se non definito."""
    n = both_pass + a_only + b_only + both_fail
    if n == 0:
        return None
    po = (both_pass + both_fail) / n
    pa, pb = (both_pass + a_only) / n, (both_pass + b_only) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)
