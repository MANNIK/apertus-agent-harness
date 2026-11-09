# T13 — Bozza del rapporto tecnico (inglese)
Stato: pronto · Priorità: alta

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
(da compilare)
