# tests

- Si eseguono senza modello e senza rete: `.venv/bin/python -m pytest -q` (oggi 98 test).
- `mock_server.py` simula un server OpenAI-compatibile: `MockServer(policy)`, `scripted({prompt: [messaggi]})`, `native(...)` (tool call strutturata), `prefix(...)` (testo con `<|tools_prefix|>`), `final(testo)`.
- `test_tasks_solvable.py`: `SOLUTIONS` deve avere esattamente gli id dei task YAML. Aggiungendo o cambiando un task, aggiungi/aggiorna il percorso corretto.
- `test_demo.py` verifica `reference_runs/demo-oracle` (integrità sha256, replay 33/33 con il numero di task attuale, nessun errore di conformità). Se cambia il numero di task, rigenera la demo e aggiorna l'atteso.
- Ogni bug trovato in una run reale diventa un test con un caso minimo che lo riproduce.
- I test non devono mai richiedere Internet né un modello vero.
