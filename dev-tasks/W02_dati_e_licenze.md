# W02 — Dati e licenze: BIRD, DuckDB e dataset analitico
Stato: pronto · Priorità: alta · Serve: W01 (non strettamente)

## Obiettivo
Decidere quali dati usare per il Text-to-SQL, verificarne le licenze e fissare gli split dev / val / test.

## Contesto
Il documento di progetto propone BIRD (Text-to-SQL), un dataset analitico personalizzato e un test set mai usato per scegliere le modifiche. Obiettivo iniziale 200–500 task indipendenti. La **licenza di BIRD e di DuckDB non è stata verificata**.

## Passi
1. Verifica sulla fonte (repo/scheda ufficiale, non a memoria) licenza e condizioni d'uso di BIRD, di DuckDB e delle loro dipendenze; scrivi fonte, versione e data del controllo.
2. Se BIRD non è utilizzabile (licenza, dimensioni, ridistribuzione), proponi alternative permissive (es. Spider o set sintetico) **solo dopo averne verificato la licenza**.
3. Progetta il dataset personalizzato di casi analitici (schemi sintetici piccoli, domande in IT/DE/FR/EN se utile) e il processo di creazione delle query gold.
4. Definisci gli split: dev (iterare), val (scegliere tra varianti), test (solo alla fine), con **schemi del test mai visti** in dev/val e nei dati di addestramento di LoRA/WSP. Fissali con id e impronta sha256.
5. Stima dimensioni e spazio su disco; i dati grandi restano fuori dal repository (solo script di scaricamento e impronte).

## Criteri di accettazione
- Documento `docs/dati.md` con licenze verificate (con data e fonte), split e impronte.
- Nessun dato scaricato o committato prima del controllo di licenza.

## Da non fare
- Non committare dataset senza licenza chiara. Non usare il test per scegliere nulla. Nessun dato reale o personale.

## Esito
(da compilare)
