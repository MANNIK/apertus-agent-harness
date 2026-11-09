"""Estrazione delle tool call dalla risposta del modello.

Ordine di priorità:
1. `tool_calls` strutturato (il server ha già fatto il parsing) -> source "native".
2. Testo grezzo con i marcatori di Apertus `<|tools_prefix|>[...]<|tools_suffix|>`.
3. Altri formati comuni (`<tool_call>{...}</tool_call>`, blocchi ```json, JSON "nudo").

NOTA sul formato: su Apertus 1.5 8B (conversione MLX, `mlx_lm.server`) `agentbench smoke` ha mostrato
`<|tools_prefix|>[{"get_weather": {"city": "Lugano"}}]` SENZA il suffisso di chiusura (è il token di
stop, il server lo toglie) e senza `tool_calls` strutturati. Il parser gestisce sia questo caso sia
`{"name": ..., "arguments": ...}`. Il ragionamento del modello, racchiuso tra `<|inner_prefix|>` e
`<|inner_suffix|>`, viene tolto prima di tutto il resto (vedi `split_reasoning`).
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from .types import ToolCall

PREFIX_TAG = "<|tools_prefix|>"
SUFFIX_TAG = "<|tools_suffix|>"
INNER_PREFIX = "<|inner_prefix|>"
INNER_SUFFIX = "<|inner_suffix|>"
INNER_RE = re.compile(re.escape(INNER_PREFIX) + r"(.*?)" + re.escape(INNER_SUFFIX), re.S)
PREFIX_RE = re.compile(re.escape(PREFIX_TAG) + r"(.*?)" + re.escape(SUFFIX_TAG), re.S)
XML_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.S)
FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def _new_id() -> str:
    return "call_" + uuid.uuid4().hex[:8]


def _load_args(raw: Any) -> tuple[dict[str, Any], str | None]:
    """Argomenti come dict; accetta anche una stringa JSON (formato OpenAI)."""
    if isinstance(raw, dict):
        return raw, None
    if raw is None or raw == "":
        return {}, None
    if isinstance(raw, str):
        try:
            val = json.loads(raw)
        except json.JSONDecodeError as e:
            return {}, f"argomenti non sono JSON valido: {e.msg}"
        if isinstance(val, dict):
            return val, None
        return {}, "gli argomenti non sono un oggetto JSON"
    return {}, f"tipo di argomenti inatteso: {type(raw).__name__}"


def _normalize(obj: Any) -> list[tuple[str, Any]] | None:
    """Converte un oggetto JSON in [(nome, argomenti_grezzi)]; None se la forma è ignota."""
    items = obj if isinstance(obj, list) else [obj]
    out: list[tuple[str, Any]] = []
    for it in items:
        if not isinstance(it, dict) or not it:
            return None
        if isinstance(it.get("name"), str):
            out.append((it["name"], it.get("arguments", it.get("parameters", {}))))
        elif len(it) == 1:
            (key, val), = it.items()
            if not isinstance(val, dict):
                return None
            out.append((key, val))
        else:
            return None
    return out or None


def _calls_from_json(text: str, source: str) -> list[ToolCall]:
    """Interpreta un blocco di testo come JSON di tool call. Se è rotto, restituisce una
    chiamata "<unparseable>" con parse_error, così il fallimento resta visibile nei controlli
    invece di sparire come se fosse una normale risposta testuale."""
    text = text.strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        return [ToolCall(_new_id(), "<unparseable>", {}, source, text[:500], f"JSON non valido: {e.msg}")]
    norm = _normalize(obj)
    if norm is None:
        return [ToolCall(_new_id(), "<unparseable>", {}, source, text[:500], "struttura JSON non riconosciuta")]
    calls = []
    for name, raw_args in norm:
        args, err = _load_args(raw_args)
        calls.append(ToolCall(_new_id(), name, args, source, text[:500], err))
    return calls


def _content_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if content is None:
        return ""
    if isinstance(content, list):  # formato "content parts"
        return "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return str(content)


def split_reasoning(content: str) -> tuple[str, str]:
    """Separa il ragionamento del modello dal testo visibile: (visibile, ragionamento).

    I controlli devono guardare la risposta vera, non i pensieri: nel ragionamento compaiono numeri
    provvisori, frasi come "non posso" o i nomi di tool prima della decisione. Casi gestiti:
    - blocco completo `<|inner_prefix|>...<|inner_suffix|>`: tolto;
    - apertura senza chiusura (ragionamento troncato da max_tokens): tutto dopo l'apertura è
      ragionamento, il testo visibile può quindi risultare vuoto;
    - chiusura senza apertura (il template ha messo l'apertura nel prompt): tutto prima della
      chiusura è ragionamento.
    """
    reasoning: list[str] = []

    def grab(m: re.Match) -> str:
        reasoning.append(m.group(1))
        return ""

    text = INNER_RE.sub(grab, content)
    if INNER_PREFIX in text:
        text, tail = text.split(INNER_PREFIX, 1)
        reasoning.append(tail)
    if INNER_SUFFIX in text:
        head, text = text.split(INNER_SUFFIX, 1)
        reasoning.append(head)
    return text, "\n".join(reasoning)


def extract_tool_calls(message: dict[str, Any], known: set[str]) -> tuple[list[ToolCall], str]:
    """Restituisce (tool call, testo ripulito dai marcatori). `known` sono i nomi dei tool
    esposti al modello: serve solo per riconoscere JSON "nudo" senza scambiarlo per una risposta."""
    content, _reasoning = split_reasoning(_content_text(message))

    native = message.get("tool_calls")
    if native:
        calls = []
        for tc in native:
            fn = tc.get("function", {}) if isinstance(tc, dict) else {}
            args, err = _load_args(fn.get("arguments"))
            calls.append(
                ToolCall(
                    id=(tc.get("id") if isinstance(tc, dict) else None) or _new_id(),
                    name=fn.get("name", ""),
                    arguments=args,
                    source="native",
                    raw=json.dumps(tc, ensure_ascii=False)[:500],
                    parse_error=err,
                )
            )
        return calls, content.strip()

    calls: list[ToolCall] = []
    text = content
    for rx, src in ((PREFIX_RE, "prefix_tag"), (XML_RE, "xml_tag")):
        for m in rx.finditer(text):
            calls += _calls_from_json(m.group(1), src)
        text = rx.sub("", text)
    if calls:
        return calls, text.strip()

    # Marcatore di apertura senza chiusura: spesso il suffisso è il token di stop e il server lo toglie.
    if PREFIX_TAG in content:
        before, payload = content.split(PREFIX_TAG, 1)
        payload = payload.replace(SUFFIX_TAG, "")
        return _calls_from_json(payload, "prefix_tag"), before.strip()

    # JSON nudo: solo se tutti i nomi sono tool davvero esposti (altrimenti è una normale risposta).
    stripped = content.strip()
    candidates = [(stripped, "bare_json")] + [(m.group(1).strip(), "json_text") for m in FENCE_RE.finditer(content)]
    for cand, src in candidates:
        if not cand.startswith(("[", "{")):
            continue
        try:
            norm = _normalize(json.loads(cand))
        except json.JSONDecodeError:
            continue
        if norm and all(name in known for name, _ in norm):
            out = []
            for name, raw_args in norm:
                args, err = _load_args(raw_args)
                out.append(ToolCall(_new_id(), name, args, src, cand[:500], err))
            remaining = "" if src == "bare_json" else FENCE_RE.sub("", content).strip()
            return out, remaining

    return [], stripped
