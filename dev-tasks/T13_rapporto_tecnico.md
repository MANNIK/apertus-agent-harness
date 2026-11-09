# T13 — Bozza del rapporto tecnico (inglese)
Stato: fatto (bozza del vecchio progetto) · Priorità: —

> **Storico (progetto precedente).** La bozza (`docs/technical_report.md`) descrive la suite agentica: **va riscritta in W12**. Restano riusabili la struttura, la tabella dei modelli generata dal comando (`--lang en`) e i test che la tengono sincronizzata.

## Obiettivo
Preparare `docs/technical_report.md` in **inglese** con la struttura finale, in modo che all'hackathon basti inserire i risultati veri.

## Contenuti obbligatori (regole)
- **Core task (regola 1)**: una frase che dice che Apertus (originale o modificato) svolge il compito centrale: agire come agente (tool use, recupero dagli errori, resistenza alle iniezioni) nei 33+ compiti.
- **Elenco di tutti i modelli (regola 6)**: genera la tabella con `agentbench manifest --models models.yaml` (modello, versione, licenza, ruolo, fase). Claude Sonnet 5.5 compare come strumento di sviluppo; qualsiasi giudice come open-weights con fase `evaluation`.
- **Architettura di deployment (regola 5)**: una tra on-premise / air-gapped / sovereign Swiss cloud. Non scegliere tu: lascia il campo da decidere con Nikola, ma spiega cosa è già vero (nessuna rete a runtime oltre l'endpoint del modello; Docker senza modelli).
- **Riproducibilità**: comandi (`make setup`, `make demo`, `make run`, replay), versioni bloccate, `calls.jsonl` e sha256.
- **Metodo e statistica**: dal piano di analisi (Wilson, McNemar, controlli, limiti).
- **Risultati**: lascia segnaposto `TBD (run: …)`; **non inventare numeri**. Inserisci solo ciò che esiste in `runs/` e cita la cartella.
- **Limiti** onesti (campione piccolo, tool finti, parser di riserva, conversione di terzi).

## Criteri di accettazione
- File completo di struttura, con sezioni e segnaposto chiari; tabella dei modelli generata dal comando, non scritta a mano.

## Esito
**Fatto:** `docs/technical_report.md` (inglese) con 8 sezioni: core task (regola 1), modelli (regola 6), architettura (regola 5), riproducibilità, metodo e statistica, risultati, limiti, come riprodurre. Tutti i risultati sono `TBD (run: …)`.
- La tabella dei modelli è **generata** dal comando `agentbench manifest --models models.yaml --lang en` (nuova opzione `--lang`) e incollata tra i marcatori `MODELS:BEGIN/END`; il test `tests/test_technical_report.py` fallisce se la tabella nel documento non coincide con l'output del comando. Per questo ho tradotto in inglese i campi testuali di `models.yaml` (nome, licenza, ruolo).
- Un secondo test verifica che le sezioni obbligatorie esistano e che ogni riga di risultato sia un segnaposto `TBD (run:` (niente numeri inventati).

**Architettura (regola 5): lasciata "TBD".** Il documento dice cosa è già vero (nessuna libreria di rete oltre a `httpx` nel client, verificato dal controllo AST; tool finti in memoria; punteggio senza LLM; Docker senza modelli provato in T07 → nel documento resta TBD finché non lo aggiorni) e cosa no.

**Verificato:** `pytest` passa (inclusi i 2 test sul rapporto). **Da fare quando ci sono i dati:** sostituire i segnaposto con numeri letti dalle cartelle di run.
**Non verificato:** le licenze segnate "to be verified" (8B del gateway, 70B, conversione MLX).
La sezione 3 e 4 sono state aggiornate con l'esito di T07 (immagine costruita, demo senza rete 62/62, versioni non bloccate).
