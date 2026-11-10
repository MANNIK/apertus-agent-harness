"""Strumenti sui pesi per Weight-Space Programming (W06): ispezione selettiva, modifica REVERSIBILE, conteggio esatto, impronte e registro.

Indipendente dal metodo WSP scelto (A/B/C in docs/wsp_candidate_methods.md). Lavora su dizionari `{nome: numpy.ndarray}`; richiede l'extra `wsp`
(numpy, ml_dtypes). NON è importato dal resto del pacchetto e **non si usa sui pesi veri nei test** (solo tensori sintetici piccoli).

Scelte di progetto (verificate dai test):
- **Annullamento esatto = conservare i valori originali.** In bf16/fp16 «aggiungi Δ poi sottrai Δ» NON riporta al valore di partenza (arrotondamenti):
  `apply_delta` restituisce un `Patch` che contiene i valori originali dei soli elementi cambiati; `revert` li rimette → tensore **identico bit a bit**.
- **Parametri modificati = quelli che cambiano DAVVERO dopo l'arrotondamento nel dtype del tensore**, non quelli con Δ ≠ 0 (un Δ minuscolo può essere inghiottito in bf16).
- Impronte sha256 su (dtype, forma, byte) per ogni tensore toccato, prima e dopo; impronta del checkpoint = sha256 delle impronte dei tensori in ordine di nome.
- Il registro (JSONL, una riga per modifica) dice quali tensori, quanti parametri (numero e %), norma di Δ e perché (`note`): anche per le modifiche scartate.
- Lettore/scrittore minimale del formato safetensors (intestazione JSON + byte grezzi) con lettura per nome via mmap, perché la libreria ufficiale non gestisce bf16 con numpy.
"""
from __future__ import annotations

import hashlib
import json
import mmap
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ml_dtypes
import numpy as np

_ST_DTYPES = {"F64": np.float64, "F32": np.float32, "F16": np.float16, "BF16": ml_dtypes.bfloat16,
              "I64": np.int64, "I32": np.int32, "I16": np.int16, "I8": np.int8, "U8": np.uint8, "BOOL": np.bool_}
_NP_TO_ST = {np.dtype(v): k for k, v in _ST_DTYPES.items()}


# --------------------------------------------------------------------------- impronte e ispezione

def tensor_hash(a: np.ndarray) -> str:
    """sha256 su dtype, forma e byte (ordine C): cambia se cambia un solo elemento, la forma o il tipo."""
    h = hashlib.sha256()
    h.update(f"{a.dtype.name}|{tuple(a.shape)}|".encode())
    h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def checkpoint_hash(weights: dict[str, np.ndarray]) -> str:
    h = hashlib.sha256()
    for name in sorted(weights):
        h.update(name.encode() + b"=" + tensor_hash(weights[name]).encode() + b";")
    return h.hexdigest()


def spectral_norm(a: np.ndarray, iters: int = 60) -> float:
    """Norma spettrale (valore singolare massimo) per iterazione di potenza, deterministica (seme fisso). Sufficiente per matrici grandi."""
    m = a.astype(np.float32)
    v = np.random.default_rng(0).standard_normal(m.shape[1]).astype(np.float32)
    v /= np.linalg.norm(v) or 1.0
    s = 0.0
    for _ in range(iters):
        u = m @ v
        nu = float(np.linalg.norm(u))
        if nu == 0.0:
            return 0.0
        u /= nu
        v = m.T @ u
        s = float(np.linalg.norm(v))
        if s == 0.0:
            return 0.0
        v /= s
    return s


def inspect_tensor(a: np.ndarray) -> dict[str, Any]:
    """Sintesi PICCOLA di un tensore (adatta a essere data a un modello di sviluppo): forma, tipo, statistiche, norme, rango stabile."""
    f = a.astype(np.float32)
    out: dict[str, Any] = {"shape": list(a.shape), "dtype": a.dtype.name, "n_params": int(a.size), "mean": float(f.mean()), "std": float(f.std()),
                           "abs_max": float(np.abs(f).max()) if a.size else 0.0, "frac_zero": float((f == 0).mean()), "norm_fro": float(np.linalg.norm(f))}
    if a.ndim == 2 and min(a.shape) > 1:
        sn = spectral_norm(a)
        out["norm_spectral"] = sn
        out["stable_rank"] = float(out["norm_fro"] ** 2 / sn ** 2) if sn > 0 else 0.0  # ||W||_F² / ||W||_2²: rango «effettivo» in [1, min(forma)]
    return out


def summarize(weights: dict[str, np.ndarray], names: list[str] | None = None) -> dict[str, dict[str, Any]]:
    return {n: inspect_tensor(weights[n]) for n in (names or sorted(weights))}


# --------------------------------------------------------------------------- modifica reversibile


def _bits(a: np.ndarray) -> np.ndarray:
    c = np.ascontiguousarray(a)
    return c.view(np.dtype(f"u{c.dtype.itemsize}"))

@dataclass
class Patch:
    """Tutto ciò che serve per annullare una modifica: per ogni tensore gli indici cambiati e i loro valori originali."""
    saved: dict[str, tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)  # nome -> (indici piatti, valori originali)
    record: dict[str, Any] = field(default_factory=dict)


def apply_delta(weights: dict[str, np.ndarray], deltas: dict[str, np.ndarray], note: str = "") -> Patch:
    """Applica θ' = θ + Δ in-place (calcolo in float32, poi arrotondamento nel dtype del tensore). Restituisce il Patch con registro e valori originali."""
    total = sum(int(w.size) for w in weights.values())
    tensors, saved, modified = [], {}, 0
    for name in sorted(deltas):
        if name not in weights:
            raise KeyError(f"tensore sconosciuto: {name}")
        w, d = weights[name], deltas[name]
        if w.shape != d.shape:
            raise ValueError(f"{name}: forma di Δ {d.shape} diversa da quella del tensore {w.shape}")
        if not np.issubdtype(w.dtype, np.floating) and w.dtype != ml_dtypes.bfloat16:
            raise ValueError(f"{name}: solo tensori in virgola mobile ({w.dtype})")
        if not w.flags.c_contiguous:
            raise ValueError(f"{name}: il tensore deve essere contiguo in memoria (la modifica è in-place)")
        before_hash = tensor_hash(w)
        new = (w.astype(np.float32) + d.astype(np.float32)).astype(w.dtype)
        changed = np.flatnonzero((_bits(new) != _bits(w)).reshape(-1))  # confronto bit a bit: gestisce NaN e -0.0
        saved[name] = (changed, w.reshape(-1)[changed].copy())
        w.reshape(-1)[changed] = new.reshape(-1)[changed]
        modified += int(changed.size)
        tensors.append({"name": name, "shape": list(w.shape), "dtype": w.dtype.name, "n_delta_nonzero": int(np.count_nonzero(d)),
                        "n_changed": int(changed.size), "pct_of_tensor": 100.0 * changed.size / max(w.size, 1),
                        "delta_norm": float(np.linalg.norm(d.astype(np.float32))), "hash_before": before_hash, "hash_after": tensor_hash(w)})
    record = {"note": note, "tensors_touched": len(tensors), "n_params_modified": modified, "total_params": total,
              "pct_params_modified": 100.0 * modified / max(total, 1), "tensors": tensors}
    record["id"] = hashlib.sha256(json.dumps([note] + [(t["name"], t["hash_before"], t["hash_after"]) for t in tensors]).encode()).hexdigest()[:16]
    return Patch(saved, record)


def revert(weights: dict[str, np.ndarray], patch: Patch) -> None:
    """Rimette i valori originali: il tensore torna IDENTICO bit a bit e l'impronta coincide con `hash_before`."""
    for name, (idx, vals) in patch.saved.items():
        weights[name].reshape(-1)[idx] = vals


def append_registry(path: str | Path, record: dict[str, Any], accepted: bool | None = None, scores: dict[str, Any] | None = None) -> None:
    """Aggiunge una riga al registro JSONL (append-only). Registrare anche le modifiche scartate: altrimenti i risultati sono selezionati a posteriori."""
    row = {**record, **({"accepted": accepted} if accepted is not None else {}), **({"scores": scores} if scores else {})}
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- safetensors minimale (con bf16)

def _read_header(f) -> tuple[dict[str, Any], int]:
    n = struct.unpack("<Q", f.read(8))[0]
    if n > 100_000_000:
        raise ValueError("intestazione safetensors implausibile")
    return json.loads(f.read(n)), 8 + n


def list_tensors(path: str | Path) -> dict[str, dict[str, Any]]:
    """Nome → {dtype, shape} senza leggere i dati."""
    with Path(path).open("rb") as f:
        header, _ = _read_header(f)
    return {k: {"dtype": v["dtype"], "shape": v["shape"]} for k, v in header.items() if k != "__metadata__"}


def load_tensors(path: str | Path, names: list[str] | None = None) -> dict[str, np.ndarray]:
    """Legge solo i tensori richiesti (copia in memoria), tramite mmap."""
    out: dict[str, np.ndarray] = {}
    with Path(path).open("rb") as f:
        header, base = _read_header(f)
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for name in (names or [k for k in header if k != "__metadata__"]):
                e = header[name]
                dt = np.dtype(_ST_DTYPES[e["dtype"]])
                lo, hi = e["data_offsets"]
                out[name] = np.frombuffer(mm[base + lo:base + hi], dtype=dt).reshape(e["shape"]).copy()
    return out


def save_tensors(path: str | Path, weights: dict[str, np.ndarray], metadata: dict[str, str] | None = None) -> None:
    """Scrive un file safetensors (ordine dei tensori per nome, allineamento a 8 byte)."""
    header: dict[str, Any] = {"__metadata__": metadata} if metadata else {}
    blobs, offset = [], 0
    for name in sorted(weights):
        a = np.ascontiguousarray(weights[name])
        b = a.tobytes()
        header[name] = {"dtype": _NP_TO_ST[a.dtype], "shape": list(a.shape), "data_offsets": [offset, offset + len(b)]}
        blobs.append(b)
        offset += len(b)
    raw = json.dumps(header, separators=(",", ":")).encode()
    raw += b" " * (-len(raw) % 8)
    with Path(path).open("wb") as f:
        f.write(struct.pack("<Q", len(raw)) + raw)
        for b in blobs:
            f.write(b)
