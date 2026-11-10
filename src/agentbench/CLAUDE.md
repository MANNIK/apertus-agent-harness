# src/agentbench — regole per chi tocca il codice

- Python >= 3.10, dipendenze runtime del pacchetto principale solo `httpx` e `pyyaml`. Ogni nuova dipendenza: licenza permissiva + motivo scritto in `pyproject.toml`.
- **Rete solo in `client.py`.** Il controllo `compliance.scan_network_imports` fallisce altrimenti (vedi la lista dei moduli vietati lì).
- **Moduli del nuovo progetto (serie W):** fatti con W03: `sql_env.py` (`SqlBox`: DuckDB in sola lettura, tool `run_sql`, schema nel prompt, `make_box`, `SQL_SYSTEM`) e `sql_eval.py` (regole del confronto / execution accuracy, funzioni pure).
  Fatto (W06, parte indipendente dal metodo): `wsp.py` (extra `wsp`: numpy, ml_dtypes): impronte, ispezione, modifica **reversibile** con conteggio esatto dei parametri, registro JSONL, lettore/scrittore safetensors con bf16; testato solo su tensori sintetici. **Non è importato dal resto del pacchetto.**
  Da creare: l'addestramento LoRA e il ciclo WSP vero e proprio (dipendono dalla scelta del metodo).
  - DuckDB: extra opzionale `sql` (MIT, verificata sul pacchetto, vedi `docs/dati.md`); `import duckdb` solo dentro `SqlBox` (il pacchetto si importa anche senza). Database costruito da `setup.sql_init` e **riaperto in sola lettura**, accesso a file/rete disabilitato, una sola istruzione SELECT per chiamata, timeout con `interrupt`: non allentare queste protezioni.
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
- Il controllo `sql_result_match` (execution accuracy) sta in `checks.py`: l'ultima `run_sql` riuscita deve dare lo stesso risultato della query gold. `Task.meta` (lingua, schema, split, trappola) finisce in `results.jsonl` per le analisi a strati.
- **Legacy del vecchio progetto**, ancora nel pacchetto: i tool finti di `TOOL_DEFS`/`ToolBox` (meteo, calcolatrice, KB, file, email, ticket) e i controlli sulle chiamate/stato. Il nuovo progetto non li usa; gli ex task sono in `archive/agent-suite/` e alcuni test del nucleo li usano come dati di prova. Rimuoverli è una pulizia futura (da proporre a Nikola), non farla di nascosto.
