# tests

- Si eseguono senza modello e senza rete: `.venv/bin/python -m pytest -q` (oggi 126+ test).
- `mock_server.py` simula un server OpenAI-compatibile: `MockServer(policy)`, `scripted({prompt: [messaggi]})`, `native(...)` (tool call strutturata), `native_many(...)` (più chiamate nello stesso turno), `prefix(...)` (testo con `<|tools_prefix|>`), `final(testo)`.
- Ogni bug trovato in una run reale diventa un test con un caso minimo che lo riproduce.
- I test non devono mai richiedere Internet, un modello vero, GPU o token (Hugging Face compreso).

## Test del vecchio progetto (W01 fatto il 10 nov 2026)
`test_tasks_solvable.py`, `test_demo.py`, `test_t03_suite_defects.py`, `test_t09_suite_extension.py` sono in `archive/agent-suite/tests/` (non eseguibili così come sono; pytest raccoglie solo `tests/`).
`test_e2e`, `test_replay`, `test_judge`, `test_compliance`, `test_thinking_flag` restano perché provano il nucleo, ma **leggono `archive/agent-suite/tasks/` come dati di prova**; `test_tools_checks.py`
prova `tools.py`/`checks.py`, ancora nel pacchetto. W03 sostituirà questi dati e moduli: quando lo fai, riadatta i test, non toglierli. Non aggiungere test alla vecchia suite.

## Test del nuovo progetto (W03, 10 nov 2026)
`test_sql_eval.py` (regole di confronto, senza DuckDB), `test_sql_env.py` (sola lettura, file/rete bloccati, timeout, limiti, schema), `test_sql_tasks.py` (ogni task risolvibile col gold, varianti sbagliate che falliscono, testo della query irrilevante, ciclo completo contro il server finto),
`test_app.py` (app dimostrativa contro un modello finto: schemi, domanda→query→tabella, input non validi, solo localhost, esempi mai dal test), `test_demo_sql.py` (integrità e replay al 100% della demo sintetica), `test_zurich_tasks.py` (dataset reale: licenze CC0 e sha256 dei dati, impronte dei task, split disgiunti per schema, 210 gold risolvibili, rigenerazione identica, protezione del test con `--final-test`). Richiedono l'extra `sql` (si saltano con `importorskip` se manca DuckDB).

## Regole per il nuovo progetto (da W03 in poi)
- **Text-to-SQL:** DuckDB **in memoria** con dati sintetici piccoli; ogni task ha la query gold in un test di risolvibilità (analogo a `test_tasks_solvable.py`).
  Test dedicati: una query sbagliata deve far fallire il controllo (colonne in più, righe duplicate, ordine, NULL, tipi); l'execution accuracy non deve dipendere dal testo della query.
- **Split:** un test verifica che dev, val e test non condividano id né schemi (generalizzazione) e che l'impronta salvata coincida.
- **Pesi:** gli strumenti di ispezione/modifica si testano su **tensori piccoli sintetici**, mai sui pesi veri: una modifica deve essere reversibile (applica Δθ e −Δθ → tensore identico), l'hash del checkpoint deve cambiare quando cambia un tensore, e il conteggio dei parametri modificati deve essere esatto.
- **Conformità:** un checkpoint modificato non dichiarato in `models.yaml` deve dare ERRORE; un modello chiuso a runtime/valutazione deve dare ERRORE (già coperto).
