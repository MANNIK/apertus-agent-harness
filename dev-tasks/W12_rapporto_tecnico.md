# W12 — Rapporto tecnico (inglese) sul progetto WSP / Text-to-SQL
Stato: pronto (bozza) · Priorità: alta · Serve: —

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
(da compilare)
