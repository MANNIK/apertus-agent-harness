# apertus-agent-harness (provvisorio: ex banco di prova agentico, ora base di "Apertus Weight-Space Lab")

Contesto del progetto e regole del hackathon: `../CLAUDE.md` (leggilo). In breve: modificare i pesi di Apertus v1.5 8B (WSP) e confrontarli con
l'originale e con LoRA su **Text-to-SQL (DuckDB)**, con valutazione per esecuzione e statistica onesta.

## Stato del repo (leggi prima di toccare)
- **Nucleo riusabile oggi:** client OpenAI-compatibile, registrazione/replay, statistiche, report, conformità, parser delle tool call, CLI.
- **Vecchio progetto (suite agentica con tool finti, 62 task, `demo-oracle`, test collegati):** **archiviato con W01** in `archive/agent-suite/` (leggi il suo `LEGGIMI.md`).
  Non estenderlo e non citarlo come risultato del nuovo progetto. `make demo` non è più disponibile fino a W03. I moduli `tools.py`, `checks.py`, `tasks.py` restano nel pacchetto
  perché `runner`, `bench` e `cli` li importano: **W03 li sostituisce**. Alcuni test del nucleo leggono `archive/agent-suite/tasks/` solo come dati di prova.
- **Da costruire (serie W):** tool `run_sql` su DuckDB e controlli di execution accuracy; dataset Text-to-SQL con split dev/val/test; strumenti di
  ispezione dei pesi; ciclo WSP; baseline LoRA; valutazione a tre condizioni; applicazione dimostrativa.
Tutto ciò che è elencato come "da costruire" **non esiste ancora**: non descriverlo come funzionante.

## Principi non negoziabili
- **Punteggio ufficiale deterministico, per esecuzione.** Le query SQL si eseguono su DuckDB e si confrontano i risultati con la query gold. Nessun LLM nel
  calcolo del punteggio. Un giudice (`agentbench judge`) è solo uno strumento di taratura, open-weights e dichiarato.
- **Mai selezionare modifiche ai pesi guardando il test set.** Dev e val per iterare, test solo alla fine; split fissi, versionati con impronta.
  Ogni modifica ai pesi tentata va registrata (anche quelle scartate): altrimenti i risultati sono selezionati a posteriori.
- **Niente rete oltre il client.** `compliance.scan_network_imports` (AST) vieta `requests, urllib3, aiohttp, socket, smtplib, ftplib,
  http.client, urllib.request, websockets`; `httpx` è ammesso **solo** in `client.py`. Non aggirarlo. Gli strumenti pesanti (PyTorch,
  transformers, peft) vivono in un **ambiente/extra separato**, non nel pacchetto principale.
- **Riproducibilità.** Ogni run salva `results.jsonl`, `calls.jsonl`, `meta.json` con sha256; `agentbench run --replay RUN` rigioca i punteggi senza modello.
  Per i pesi: hash di ogni checkpoint, elenco dei tensori modificati, numero/% di parametri toccati, configurazione completa.
- **Ogni task deve essere risolvibile**: ogni task SQL ha la query gold eseguibile in un test.
- **Onestà dei risultati.** Intervalli di Wilson e McNemar sono già nel report. Con tre condizioni i confronti sono a coppie: dichiara la correzione per confronti
  multipli. Non scrivere "migliora" senza guardare gli intervalli, e non descrivere una differenza non significativa come "nessun effetto".
- **WSP è un'ipotesi.** Finché non ci sono run salvate, scrivi "da verificare", non "migliora Apertus".

## Mappa del codice (`src/agentbench/`)
| File | Ruolo | Stato nel nuovo progetto |
| --- | --- | --- |
| `cli.py` | Comandi: `smoke run report compare list-tasks compliance manifest judge` (`run` ha `--thinking`, `--ablate`) | riusato, da estendere |
| `client.py` | Unico punto che parla in rete (httpx); registra le chiamate (`record_to`) | riusato |
| `bench.py` / `runner.py` | Ciclo di una run / ciclo di un task (conversazione, tool, step massimi) | riusato; il tool `run_sql` si innesta qui |
| `parser.py` | Estrae le tool call (native, `<|tools_prefix|>`, ecc.) e toglie il ragionamento `<|inner_prefix|>…<|inner_suffix|>` | riusato |
| `recording.py` / `replay.py` | Registrazione e rigioco (chiavi indipendenti da nome modello e id casuali) | riusato |
| `report.py` / `stats.py` | Report Markdown, confronto, Wilson, McNemar, kappa | riusato; confronto a 3 condizioni da aggiungere |
| `compliance.py` | Registro modelli (`models.yaml`), controlli delle regole 3/4/5/6, manifest (`--lang en`) | riusato; checkpoint modificati da dichiarare |
| `judge.py` | Giudice open-weights opzionale e accordo con i controlli | riusato solo se serve |
| `tools.py` | Tool finti (meteo, calcolatrice, KB, file, email, ticket) | **vecchio progetto**, ancora importato da `runner`/`bench`/`cli`: sostituito da W03 |
| `checks.py` / `tasks.py` | Controlli sulle chiamate/testo/stato e caricamento dei task YAML | **vecchio progetto**: da adattare o sostituire con execution accuracy (W03) |

## Comandi (dalla cartella `apertus-agent-harness/`) — validi finché W01 non cambia il repo
```
scripts/bootstrap.sh              # una volta: uv, Python, dipendenze (tutto dentro .uv/ e .venv/)
.venv/bin/python -m pytest -q     # test (nessun modello): oggi 126+ passati
make help                         # elenco comandi; make demo è non disponibile fino a W03 (la vecchia demo è archiviata)
scripts/serve_mlx.sh              # server del modello locale (porta 8080), stampa le variabili da esportare
.venv/bin/agentbench smoke        # primo test contro il modello (LLM_BASE_URL, LLM_NAME, LLM_API_KEY, oppure APERTUS_*)
make run | make compare A=… B=… | make compliance | make manifest | make judge RUN=… | make docker-build docker-demo airgap-check
```
Il server MLX con il chat template di Apertus **ragiona per impostazione predefinita** (verificato il 10 nov 2026): per fissare la condizione usa
`--thinking on|off` (passa `chat_template_kwargs.enable_thinking`) e dichiaralo sempre nella run.

## Definition of done (per ogni modifica)
1. `.venv/bin/python -m pytest -q` passa. Scrivi o aggiorna i test insieme al codice.
2. `make compliance` non dà ERRORI (gli avvisi vanno spiegati).
3. Se cambi dati, split, formato dei file di una run o il prompt: aggiorna test e documenti; le vecchie run non sono più confrontabili — dillo nel messaggio finale.
4. Ogni modello o checkpoint nuovo è dichiarato in `models.yaml` (versione/hash, tecnica, ruolo, fase) prima di essere usato.
5. README e documenti allineati; segna chiaramente cosa è verificato e cosa no.

## Cosa NON fare
- Non modificare né cancellare `runs/` e `archive/agent-suite/reference_runs/` a mano (sono dati).
- Non citare `archive/agent-suite/reference_runs/demo-oracle` come risultato di Apertus: è un copione sintetico della vecchia suite.
- Non chiamare modelli chiusi dal codice della soluzione o dalle valutazioni; non aggiungere chiamate di rete fuori da `client.py`.
- Non usare il test set per decidere cosa modificare nei pesi.
- Non usare `--force`/azioni distruttive su git senza chiedere; non toccare `../models/`; non committare pesi, `.env` o token.
- Non fidarti di quello che "dovrebbe" fare `mlx_lm.server`: se non l'hai provato, scrivilo come non verificato.

## Compiti da svolgere
Cartella `dev-tasks/`: parti da `dev-tasks/README.md`. **Serie W = lavoro attivo** (W01 fatto il 10 nov 2026; ordine consigliato: W04 → W02 → W03 → W05); serie T = storico.
