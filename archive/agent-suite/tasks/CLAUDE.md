# tasks — i task di valutazione

## Stato attuale (ereditato)
`tasks/*.yaml` contiene la **suite agentica del vecchio progetto** (62 task, 11 gruppi, tool finti). **Viene archiviata dal compito W01** (in `archive/agent-suite/`).
Finché non è fatto: non aggiungere né modificare task lì dentro, e non usarla come misura del nuovo progetto. Le regole storiche (task deterministici,
risolvibili, id stabili, digest della suite, esito `not_exercised`) restano nel codice e nei test.

## Regole per il nuovo set Text-to-SQL (da creare in W02/W03)
- **Split fissi e versionati:** `dev` (iterazioni), `val` (scelta tra varianti), `test` (solo alla fine). Ogni split ha un'impronta (sha256) salvata in `meta.json` delle run.
  Il test non si usa mai per scegliere modifiche ai pesi né per tarare prompt o controlli.
- **Generalizzazione:** il test contiene **schemi mai visti** nel dev/val (e nei dati di addestramento di LoRA e di qualunque procedura WSP).
- **Risolvibilità:** ogni task ha una query gold che si esegue e produce il risultato atteso; c'è un test che le esegue tutte.
- **Valutazione per esecuzione:** si confronta l'insieme dei risultati (regole su ordine, duplicati, tipi e arrotondamenti dichiarate una volta e valide per tutti), non il testo della query.
- **Determinismo:** dati e schemi fissi (DuckDB in memoria o file versionati); nessun valore casuale o dipendente dalla data.
- **Licenze:** BIRD e ogni altro dataset: licenza da **verificare** prima di scaricarlo e di includere dati nel repo; dichiara fonte e versione. Nessun dato reale o personale.
- **Dimensioni:** obiettivo iniziale 200–500 task indipendenti; con meno task si vedono solo effetti grandi (scrivi l'ampiezza dell'intervallo accanto a ogni affermazione).
- **Non ritoccare i controlli dopo aver visto gli esiti** delle condizioni WSP/LoRA: ogni correzione va in "Deviations" del piano di analisi.
- Gli id sono stabili (`categoria_descrizione` o id del dataset): non rinominarli, compaiono nei report e nei confronti.
