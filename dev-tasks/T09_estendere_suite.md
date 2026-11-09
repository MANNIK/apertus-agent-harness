# T09 — Estendere la suite
Stato: pronto · Priorità: media

## Obiettivo
33 compiti vedono solo effetti grandi (intervallo di Wilson ampio). Portare la suite verso ~60 compiti, coprendo ciò che manca, senza abbassare la qualità.

## Cosa aggiungere (proposta, discuti le priorità nell'Esito)
- **Lingue**: gli stessi scenari in italiano, tedesco, francese e inglese (contesto svizzero), per vedere se il comportamento cambia con la lingua.
- **Chiamate parallele**: richieste che richiedono più chiamate indipendenti nello stesso turno.
- **Catene più lunghe** (4–6 passi) e strumenti "di disturbo" non necessari.
- **Ambiguità**: richieste in cui il modello deve chiedere chiarimenti, contro richieste in cui deve agire.
- **Iniezioni** in posizioni diverse (file, risultato di ricerca, risultato di errore) e con diversi gradi di esplicitezza. Ricorda "non esercitato" (T03).
- **Argomenti difficili**: date, importi con separatori diversi, caratteri speciali.

## Regole
- Ogni task: deterministico, risolvibile (percorso in `tests/test_tasks_solvable.py`), controlli sullo stato dove possibile, nessun dato reale.
- Dichiara la nuova versione della suite (il digest cambia: le run vecchie non sono confrontabili). Aggiorna README (numero e gruppi), rigenera la demo (`scripts/build_demo.py`), aggiorna `tests/test_demo.py`.
- Non scegliere i task guardando cosa fa passare Apertus: scrivili prima e **non** ritoccare i controlli dopo aver visto gli esiti.

## Criteri di accettazione
- Test passano, `make demo` al 100%, elenco dei nuovi task con scopo di ciascuno.

## Esito
(da compilare)
