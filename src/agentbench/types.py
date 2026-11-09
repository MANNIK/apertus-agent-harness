"""Strutture dati condivise: chiamate a tool, risultati, step e traiettoria.

Una *traiettoria* è l'intero svolgimento di un task: i messaggi scambiati, gli step del
modello (ognuno con le sue tool call e i risultati) e il testo finale. Tutti i controlli
di valutazione lavorano su questa struttura, mai direttamente sulla rete.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    # Da dove abbiamo estratto la chiamata:
    #   native     -> campo `tool_calls` strutturato restituito dal server
    #   prefix_tag -> testo tra <|tools_prefix|> e <|tools_suffix|> (formato nativo di Apertus)
    #   xml_tag    -> testo tra <tool_call> e </tool_call>
    #   json_text  -> JSON dentro un blocco ```json
    #   bare_json  -> tutto il contenuto è JSON (token speciali eliminati dal server)
    source: str
    raw: str = ""
    parse_error: str | None = None


@dataclass
class ToolResult:
    call_id: str
    name: str
    ok: bool
    content: str
    # unknown_tool: il modello ha inventato un tool; bad_args: argomenti non validi per lo schema;
    # tool_error: il tool ha risposto con un errore (anche iniettato volontariamente dal task).
    error_kind: str | None = None


@dataclass
class Step:
    index: int
    assistant_text: str
    tool_calls: list[ToolCall]
    tool_results: list[ToolResult]
    latency_s: float
    usage: dict[str, Any]
    finish_reason: str | None


@dataclass
class Trajectory:
    messages: list[dict[str, Any]] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    final_text: str = ""
    stopped: str = "final"  # final | max_steps | error
    error: str | None = None

    @property
    def calls(self) -> list[ToolCall]:
        return [c for s in self.steps for c in s.tool_calls]

    @property
    def pairs(self) -> list[tuple[ToolCall, ToolResult]]:
        """Coppie (chiamata, risultato) nell'ordine in cui sono avvenute."""
        out: list[tuple[ToolCall, ToolResult]] = []
        for s in self.steps:
            out.extend(zip(s.tool_calls, s.tool_results))
        return out

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
