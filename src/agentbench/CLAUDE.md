# src/agentbench — regole per chi tocca il codice

- Python >= 3.10, dipendenze runtime del pacchetto principale solo `httpx` e `pyyaml`. Ogni nuova dipendenza: licenza permissiva + motivo scritto in `pyproject.toml`.
- **Rete solo in `client.py`.** Il controllo `compliance.scan_network_imports` fallisce altrimenti (vedi la lista dei moduli vietati lì).
- **Moduli del nuovo progetto (da creare, serie W):** `sql` (tool `run_sql` su DuckDB, confronto dei risultati / execution accuracy), `wsp` (ispezione e modifica dei pesi) e `lora`.
  - DuckDB: dipendenza **opzionale** (extra) con licenza da verificare; deterministica, solo memoria o file locali, mai rete.
  - PyTorch / transformers / peft: solo in un **extra o ambiente separato** (`external/` o simile), mai importati dal pacchetto principale; il controllo di rete deve restare verde.
  - Le modifiche ai pesi sono **reversibili** e producono sempre un registro: tensori toccati, Δθ (norma, rango), numero e % di parametri modificati, hash prima/dopo.
- Nuovo controllo per i task: funzione `fn(spec, ctx) -> (ok: bool, dettaglio: str)` con `@check("nome")` in `checks.py` (`ctx.traj.calls`, `ctx.box`), testata in `tests/test_tools_checks.py`. Il controllo di execution accuracy si aggiunge allo stesso modo.
- Nuovo tool: definizione in `TOOL_DEFS` e logica in `ToolBox` (`tools.py`); deve essere deterministico e senza effetti fuori dalla memoria.
- Formati dei file di una run (`results.jsonl`, `calls.jsonl`, `meta.json`, `judge.jsonl`, `judge_meta.json`): se li cambi, aggiorna `report.py`, `replay.py`, `compliance.py`, i test e le run di riferimento.
  `results.jsonl` ha `outcome` (`passed|failed|not_exercised`), `exercised` e controlli `diagnostic` che non contano nel punteggio; `meta.json` ha `ablations` e `extra_body` (qui finisce `--thinking`).
- `recording.request_key` ignora il nome del modello e normalizza gli id delle tool call: non cambiarlo senza rifare i test di replay (`tests/test_replay.py`).
- **Conformità dei checkpoint:** un checkpoint WSP/LoRA è un modello da dichiarare in `models.yaml` (base, tecnica, versione/hash, ruolo, fase) prima di comparire in una run; `compliance` deve dare errore se manca.
- Messaggi all'utente e commenti in italiano; nomi di variabili e funzioni in inglese.
- Parser (`parser.py`): il formato di Apertus è `<|tools_prefix|>[{"nome": {args}}]` senza suffisso; `mlx_lm.server` non restituisce `tool_calls` strutturati, vLLM con `--tool-call-parser apertus` sì. Gestisci entrambi e aggiungi un test per ogni nuovo caso reale.
  Il ragionamento `<|inner_prefix|>…<|inner_suffix|>` è attivo per impostazione predefinita nel server MLX locale: viene tolto prima della valutazione.
- Strumenti del vecchio progetto (`tools.py` finti, `checks.py` sulle chiamate, `tasks.py` YAML): in archiviazione (W01); riusa i meccanismi, non le definizioni.
