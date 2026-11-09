# W01 — Riorientare il repository sul progetto WSP / Text-to-SQL
Stato: pronto · Priorità: alta (primo) · Serve: —

## Obiettivo
Togliere dal percorso principale la suite agentica del vecchio progetto e lasciare un nucleo pulito su cui costruire il Text-to-SQL, senza perdere la storia né i test del nucleo riusabile.

## Contesto
Decisione di Nikola (10 nov 2026): la suite agentica (62 task, tool finti) viene **tolta**, non resta come controllo di regressione. Oggi `tasks/`, `reference_runs/demo-oracle`, `tools.py`, `checks.py` e molti test dipendono da essa. Il nucleo riusabile: `client`, `recording/replay`, `stats`, `report`, `compliance`, `parser`, `cli`.

## Passi
1. Ramo git dedicato (`git switch -c riorientamento`). Niente `--force`.
2. Elenca cosa dipende dalla suite (`grep`/import) e cosa è nucleo; scrivilo nell'Esito prima di spostare.
3. Sposta in `archive/agent-suite/` (con `git mv`) `tasks/*.yaml`, `reference_runs/demo-oracle`, `scripts/build_demo.py`, `prompts/`, `rubrics/` se legati alla suite, e i test che la riguardano (`test_tasks_solvable`, `test_demo`, `test_t03_*`, `test_t09_*`). Aggiungi in `archive/` un `LEGGIMI.md`: cosa è, perché archiviato, che i suoi risultati non sono confrontabili.
4. Adatta `Makefile`, `README.md`, `.github/workflows/eval.yml`, `Dockerfile`/`.dockerignore` e `tests/CLAUDE.md` per non riferirsi più alla suite come obiettivo; `make demo` deve avere un nuovo significato (o sparire) finché non c'è la demo Text-to-SQL (W03).
5. Mantieni nel nucleo i test dei moduli riusati (parser, recording/replay, stats, report, compliance, thinking flag) e fai passare `pytest` e `make compliance`.
6. Proponi a Nikola se rinominare la cartella (es. `apertus-weight-space-lab`); **non rinominare senza il suo ok**. Se rinomini, aggiorna i `CLAUDE.md`, il remoto GitHub e i percorsi `../models`.

## Criteri di accettazione
- `.venv/bin/python -m pytest -q` verde; `make compliance` senza errori.
- Nessun riferimento a `tasks/` o a `demo-oracle` come obiettivo nei documenti attivi.
- `git log` mostra gli spostamenti come rinomine (storia conservata).

## Da non fare
- Non cancellare nulla: si sposta. Non toccare `runs/` né `../models/`.
- Non rinominare la cartella né fare push senza chiedere.

## Esito
(da compilare)
