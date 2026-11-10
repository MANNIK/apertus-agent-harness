"""Execution accuracy: confronto deterministico tra il risultato della query del modello e quello della query gold.

Nessun LLM e nessun testo di query: conta solo il risultato eseguito. Le regole sono dichiarate qui UNA volta e valgono per
tutte le condizioni (originale, WSP, LoRA). Non vanno ammorbidite dopo aver visto risultati di modelli: ogni cambiamento va in
`docs/analysis_plan.md` → Deviations.

Regole
- Righe: confronto come **multiinsieme** (i duplicati contano). L'ordine delle righe conta **solo** se il task dichiara
  `order_matters: true` (la domanda chiede un ordinamento; la query gold deve avere un ordinamento totale, senza pareggi).
- Colonne: contano il **numero** e l'**ordine** (confronto per posizione); i **nomi** sono ignorati. Colonne in più o in meno = errore.
- NULL: NULL = NULL; NULL è diverso da 0, da stringa vuota e da `false`.
- Numeri (int, float, Decimal): uguali se `math.isclose(rel_tol=1e-9, abs_tol=1e-6)`; due interi si confrontano esattamente. `3` = `3.0`.
  Un valore non arrotondato non equivale a uno arrotondato dal gold (es. `ROUND(x, 2)`): se la domanda richiede un arrotondamento, il gold lo applica.
- Booleani: uguali solo a booleani. Stringhe: confronto esatto, maiuscole/minuscole e spazi contano. Date/ore: uguali solo a valori dello stesso tipo
  (una data convertita in testo non equivale alla data).
- NaN = NaN.
- **Misura secondaria «rilassata» (`compare_projection`)**: accetta colonne in più e in ordine diverso, se esiste una scelta ordinata di colonne del risultato che, dopo la proiezione,
  soddisfa le regole sopra. Serve a separare «ha sbagliato la query» da «ha aggiunto una colonna utile» (es. nome e conteggio quando si chiede solo il nome). Non sostituisce la misura rigida (primaria).
- Limite noto: con righe non ordinate si ordinano entrambi i lati con una chiave arrotondata e poi si confronta con la tolleranza; un caso di
  valori a cavallo dell'arrotondamento e uguali in tutte le altre colonne potrebbe dare un falso negativo (non osservato, solo teorico).
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

REL_TOL = 1e-9
ABS_TOL = 1e-6


@dataclass
class SqlResult:
    columns: list[str]
    rows: list[tuple[Any, ...]] = field(default_factory=list)


@dataclass
class Match:
    ok: bool
    reason: str


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def values_equal(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_number(a) and _is_number(b):
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        fa, fb = float(a), float(b)
        if math.isnan(fa) or math.isnan(fb):
            return math.isnan(fa) and math.isnan(fb)
        return math.isclose(fa, fb, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    if type(a) is not type(b):
        return False
    return a == b


def _sort_key_value(v: Any) -> tuple[int, Any]:
    """Chiave totale tra tipi diversi, per ordinare righe da confrontare come multiinsieme."""
    if v is None:
        return (0, 0)
    if isinstance(v, bool):
        return (1, int(v))
    if _is_number(v):
        f = float(v)
        return (5, 0.0) if math.isnan(f) else (2, round(f, 4))
    if isinstance(v, str):
        return (3, v)
    return (4, f"{type(v).__name__}:{v}")


def _row_key(row: tuple[Any, ...]) -> tuple[tuple[int, Any], ...]:
    return tuple(_sort_key_value(v) for v in row)


def compare_results(pred: SqlResult, gold: SqlResult, order_matters: bool = False) -> Match:
    """Esito del confronto secondo le regole del modulo; `reason` spiega il primo difetto trovato."""
    if len(pred.columns) != len(gold.columns):
        return Match(False, f"numero di colonne diverso: {len(pred.columns)} invece di {len(gold.columns)}")
    if len(pred.rows) != len(gold.rows):
        return Match(False, f"numero di righe diverso: {len(pred.rows)} invece di {len(gold.rows)}")
    p, g = list(pred.rows), list(gold.rows)
    if not order_matters:
        p.sort(key=_row_key)
        g.sort(key=_row_key)
    for i, (rp, rg) in enumerate(zip(p, g)):
        for j, (vp, vg) in enumerate(zip(rp, rg)):
            if not values_equal(vp, vg):
                return Match(False, f"riga {i + 1}, colonna {j + 1}: {vp!r} invece di {vg!r}")
    return Match(True, f"risultato uguale ({len(g)} righe, {len(g[0]) if g else len(gold.columns)} colonne)")


def compare_projection(pred: SqlResult, gold: SqlResult, order_matters: bool = False, max_cols: int = 8) -> Match:
    """Execution accuracy rilassata: il gold è una proiezione (ordinata) del risultato del modello. Più permissiva di `compare_results`, mai più severa."""
    k, n = len(gold.columns), len(pred.columns)
    if n < k:
        return Match(False, f"colonne insufficienti: {n} invece di almeno {k}")
    if len(pred.rows) != len(gold.rows):
        return Match(False, f"numero di righe diverso: {len(pred.rows)} invece di {len(gold.rows)}")
    if n > max_cols:
        return Match(False, f"troppe colonne ({n}) per la proiezione")
    for idx in itertools.permutations(range(n), k):
        proj = SqlResult([pred.columns[i] for i in idx], [tuple(r[i] for i in idx) for r in pred.rows])
        if compare_results(proj, gold, order_matters).ok:
            return Match(True, f"le colonne {[i + 1 for i in idx]} del risultato coincidono con il gold")
    return Match(False, "nessuna scelta di colonne coincide con il gold")
