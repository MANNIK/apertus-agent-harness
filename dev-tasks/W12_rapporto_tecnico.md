# W12 — Rapporto tecnico (inglese) sul progetto WSP / Text-to-SQL
Stato: **bozza riscritta, risultati TBD** · Priorità: alta · Serve: —

## Obiettivo
Riscrivere `docs/technical_report.md` per il nuovo progetto, con struttura finale e risultati come segnaposto fino alle run vere.

## Contesto
La bozza attuale è della vecchia suite. Restano riusabili la struttura e i test che sincronizzano la tabella dei modelli con `agentbench manifest --models models.yaml --lang en`.

## Passi
1. Sezioni: core task (regola 1), modelli (regola 6, tabella generata), architettura (regola 5, solo se decisa), metodo WSP e LoRA, protocollo dev/val/test, risultati, costi, limiti, riproducibilità.
2. Ogni risultato è `TBD (run: …)` finché non esiste una run salvata; poi solo numeri letti dalla cartella citata.
3. Dichiara che WSP è un'ipotesi e riporta intervalli e test; spiega la correzione per confronti multipli.
4. Aggiorna i test del rapporto (`tests/test_technical_report.py`).

## Criteri di accettazione
- File completo, sezioni e segnaposto chiari; tabella dei modelli generata dal comando.

## Da non fare
- Nessun numero inventato; nessuna conclusione senza intervalli.

## Esito
Stato: **bozza riscritta per il nuovo progetto (10 nov 2026); tutti i risultati sono segnaposto `TBD (run: …)`.**
- `docs/technical_report.md` (inglese): compito centrale, tre condizioni, modelli (tabella generata da `agentbench manifest`, verificata da test), architettura (TBD), riproducibilità, metodo e statistica, tabella dei risultati vuota, limiti onesti (domande non riviste da madrelingua, 70 modelli di domanda, test piccolo, contaminazione non esclusa, velocità, WSP ipotesi).
- `tests/test_technical_report.py`: ogni riga dei risultati deve citare una run (`(run: …)`): un numero senza run salvata non passa.
- **Da fare:** sostituire i segnaposto con numeri letti da run salvate (con sha256 di `meta.json`), dichiarare l'architettura, descrivere WSP e LoRA quando esistono, rivedere la tabella dei modelli (checkpoint modificati).

