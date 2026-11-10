# W02 — Dati e licenze: BIRD, DuckDB e dataset analitico
Stato: **in corso** (licenze verificate in parte, dataset non ancora costruito) · Priorità: alta · Serve: W01 (fatto)

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
6. **Dataset svizzero multilingue (aggiunto il 10 nov 2026, dal confronto con i progetti di ottobre):** valuta come dataset principale tabelle reali di open data svizzeri
   (candidati da verificare uno per uno, non a memoria: opendata.swiss, BFS, Swissvotes, OpenParlData) con domande in DE/FR/IT/EN. Per ogni fonte: licenza, condizioni di
   ridistribuzione, dimensione, data del controllo. Motivo: i progetti premiati sono ancorati alla Svizzera e questo rende misurabile la robustezza alla lingua della domanda.
   BIRD resta set secondario/di controllo; annota che **non sappiamo** se BIRD/Spider sono nei dati di addestramento di Apertus (rischio di contaminazione) e non scriverlo come fatto.
   **Pitch di riferimento (10 nov 2026):** "interroga i dati pubblici svizzeri nella tua lingua, in locale, con un modello Apertus modificato in modo misurabile e ispezionabile".
   Selezione delle fonti: poche e pulite (2–3 con licenza verificata) meglio di molte dubbie; scarta entro pochi giorni ogni fonte senza licenza chiara.
   **Costruisci il dataset con queste caratteristiche** (ipotesi da confermare sui file reali, non fatti verificati):
   - *schema-linking cross-lingua:* tabelle con nomi di colonna in una lingua (es. tedesco) e domande in un'altra (FR/IT/EN); la coppia lingua-schema/lingua-domanda è registrata per ogni task;
   - *trappole di formato svizzere:* date `31.12.2024`, numeri con apostrofo `1'234.50`, CHF, codici di cantone, simboli al posto dei valori mancanti, caratteri accentati: etichettale per poterle analizzare;
   - *domande su dati che i modelli tendono a ricordare male* (es. esiti di votazioni): la risposta deve venire dall'esecuzione, non dalla memoria;
   - opzionale, solo se la squadra ha madrelingua e tempo: un piccolo set di domande in svizzero tedesco come test di generalizzazione (da scrivere a mano, non generato).
7. Lo split del test è **per schema** (schemi mai visti), non solo per domanda; la lingua della domanda è una variabile registrata per ogni task.

## Criteri di accettazione
- Documento `docs/dati.md` con licenze verificate (con data e fonte), split e impronte.
- Nessun dato scaricato o committato prima del controllo di licenza.

## Da non fare
- Non committare dataset senza licenza chiara. Non usare il test per scegliere nulla. Nessun dato reale o personale.

## Esito
**Parziale (10 nov 2026)** — documento `docs/dati.md` scritto; dataset e split **non** ancora fatti.

**Verificato**
- Swissvotes: **CC BY 4.0** letto sulla pagina ufficiale; file CSV scaricato (2.736.956 byte, sha256 in `docs/dati.md`), 719 righe × 874 colonne, UTF-8 con BOM, separatore `;`. `scripts/fetch_swissvotes.sh` scarica e verifica lo sha256 (provato: stesso hash).
- BIRD: dichiara **CC BY-SA 4.0** sul sito e nel README ufficiali (dal 27 apr 2024). Nessuna dimensione del dev set trovata.

**Non verificato / aperto**
- DuckDB (MIT) e Spider: solo da riassunti di ricerca. opendata.swiss/BFS: le pagine rispondono 403 ai programmi: **serve la lettura umana nel browser** dataset per dataset. OpenParlData: licenza dei dati non trovata.
- Il paper di BIRD (2023) sarebbe stato CC BY-NC secondo un riassunto di ricerca: non confermato.
- Share-alike di BIRD e pesi addestrati: questione aperta, non consulenza legale; per ora BIRD solo valutazione.
- **Problema di fondo:** con la sola fonte Swissvotes lo split per schema è debole (un solo dominio). Serve la decisione della squadra tra le opzioni in `docs/dati.md` §3.
- Nessuno split, nessun dataset Text-to-SQL, nessuna query gold, nessuna verifica delle licenze delle dipendenze Python.

**Aggiornamento (10 nov 2026, sera) — nuova fonte principale proposta: Open Data Stadt Zürich.**
- Nikola: «dati reali» e «altre fonti». L'API CKAN di `data.stadt-zuerich.ch` risponde: **942 dataset, 913 CC0, 13 CC BY, 16 CC BY-SA, 629 con CSV** (verificato con la pagina del portale, stessi conteggi). Le pagine legali sono 404: testo formale **non letto**, nulla su uso per IA o diritti di terzi.
- `opendata.swiss` e la sua API rispondono 403 ai programmi (non aggirato). Basilea (`data.bs.ch`): API raggiungibile, licenze **non** lette.
- Selezione e regole in `docs/dati.md` §2b (CC0 per singolo dataset, niente nomi di persone, un dataset = uno schema = un solo split). **Nulla è stato ancora scaricato né trasformato in task.**
- Prossimi passi: scaricare la rosa proposta con sha256, ispezionare colonne e valori, scrivere domande e gold (DE/FR/IT/EN) con revisione umana, definire gli split per schema.
