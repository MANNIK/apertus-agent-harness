# apertus-agent-harness

Banco di prova per misurare il comportamento agentico di un modello servito via API OpenAI-compatibile (`/v1/chat/completions`).
Nato per Apertus v1.5 8B in locale (MLX). Contesto del hackathon e regole: vedi `../CLAUDE.md` (leggilo).

## Principi non negoziabili
- **Punteggio ufficiale deterministico.** Tool finti, controlli su chiamate/testo/stato finale. Nessun LLM nel calcolo del punteggio.
  Un giudice (`agentbench judge`) è solo uno strumento di taratura, con modello open-weights dichiarato.
- **Niente rete oltre il client.** `compliance.scan_network_imports` (AST) vieta `requests, urllib3, aiohttp, socket, smtplib, ftplib,
  http.client, urllib.request, websockets`; `httpx` è ammesso **solo** in `client.py`. Non aggirarlo.
- **Riproducibilità.** Ogni run salva `results.jsonl`, `calls.jsonl`, `meta.json` con sha256. `agentbench run --replay RUN` deve rigiocare gli stessi punteggi senza modello.
- **Ogni task deve essere risolvibile**: `tests/test_tasks_solvable.py` ha un percorso corretto per ciascuno (set di id identico a quello dei task).
- **Onestà dei risultati.** Intervalli di Wilson e McNemar sono già nel report: non scrivere "migliora" senza guardarli (con 33 task si vedono solo effetti grandi).

## Mappa del codice (`src/agentbench/`)
| File | Ruolo |
| --- | --- |
| `cli.py` | Comandi: `smoke run report compare list-tasks compliance manifest judge` |
| `client.py` | Unico punto che parla in rete (httpx); registra le chiamate (`record_to`) |
| `bench.py` / `runner.py` | Ciclo di una run / ciclo di un task (conversazione, tool, step massimi) |
| `parser.py` | Estrae le tool call (native, `<|tools_prefix|>`, ecc.) e toglie il ragionamento `<|inner_prefix|>…<|inner_suffix|>` |
| `tools.py` | Tool finti e `ToolBox` (meteo, calcolatrice, KB, file virtuali, email finta, ticket) |
| `checks.py` | Controlli dichiarativi usati dai task YAML (`@check("nome")`) |
| `tasks.py` | Caricamento e validazione dei task; `DEFAULT_SYSTEM` |
| `recording.py` / `replay.py` | Registrazione e rigioco (chiavi indipendenti da nome modello e id casuali) |
| `report.py` / `stats.py` | Report Markdown, confronto, Wilson, McNemar, kappa |
| `compliance.py` | Registro modelli (`models.yaml`), controlli delle regole 3/4/5/6, manifest |
| `judge.py` | Giudice open-weights opzionale e accordo con i controlli |

## Comandi (dalla cartella `apertus-agent-harness/`)
```
scripts/bootstrap.sh              # una volta: uv, Python, dipendenze (tutto dentro .uv/ e .venv/)
.venv/bin/python -m pytest -q     # test (nessun modello): oggi 98 passati
make help                         # elenco comandi; make demo = replay sintetico, deve dare 33/33
scripts/serve_mlx.sh              # server del modello locale (porta 8080), stampa le variabili da esportare
.venv/bin/agentbench smoke        # primo test contro il modello (LLM_BASE_URL, LLM_NAME, LLM_API_KEY, oppure APERTUS_*)
make run | make compare A=… B=… | make compliance | make manifest | make judge RUN=…
```

## Definition of done (per ogni modifica)
1. `.venv/bin/python -m pytest -q` passa. Scrivi o aggiorna i test insieme al codice.
2. `make compliance` non dà ERRORI (gli avvisi vanno spiegati).
3. Se cambi task, tool, prompt di default o formato dei file: aggiorna `SOLUTIONS` in `tests/test_tasks_solvable.py`, rigenera
   `reference_runs/demo-oracle` con `.venv/bin/python scripts/build_demo.py` e controlla che `make demo` dia il 100%.
   Nota: cambiare i task cambia il digest della suite, quindi le vecchie run non sono più confrontabili con le nuove.
4. README e documenti allineati; segna chiaramente cosa è verificato e cosa no.

## Cosa NON fare
- Non modificare né cancellare `runs/` e `reference_runs/` a mano (sono dati; `reference_runs/demo-oracle` si rigenera solo con lo script).
- Non citare `reference_runs/demo-oracle` come risultato di Apertus: è un copione sintetico.
- Non chiamare modelli chiusi, né aggiungere chiamate di rete fuori da `client.py`.
- Non usare `--force`/azioni distruttive su git senza chiedere; non toccare `../models/`.
- Non fidarti di quello che "dovrebbe" fare `mlx_lm.server`: se non l'hai provato, scrivilo come non verificato.

## Compiti da svolgere
Cartella `dev-tasks/`: parti da `dev-tasks/README.md`.
