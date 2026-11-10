# W01 — Riorientare il repository sul progetto WSP / Text-to-SQL
Stato: fatto (rinomina in attesa di Nikola) · Priorità: alta (primo) · Serve: —

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
Stato: **fatto, tranne la rinomina della cartella** (10 nov 2026, ramo `riorientamento`, pubblicato su GitHub).

**Dipendenze trovate (passo 2).** `runner.py`, `bench.py`, `cli.py` e `checks.py` importano `tools.py`; `bench.py`/`cli.py` importano `tasks.py` e `checks.py`. Quindi questi tre moduli **non sono
spostabili senza rompere il nucleo**: restano in `src/agentbench/` e li sostituisce W03 (il compito non chiedeva di spostarli). Cinque test del nucleo (`e2e`, `replay`, `judge`, `compliance`,
`thinking_flag`) usavano i task YAML come dati di prova.

**Fatto**
- Ramo `riorientamento`. Spostati con `git mv` in `archive/agent-suite/`: `tasks/`, `reference_runs/` (con `demo-oracle`), `prompts/`, `rubrics/`, `scripts/build_demo.py` e i test `test_tasks_solvable`,
  `test_demo`, `test_t03_suite_defects`, `test_t09_suite_extension`. Aggiunto `archive/agent-suite/LEGGIMI.md`. Git le vede come 27 rinomine.
- I cinque test del nucleo ora leggono `archive/agent-suite/tasks/` e `.../rubrics/` come dati di prova (sed sui percorsi).
- `Makefile`: `make demo` termina con un messaggio chiaro; `make run` accetta `TASKS=`. `Dockerfile`: tolti i `COPY` dei file archiviati; il comando predefinito è ora `agentbench compliance --models models.yaml`.
  `.github/workflows/eval.yml`: il passo "Esegui la suite" fallisce di proposito con un messaggio. Aggiornati README, `CLAUDE.md` (radice e progetto), `tests/CLAUDE.md`, `scripts/CLAUDE.md`.

**Verificato (comandi eseguiti)**
- `.venv/bin/python -m pytest -q`: **101 passati** (129 prima; la differenza sono i 28 test spostati con la suite: calcolo, non ricontato per file).
- `make compliance`: 0 errori, 1 avviso (`deployment.target` vuoto: attende la scelta di Nikola, W11).
- `make demo`: esce con codice 1 e il messaggio previsto. `agentbench list-tasks` senza `--tasks` dà "errore: … 'tasks'"; con `--tasks archive/agent-suite/tasks` elenca 62 task.
- Nessun riferimento attivo a `tasks/`, `demo-oracle`, `rubrics/`, `prompts/` fuori dall'archivio (grep sui documenti e sui file di build).

**Non verificato / aperto**
- **Docker non è attivo su questo Mac**: né il `Dockerfile` modificato né `make airgap-check` sono stati provati. Da rifare quando Docker è disponibile.
- La workflow GitHub non è stata eseguita.
- `agentbench judge` ha ancora come predefinito `rubrics/agentic_v1.md` (percorso vecchio): serve `--rubric archive/agent-suite/rubrics/agentic_v1.md`. Il giudice è comunque "solo se serve" (T08 obsoleto).
- **Commit fatti e pubblicati** (Nikola ha autorizzato): commit `36d271b` (W01) e `379701e` (aggiornamenti W02–W11) sul ramo `riorientamento`, push su `origin`. `git show -M --summary HEAD~1` mostra 27 rinomine: criterio soddisfatto.
  Il ramo **non è stato unito a `main`** (decisione di Nikola).
- Rinomina della cartella `apertus-agent-harness`: **non fatta, serve l'ok di Nikola** (proposta: `apertus-weight-space-lab`; implica `CLAUDE.md`, remoto GitHub, percorsi `../models`).
- `docs/analysis_plan.md` (vecchio piano) era ancora al suo posto: l'ha spostato W04 in `docs/archive/`.
