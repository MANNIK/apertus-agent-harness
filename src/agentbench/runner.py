"""Il ciclo agentico: chiede al modello, esegue i tool richiesti, restituisce i risultati.

Si ferma quando il modello risponde senza chiamare tool (risposta finale), quando supera
`max_steps` o quando il server dà errore. Tutto ciò che avviene è registrato nella Trajectory.

`history_mode` decide come i tool entrano nella conversazione dei turni successivi:
  openai -> messaggio assistant con `tool_calls` + messaggi con role "tool" (standard OpenAI)
  text   -> assistant con il testo grezzo + risultati in un messaggio "user" ("[tool results]")
Se il chat template del server non gestisce il ruolo "tool", la modalità "text" è la via d'uscita.
"""
from __future__ import annotations

import json
from typing import Any

from .client import ChatClient, ChatError
from .parser import extract_tool_calls
from .tasks import DEFAULT_SYSTEM, Task
from .tools import ToolBox
from .types import Step, ToolCall, ToolResult, Trajectory


def _assistant_message(raw: dict[str, Any], calls: list[ToolCall], text: str, mode: str) -> dict[str, Any]:
    if mode == "text":
        content = raw.get("content") or ""
        if not isinstance(content, str) or not content.strip():
            content = "Calling tools: " + json.dumps(
                [{"name": c.name, "arguments": c.arguments} for c in calls], ensure_ascii=False
            )
        return {"role": "assistant", "content": content}
    return {
        "role": "assistant",
        "content": text,
        "tool_calls": [
            {"id": c.id, "type": "function",
             "function": {"name": c.name, "arguments": json.dumps(c.arguments, ensure_ascii=False)}}
            for c in calls
        ],
    }


def _tool_messages(results: list[ToolResult], mode: str) -> list[dict[str, Any]]:
    if mode == "text":
        body = "\n".join(f"{r.name}: {r.content}" for r in results)
        return [{"role": "user", "content": "[tool results]\n" + body}]
    return [{"role": "tool", "tool_call_id": r.call_id, "name": r.name, "content": r.content} for r in results]


def run_task(
    client: ChatClient,
    task: Task,
    box: ToolBox,
    history_mode: str = "openai",
    default_system: str = DEFAULT_SYSTEM,
) -> Trajectory:
    available = list(task.tools)
    specs = box.specs(available) if available else None
    system = task.system if task.system is not None else default_system
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task.prompt},
    ]
    traj = Trajectory(messages=messages)
    known = set(available)

    for i in range(task.max_steps):
        try:
            resp = client.chat(messages, tools=specs)
        except ChatError as e:
            traj.stopped, traj.error = "error", str(e)
            return traj
        raw = resp["message"]
        calls, text = extract_tool_calls(raw, known)
        step = Step(i, text, calls, [], resp["latency_s"], resp["usage"], resp["finish_reason"])
        traj.steps.append(step)

        if not calls:  # risposta finale
            traj.final_text = text
            messages.append({"role": "assistant", "content": text})
            traj.stopped = "final"
            return traj

        messages.append(_assistant_message(raw, calls, text, history_mode))
        step.tool_results = [box.execute(c, available) for c in calls]
        messages.extend(_tool_messages(step.tool_results, history_mode))

    traj.stopped = "max_steps"
    return traj
