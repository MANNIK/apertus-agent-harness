"""Strumenti sui pesi (wsp.py): solo tensori SINTETICI piccoli, mai pesi veri. Modifica reversibile, conteggio esatto, impronte, registro, safetensors."""
import json

import ml_dtypes
import numpy as np
import pytest

from agentbench import wsp

DTYPES = [np.float32, np.float16, ml_dtypes.bfloat16]


def make(dtype, seed=0, shape=(16, 24)):
    rng = np.random.default_rng(seed)
    return {"a": rng.standard_normal(shape).astype(dtype), "b": rng.standard_normal((8,)).astype(dtype), "c": rng.standard_normal((4, 4)).astype(dtype)}


def sparse_delta(shape, n, value, seed=1):
    rng = np.random.default_rng(seed)
    d = np.zeros(int(np.prod(shape)), dtype=np.float32)
    d[rng.choice(d.size, n, replace=False)] = value
    return d.reshape(shape)


def test_hash_changes_with_one_element_shape_and_dtype():
    a = np.arange(12, dtype=np.float32).reshape(3, 4)
    h = wsp.tensor_hash(a)
    b = a.copy(); b[2, 3] += 1
    assert wsp.tensor_hash(b) != h and wsp.tensor_hash(a.reshape(4, 3)) != h and wsp.tensor_hash(a.astype(np.float16)) != h
    assert wsp.tensor_hash(a.copy()) == h


def test_checkpoint_hash_does_not_depend_on_dict_order():
    w = make(np.float32)
    assert wsp.checkpoint_hash(w) == wsp.checkpoint_hash(dict(reversed(list(w.items()))))
    w2 = {k: v.copy() for k, v in w.items()}; w2["b"][0] += 1
    assert wsp.checkpoint_hash(w2) != wsp.checkpoint_hash(w)


@pytest.mark.parametrize("dtype", DTYPES)
def test_apply_then_revert_restores_bit_for_bit_and_hashes_match(dtype):
    w = make(dtype)
    orig = {k: v.copy() for k, v in w.items()}
    h0 = wsp.checkpoint_hash(w)
    patch = wsp.apply_delta(w, {"a": sparse_delta(w["a"].shape, 7, 0.5), "c": sparse_delta(w["c"].shape, 3, -0.25, seed=2)}, note="prova")
    assert wsp.checkpoint_hash(w) != h0 and np.array_equal(w["b"], orig["b"])  # b non toccato
    wsp.revert(w, patch)
    assert wsp.checkpoint_hash(w) == h0
    for k in w:
        assert w[k].tobytes() == orig[k].tobytes()
    for t in patch.record["tensors"]:
        assert wsp.tensor_hash(w[t["name"]]) == t["hash_before"] != t["hash_after"]


def test_modified_parameters_are_counted_after_rounding_not_by_nonzero_delta():
    w = {"x": np.ones((10, 10), dtype=ml_dtypes.bfloat16)}
    tiny = np.full((10, 10), 1e-6, dtype=np.float32)  # in bf16 vicino a 1.0 viene inghiottito dall'arrotondamento
    p = wsp.apply_delta(w, {"x": tiny})
    t = p.record["tensors"][0]
    assert t["n_delta_nonzero"] == 100 and t["n_changed"] == 0 and p.record["n_params_modified"] == 0 and t["hash_before"] == t["hash_after"]


def test_exact_counts_percentages_and_totals():
    w = make(np.float32)
    total = sum(v.size for v in w.values())
    p = wsp.apply_delta(w, {"a": sparse_delta(w["a"].shape, 5, 1.0), "c": sparse_delta(w["c"].shape, 2, 1.0, seed=3)})
    r = p.record
    assert r["n_params_modified"] == 7 and r["total_params"] == total and r["tensors_touched"] == 2
    assert abs(r["pct_params_modified"] - 100 * 7 / total) < 1e-9
    by = {t["name"]: t for t in r["tensors"]}
    assert by["a"]["n_changed"] == 5 and abs(by["a"]["pct_of_tensor"] - 100 * 5 / (16 * 24)) < 1e-9 and abs(by["a"]["delta_norm"] - 5 ** 0.5) < 1e-6


def test_naive_add_then_subtract_is_not_exact_in_low_precision_but_revert_is():
    rng = np.random.default_rng(5)
    a = rng.standard_normal(2000).astype(ml_dtypes.bfloat16)
    d = rng.standard_normal(2000).astype(np.float32) * 0.3
    naive = ((a.astype(np.float32) + d).astype(ml_dtypes.bfloat16).astype(np.float32) - d).astype(ml_dtypes.bfloat16)
    assert naive.tobytes() != a.tobytes()  # perché `revert` conserva i valori originali invece di sottrarre Δ
    w = {"a": a.copy()}
    wsp.revert(w, wsp.apply_delta(w, {"a": d}))
    assert w["a"].tobytes() == a.tobytes()


def test_invalid_deltas_are_rejected():
    w = make(np.float32)
    with pytest.raises(KeyError):
        wsp.apply_delta(w, {"nope": np.zeros(3, dtype=np.float32)})
    with pytest.raises(ValueError, match="forma"):
        wsp.apply_delta(w, {"b": np.zeros(9, dtype=np.float32)})
    with pytest.raises(ValueError, match="virgola mobile"):
        wsp.apply_delta({"i": np.zeros(4, dtype=np.int32)}, {"i": np.zeros(4, dtype=np.float32)})
    with pytest.raises(ValueError, match="contiguo"):
        wsp.apply_delta({"t": np.zeros((4, 4), dtype=np.float32).T[:, :2]}, {"t": np.zeros((2, 4), dtype=np.float32).T[:, :2]})


def test_registry_is_append_only_jsonl_and_keeps_rejected_attempts(tmp_path):
    w = make(np.float32)
    reg = tmp_path / "wsp_log.jsonl"
    p1 = wsp.apply_delta(w, {"a": sparse_delta(w["a"].shape, 4, 1.0)}, note="ipotesi 1: layer 3")
    wsp.append_registry(reg, p1.record, accepted=False, scores={"val_ex": 0.41})
    wsp.revert(w, p1)
    p2 = wsp.apply_delta(w, {"b": sparse_delta(w["b"].shape, 2, 1.0)}, note="ipotesi 2")
    wsp.append_registry(reg, p2.record, accepted=True)
    rows = [json.loads(l) for l in reg.read_text(encoding="utf-8").splitlines()]
    assert [r["accepted"] for r in rows] == [False, True] and rows[0]["scores"] == {"val_ex": 0.41} and rows[0]["note"].startswith("ipotesi 1")
    assert rows[0]["id"] != rows[1]["id"] and rows[0]["n_params_modified"] == 4


def test_inspect_tensor_stable_rank_and_spectral_norm():
    u, v = np.random.default_rng(1).standard_normal((20, 1)), np.random.default_rng(2).standard_normal((1, 30))
    r1 = wsp.inspect_tensor((u @ v).astype(np.float32))
    assert abs(r1["stable_rank"] - 1.0) < 1e-2 and r1["n_params"] == 600 and r1["shape"] == [20, 30]
    eye = wsp.inspect_tensor(np.eye(16, dtype=np.float32))
    assert abs(eye["stable_rank"] - 16.0) < 0.5 and abs(eye["norm_spectral"] - 1.0) < 1e-3
    m = np.random.default_rng(3).standard_normal((40, 30)).astype(np.float32)
    assert abs(wsp.spectral_norm(m, iters=200) - np.linalg.norm(m, 2)) < 1e-2
    assert "stable_rank" not in wsp.inspect_tensor(np.zeros(5, dtype=np.float32))
    assert set(wsp.summarize(make(np.float32), ["a", "c"])) == {"a", "c"}


@pytest.mark.parametrize("dtype", DTYPES)
def test_safetensors_roundtrip_with_partial_loading(tmp_path, dtype):
    w = make(dtype)
    f = tmp_path / "m.safetensors"
    wsp.save_tensors(f, w, metadata={"format": "np"})
    assert wsp.list_tensors(f)["a"] == {"dtype": {np.float32: "F32", np.float16: "F16", ml_dtypes.bfloat16: "BF16"}[dtype], "shape": [16, 24]}
    full, part = wsp.load_tensors(f), wsp.load_tensors(f, ["b"])
    assert set(part) == {"b"} and all(full[k].tobytes() == w[k].tobytes() and full[k].dtype == w[k].dtype for k in w)


def test_our_safetensors_files_are_readable_by_the_official_library_and_vice_versa(tmp_path):
    st = pytest.importorskip("safetensors.numpy")
    w = make(np.float32)
    f1 = tmp_path / "ours.safetensors"
    wsp.save_tensors(f1, w)
    off = st.load_file(str(f1))
    assert all(np.array_equal(off[k], w[k]) for k in w)
    f2 = tmp_path / "official.safetensors"
    st.save_file(w, str(f2))
    ours = wsp.load_tensors(f2)
    assert all(np.array_equal(ours[k], w[k]) for k in w)
