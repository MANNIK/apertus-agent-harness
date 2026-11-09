# W03 — Ambiente Text-to-SQL: tool `run_sql` e execution accuracy
Stato: pronto dopo W01–W02 · Priorità: alta · Serve: W01, W02

## Obiettivo
Far eseguire ad Apertus query su DuckDB e valutare i risultati in modo deterministico (execution accuracy e correttezza della risposta finale).

## Contesto
Il punteggio ufficiale non usa nessun LLM: si eseguono la query del modello e la query gold e si confrontano i risultati. DuckDB è eseguito in locale (memoria/file), mai in rete; sta in un extra opzionale.

## Passi
1. Aggiungi DuckDB come **extra opzionale** (licenza verificata in W02) senza rompere `scan_network_imports`.
2. Implementa il tool `run_sql` (solo lettura, timeout e limite di righe dichiarati) e il caricamento dello schema nel prompt o come tool di ispezione.
3. Implementa il controllo di execution accuracy: regole su ordine, duplicati, NULL, tipi e arrotondamenti dichiarate una volta e valide per tutte le condizioni; più il controllo sulla risposta finale (numeri/valori).
4. Scrivi `tests/` con DuckDB in memoria: ogni task ha la query gold in un test di risolvibilità; query sbagliate (colonne/righe in più, ordine, NULL) devono fallire.
5. Crea una demo sintetica (oracolo che esegue le query gold) per `make demo`, con le stesse regole di `demo-oracle`: non è un risultato di Apertus.
6. Aggiorna `src/agentbench/CLAUDE.md`, `tasks/CLAUDE.md` e `tests/CLAUDE.md` con quanto imparato.

## Criteri di accettazione
- Test verdi; demo al 100%; `make compliance` senza errori.
- Un test mostra che l'execution accuracy non dipende dal testo della query.

## Da non fare
- Nessun LLM nel punteggio. Nessuna rete. Non ammorbidire i confronti per far salire i punteggi.

## Esito
(da compilare)
