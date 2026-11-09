"""Tool finti e deterministici + validazione degli argomenti.

I tool non toccano la rete né il disco: lavorano su stato in memoria (un filesystem virtuale,
una casella di posta in uscita, una knowledge base). Così ogni run è riproducibile e i
controlli possono ispezionare lo *stato finale* (es. "il file totale contiene 4500").

Un task può iniettare comportamenti nel ToolBox tramite `setup`:
  files:  {percorso: contenuto}          filesystem virtuale iniziale
  kb:     [{title, text, keywords}]      documenti extra nella knowledge base (es. avvelenati)
  faults: {tool: {fail_first: N, message: "..."}}   i primi N usi del tool falliscono
"""
from __future__ import annotations

import ast
import json
import operator as op
import re
import unicodedata
from collections import defaultdict
from typing import Any

from .types import ToolCall, ToolResult


class ToolError(Exception):
    """Errore "normale" di un tool: viene restituito al modello come risultato con ok=False."""


# --------------------------------------------------------------------------- dati fissi

WEATHER = {  # chiave normalizzata -> (nome, °C, condizione)
    "zurich": ("Zurich", 8, "cloudy"),
    "lugano": ("Lugano", 12, "sunny"),
    "geneva": ("Geneva", 9, "rain"),
    "bern": ("Bern", 6, "fog"),
    "parma": ("Parma", 14, "sunny"),
    "chur": ("Chur", 4, "snow"),
}
TO_CHF = {"CHF": 1.0, "EUR": 0.94, "USD": 0.88, "GBP": 1.12}

DEFAULT_KB = [
    {"title": "Refund policy",
     "text": "Customers can request a refund within 30 days of purchase. Refunds are processed within 5 business days.",
     "keywords": "rimborso rimborsi remboursement rückerstattung geld zurück"},
    {"title": "Support contact",
     "text": "Support contact: help@helvetia-labs.example. Support hours are Monday to Friday, 08:00-17:00 CET.",
     "keywords": "assistenza supporto contatto contact support kontakt hilfe email"},
    {"title": "API rate limit",
     "text": "The API rate limit is 100 requests per minute per key. Exceeding the limit returns HTTP 429.",
     "keywords": "limite richieste limite de requêtes anfragen limit quota"},
    {"title": "Q3 revenue",
     "text": "Q3 2026 revenue was CHF 4.2 million, up 12 percent from Q2.",
     "keywords": "ricavi fatturato chiffre d'affaires umsatz trimestre"},
    {"title": "Offices",
     "text": "Offices: Zurich (headquarters, 120 employees) and Lugano (engineering, 45 employees).",
     "keywords": "sedi uffici bureaux büros dipendenti employés mitarbeiter"},
]

# Definizioni nel formato `tools` di OpenAI: nome -> (descrizione, schema JSON dei parametri)
TOOL_DEFS: dict[str, tuple[str, dict[str, Any]]] = {
    "get_weather": (
        "Get the current weather for a city.",
        {"type": "object", "required": ["city"], "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Lugano'"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit (default celsius)"}}},
    ),
    "get_exchange_rate": (
        "Get the current exchange rate: how many units of `quote` one unit of `base` buys.",
        {"type": "object", "required": ["base", "quote"], "properties": {
            "base": {"type": "string", "description": "ISO currency code, e.g. EUR"},
            "quote": {"type": "string", "description": "ISO currency code, e.g. CHF"}}},
    ),
    "calculator": (
        "Evaluate an arithmetic expression (+, -, *, /, **, %, parentheses).",
        {"type": "object", "required": ["expression"], "properties": {
            "expression": {"type": "string", "description": "e.g. '(12 + 8) / 2'"}}},
    ),
    "search_kb": (
        "Search the company knowledge base. Returns the best matching entries.",
        {"type": "object", "required": ["query"], "properties": {
            "query": {"type": "string", "description": "Search keywords"}}},
    ),
    "list_files": (
        "List files in the workspace, optionally filtered by a path prefix.",
        {"type": "object", "required": [], "properties": {
            "prefix": {"type": "string", "description": "Only list paths starting with this prefix"}}},
    ),
    "read_file": (
        "Read a text file from the workspace.",
        {"type": "object", "required": ["path"], "properties": {
            "path": {"type": "string", "description": "File path, e.g. 'notes/todo.txt'"}}},
    ),
    "write_file": (
        "Write (create or overwrite) a text file in the workspace.",
        {"type": "object", "required": ["path", "content"], "properties": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Full file content"}}},
    ),
    "send_email": (
        "Send an email.",
        {"type": "object", "required": ["to", "subject", "body"], "properties": {
            "to": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string"},
            "body": {"type": "string"}}},
    ),
    "create_ticket": (
        "Create a support ticket.",
        {"type": "object", "required": ["title", "priority"], "properties": {
            "title": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]}}},
    ),
}


# --------------------------------------------------------------------------- utilità

_TYPES: dict[str, Any] = {
    "string": str, "integer": int, "number": (int, float),
    "boolean": bool, "array": list, "object": dict,
}


def validate_args(schema: dict[str, Any], args: dict[str, Any]) -> list[str]:
    """Validatore JSON-Schema minimale (required, type, enum): niente dipendenze esterne."""
    errs: list[str] = []
    props = schema.get("properties", {})
    for req in schema.get("required", []):
        if req not in args:
            errs.append(f"missing required argument '{req}'")
    for key, val in args.items():
        spec = props.get(key)
        if spec is None:
            errs.append(f"unexpected argument '{key}'")
            continue
        t = spec.get("type")
        if t:
            is_bool = isinstance(val, bool)
            if (is_bool and t != "boolean") or (not is_bool and not isinstance(val, _TYPES[t])):
                errs.append(f"argument '{key}' must be of type {t}, got {type(val).__name__}")
                continue
        if "enum" in spec and val not in spec["enum"]:
            errs.append(f"argument '{key}' must be one of {spec['enum']}, got {val!r}")
    return errs


def _norm(s: str) -> str:
    """'Zürich ' -> 'zurich' (minuscolo, senza accenti)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


_BIN = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod}
_UN = {ast.USub: op.neg, ast.UAdd: op.pos}


def safe_eval(expr: str) -> float:
    """Valuta un'espressione aritmetica via AST: solo numeri e operatori, nessun eval()."""
    def ev(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("exponent too large")
            return _BIN[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
            return _UN[type(node.op)](ev(node.operand))
        raise ValueError("unsupported expression")
    return ev(ast.parse(expr.strip(), mode="eval"))


def _fmt_number(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.10g}"


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", s.lower()) if len(w) >= 3}


# --------------------------------------------------------------------------- ToolBox

class ToolBox:
    def __init__(self, setup: dict[str, Any] | None = None) -> None:
        setup = setup or {}
        self.fs: dict[str, str] = dict(setup.get("files", {}))
        self.kb: list[dict[str, str]] = DEFAULT_KB + list(setup.get("kb", []))
        self.faults: dict[str, dict[str, Any]] = {k: dict(v) for k, v in setup.get("faults", {}).items()}
        self.outbox: list[dict[str, str]] = []
        self.tickets: list[dict[str, str]] = []
        self.counts: dict[str, int] = defaultdict(int)

    @staticmethod
    def specs(names: list[str]) -> list[dict[str, Any]]:
        """Definizioni dei tool nel formato `tools` di OpenAI."""
        return [
            {"type": "function", "function": {"name": n, "description": TOOL_DEFS[n][0], "parameters": TOOL_DEFS[n][1]}}
            for n in names
        ]

    def execute(self, call: ToolCall, available: list[str]) -> ToolResult:
        """Esegue una chiamata. Gli errori del modello (tool inventato, argomenti sbagliati)
        vengono restituiti come testo, esattamente come farebbe un'API reale: il modello deve
        accorgersene e correggersi, ed è proprio questo che vogliamo misurare."""
        def fail(kind: str, msg: str) -> ToolResult:
            return ToolResult(call.id, call.name, False, f"Error: {msg}", kind)

        if call.parse_error:
            return fail("bad_args", f"could not parse the tool call ({call.parse_error})")
        if call.name not in available:
            return fail("unknown_tool", f"unknown tool '{call.name}'. Available tools: {', '.join(available)}")
        errs = validate_args(TOOL_DEFS[call.name][1], call.arguments)
        if errs:
            return fail("bad_args", "invalid arguments: " + "; ".join(errs))

        self.counts[call.name] += 1
        fault = self.faults.get(call.name)
        if fault and self.counts[call.name] <= fault.get("fail_first", 0):
            return fail("tool_error", fault.get("message", "tool failure"))
        try:
            return ToolResult(call.id, call.name, True, getattr(self, "_t_" + call.name)(**call.arguments))
        except ToolError as e:
            return fail("tool_error", str(e))

    # ------------------------------------------------------------------ implementazioni

    def _t_get_weather(self, city: str, unit: str = "celsius") -> str:
        key = _norm(city)
        if key not in WEATHER:
            known = ", ".join(v[0] for v in WEATHER.values())
            raise ToolError(f"city not found: '{city}'. Known cities: {known}")
        name, celsius, cond = WEATHER[key]
        temp = celsius if unit == "celsius" else round(celsius * 9 / 5 + 32, 1)
        return json.dumps({"city": name, "temperature": temp, "unit": unit, "condition": cond})

    def _t_get_exchange_rate(self, base: str, quote: str) -> str:
        b, q = base.upper(), quote.upper()
        for cur in (b, q):
            if cur not in TO_CHF:
                raise ToolError(f"unsupported currency '{cur}'. Supported: {', '.join(TO_CHF)}")
        return json.dumps({"base": b, "quote": q, "rate": round(TO_CHF[b] / TO_CHF[q], 4)})

    def _t_calculator(self, expression: str) -> str:
        try:
            return _fmt_number(safe_eval(expression))
        except ZeroDivisionError:
            raise ToolError("division by zero")
        except (ValueError, SyntaxError, TypeError, OverflowError) as e:
            raise ToolError(f"cannot evaluate expression: {e}")

    def _t_search_kb(self, query: str) -> str:
        q = _words(query)
        scored = []
        for doc in self.kb:
            score = len(q & _words(doc["title"] + " " + doc["text"] + " " + doc.get("keywords", "")))
            if score:
                scored.append((score, doc))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            return "No results."
        return json.dumps([{"title": d["title"], "text": d["text"]} for _, d in scored[:2]], ensure_ascii=False)

    def _t_list_files(self, prefix: str = "") -> str:
        return json.dumps(sorted(p for p in self.fs if p.startswith(prefix)))

    def _t_read_file(self, path: str) -> str:
        if path not in self.fs:
            raise ToolError(f"file not found: '{path}'. Use list_files to see available files.")
        return self.fs[path]

    def _t_write_file(self, path: str, content: str) -> str:
        self.fs[path] = content
        return f"Wrote {len(content)} characters to {path}"

    def _t_send_email(self, to: str, subject: str, body: str) -> str:
        self.outbox.append({"to": to, "subject": subject, "body": body})
        return f"Email sent to {to}"

    def _t_create_ticket(self, title: str, priority: str) -> str:
        ticket = {"id": f"TCK-{1001 + len(self.tickets)}", "title": title, "priority": priority}
        self.tickets.append(ticket)
        return json.dumps(ticket)
