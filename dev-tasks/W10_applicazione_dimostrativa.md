# W10 — Applicazione dimostrativa di data analysis self-hosted
Stato: **prima versione funzionante, provata con Apertus reale via HTTP (2 domande); interfaccia nel browser non verificata** · Priorità: media-alta · Serve: W03 (tool), un checkpoint servibile

## Obiettivo
Dimostrare che Apertus (modificato) svolge il compito centrale in un'applicazione concreta (regola 1), girando in locale.

## Contesto
Un semplice benchmark potrebbe non bastare per il requisito del core AI task. L'app deve usare solo Apertus e componenti open-weights/deterministici (DuckDB), senza API proprietarie a runtime.

## Passi
1. Definisci con Nikola interfaccia e workflow (es. CLI o piccola web app locale): domanda in linguaggio naturale → schema → SQL generato da Apertus → esecuzione DuckDB → risposta.
   **Proposta del 10 nov 2026 (da confermare):** "analista dei dati aperti svizzeri": l'utente chiede in DE/FR/IT/EN, l'app mostra la query generata, la esegue in locale su DuckDB e
   **spiega il risultato**; opzione per confrontare la risposta del modello originale e di quello modificato (un solo modello caricato alla volta sul Mac). Deve rendere il valore chiaro in circa 2 minuti.
2. Dataset di esempio con licenza verificata (W02).
3. Gira senza rete verso l'esterno (solo l'endpoint del modello locale); prova con `--network none` per tutto tranne il modello.
4. Elenca nel rapporto cosa fa Apertus e cosa fa il codice deterministico.

## Criteri di accettazione
- Demo riproducibile in locale; nessuna chiamata a servizi AI proprietari (verificato dal controllo di conformità).

## Da non fare
- Nessuna API AI chiusa a runtime. Non presentare come risultato scientifico ciò che è una demo.

## Esito
Stato: **prima versione funzionante; provata con modello finto (test) e con Apertus reale (2 domande, 10 nov 2026 sera); interfaccia nel browser non verificata.**
- `app/analyst.py` (`make app`): pagina locale con scelta del dataset (15 schemi della Città di Zurigo, CC0), domanda libera in DE/FR/IT/EN, esempi di dev/val; mostra query eseguite (anche quelle in errore), tabella dell'ultima query riuscita, risposta, passi, tempo e nome del modello. Usa lo stesso ciclo e lo stesso ambiente SQL delle valutazioni (`run_task`, `SqlBox`, `SQL_SYSTEM`).
- Chi fa cosa (per il rapporto): Apertus = capire la domanda, scegliere tabelle/colonne, scrivere SQL, spiegare; codice deterministico = costruire il database, eseguire in sola lettura con timeout e limiti, mostrare i risultati. Nessun altro modello, nessuna API esterna.
- Sovranità: ascolta solo su `127.0.0.1`; nessuna risorsa esterna nella pagina; il testo del modello è inserito come testo; l'unica connessione in uscita è verso l'endpoint del modello. **Verificato** da `tests/test_app.py` (6 test): schemi, domanda→query→tabella→risposta con modello finto, richieste non valide rifiutate senza chiamare il modello, esempi mai dal test set, errore del modello riportato senza crash, pagina senza URL esterne né `innerHTML`.
- **Non verificato:** funzionamento con Apertus reale (tempi di decine di secondi per domanda misurati nelle run di valutazione, non nell'app); aspetto e usabilità nel browser; prova con `--network none`/air-gapped (dipende da W11 e da Docker); confronto affiancato originale/modificato (un solo modello per volta: serve riavviare il server); modalità con un checkpoint WSP/LoRA (non esistono).
- **Da fare:** prova dal vivo con il modello, scegliere con la squadra se serve il confronto originale/modificato nella stessa pagina, immagine Docker dell'app (W11).

**Prova con Apertus reale (10 nov 2026, sera, `--thinking off`, originale):** server avviato, app avviata come libreria e interrogata via HTTP su `127.0.0.1` con due domande vere.
- «Wie viele Personen wohnten im Jahr 2023 im Quartier Enge?» (schema `bevq`): una query corretta nella forma (`SELECT AnzBestWir … WHERE StichtagDatJahr = 2023 AND QuarLang = 'Enge'`), tabella con 1 riga (10035), risposta in tedesco coerente col risultato; 2 passi, 61 s.
- «Quel arrondissement comptait le moins d'habitants en 2020 ?» (schema `bevk`): query con ORDER BY … LIMIT 1, risultato `Kreis 1`, 5831, risposta in francese; 2 passi, 50 s. La query restituisce anche il conteggio (2 colonne): lo stesso comportamento che nel baseline penalizza la misura rigida.
- **Non verificato:** correttezza dei valori rispetto ai dati (non confrontata con un gold), l'aspetto della pagina nel browser, la prova air-gapped, il confronto affiancato originale/modificato. Tempo per domanda circa un minuto: per una demo dal vivo va tenuto conto della velocità del Mac.
