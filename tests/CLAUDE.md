# tests

- Si eseguono senza modello e senza rete: `.venv/bin/python -m pytest -q` (oggi 126+ test).
- `mock_server.py` simula un server OpenAI-compatibile: `MockServer(policy)`, `scripted({prompt: [messaggi]})`, `native(...)` (tool call strutturata), `native_many(...)` (più chiamate nello stesso turno), `prefix(...)` (testo con `<|tools_prefix|>`), `final(testo)`.
- Ogni bug trovato in una run reale diventa un test con un caso minimo che lo riproduce.
- I test non devono mai richiedere Internet, un modello vero, GPU o token (Hugging Face compreso).

## Test del vecchio progetto (in archiviazione, W01)
`test_tasks_solvable.py` (`SOLUTIONS` = id dei task YAML), `test_demo.py` (demo-oracle, integrità sha256 e replay al 100%), `test_t03_suite_defects.py`, `test_t09_suite_extension.py`,
`test_thinking_flag.py` e quelli sulle tool finte vengono spostati o adattati con la suite. Non aggiungere test a quella suite.

## Regole per il nuovo progetto (da W03 in poi)
- **Text-to-SQL:** DuckDB **in memoria** con dati sintetici piccoli; ogni task ha la query gold in un test di risolvibilità (analogo a `test_tasks_solvable.py`).
  Test dedicati: una query sbagliata deve far fallire il controllo (colonne in più, righe duplicate, ordine, NULL, tipi); l'execution accuracy non deve dipendere dal testo della query.
- **Split:** un test verifica che dev, val e test non condividano id né schemi (generalizzazione) e che l'impronta salvata coincida.
- **Pesi:** gli strumenti di ispezione/modifica si testano su **tensori piccoli sintetici**, mai sui pesi veri: una modifica deve essere reversibile (applica Δθ e −Δθ → tensore identico), l'hash del checkpoint deve cambiare quando cambia un tensore, e il conteggio dei parametri modificati deve essere esatto.
- **Conformità:** un checkpoint modificato non dichiarato in `models.yaml` deve dare ERRORE; un modello chiuso a runtime/valutazione deve dare ERRORE (già coperto).
