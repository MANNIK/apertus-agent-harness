# src/agentbench — regole per chi tocca il codice

- Python >= 3.10, dipendenze runtime solo `httpx` e `pyyaml`. Ogni nuova dipendenza: licenza permissiva + motivo scritto in `pyproject.toml`.
- **Rete solo in `client.py`.** Il controllo `compliance.scan_network_imports` fallisce altrimenti (vedi la lista dei moduli vietati lì).
- Nuovo controllo per i task: funzione `fn(spec, ctx) -> (ok: bool, dettaglio: str)` con `@check("nome")` in `checks.py` (`ctx.traj.calls`, `ctx.box`), come gli altri; testalo in `tests/test_tools_checks.py`.
- Nuovo tool finto: definizione in `TOOL_DEFS` e logica in `ToolBox` (`tools.py`); deve essere deterministico e senza effetti fuori dalla memoria.
- Formati dei file di una run (`results.jsonl`, `calls.jsonl`, `meta.json`, `judge.jsonl`, `judge_meta.json`): se li cambi, aggiorna `report.py`, `replay.py`, `compliance.py`, i test e `reference_runs/demo-oracle`.
- `recording.request_key` ignora il nome del modello e normalizza gli id delle tool call: non cambiarlo senza rifare i test di replay (`tests/test_replay.py`).
- Messaggi all'utente e commenti in italiano; nomi di variabili e funzioni in inglese.
- Parser (`parser.py`): il formato di Apertus è `<|tools_prefix|>[{"nome": {args}}]` senza suffisso; `mlx_lm.server` non restituisce `tool_calls` strutturati, vLLM con `--tool-call-parser apertus` sì. Gestisci entrambi e aggiungi un test per ogni nuovo caso reale.
