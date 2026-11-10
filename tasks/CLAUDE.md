# tasks — task Text-to-SQL

- `demo_sales.yaml`: 8 task **sintetici** (schema e dati inventati) per test e demo; **non** è il dataset di valutazione. Gli altri file di questa cartella sono sottocartelle: `agentbench run --tasks tasks` carica solo i `*.yaml` di primo livello (la demo).
- **`zurich/{dev,val,test}/`: dataset reale `zurich-sql` v0.1** (210 task su dati CC0 della Città di Zurigo, vedi `docs/dati.md` §7). **File generati**: non modificarli a mano; cambia `scripts/zurich_spec.py` e rigenera con `scripts/build_zurich_tasks.py` (`tests/test_zurich_tasks.py` verifica che coincidano).
  Uso: `agentbench run --tasks tasks/zurich/dev`. Il **test** richiede `--final-test` e si usa **una sola volta** a configurazione congelata.
- La vecchia suite agentica è in `archive/agent-suite/tasks/` (non estenderla).

## Formato di un task SQL (YAML, lista di task)
```yaml
- id: ...                      # unico
  category: aggregation        # aggregation | join | format_trap | null_trap | cross_lingual | ... (i report raggruppano per categoria)
  prompt: "<la domanda>"       # solo la domanda: lo schema lo aggiunge l'harness
  tools: [run_sql]
  setup:
    sql_init: ["CREATE TABLE ...", "INSERT INTO ..."]   # costruisce il DB (una connessione normale), poi il DB è riaperto in sola lettura; {DATA} = cartella dei dati (env AGENTBENCH_DATA_DIR o <radice>/data)
    limits: {timeout_s: 10, max_rows_shown: 50, ...}    # opzionale; vedi DEFAULT_LIMITS in src/agentbench/sql_env.py
  meta: {language: fr, schema_id: ..., split: dev|val|test|demo, trap: ...}   # etichette per le analisi a strati
  checks:
    - {type: sql_result_match, gold: "SELECT ...", order_matters: false}        # execution accuracy
    - {type: final_number, value: 275}                                           # opzionale: risposta finale (numeri)
```
Con le ancore YAML (`&db` / `*db`) più task condividono lo stesso `setup`.

## Regole per chi scrive task
- **Ogni task ha la query gold eseguibile**: `tests/test_sql_tasks.py` verifica che il gold passi il proprio controllo, che le varianti sbagliate (colonna in più, nessuna riga, righe duplicate) falliscano e che il testo della query non conti.
- `order_matters: true` **solo** se la domanda chiede un ordinamento, e il gold deve avere un ordinamento **totale** (nessun pareggio), altrimenti il risultato non è deterministico.
- Le regole di confronto stanno in `src/agentbench/sql_eval.py` e valgono per tutte le condizioni: non ammorbidirle per far salire i punteggi (modifiche solo in `docs/analysis_plan.md` → Deviations).
- Quale query conta: l'**ultima `run_sql` riuscita** della conversazione.
- Test set: mai usato per scegliere modifiche ai pesi. `meta.split` e gli schemi del test devono restare separati da dev/val (W02).
