# W13 — Misura di regressione su capacità non ottimizzate
Stato: **set proposto e implementato (36 item); da confermare dalla squadra** · Priorità: media · Serve: decisione di Nikola sul set

## Obiettivo
Poter dire se WSP o LoRA peggiorano capacità diverse dal Text-to-SQL (la 'Regression Rate' del documento), ora che la suite agentica non c'è più.

## Contesto
Il set di regressione non è stato scelto. Servono pochi item deterministici o con risposta verificabile, in lingue e domini diversi, con licenza permissiva; un giudice, se serve, deve essere open-weights (regola 4).

## Passi
1. Proponi 2–3 opzioni (es. piccolo set a risposta verificabile creato da noi, o sottoinsieme di un benchmark open con licenza controllata) con costi, tempi e rischi.
2. Fissa il set e il criterio di 'regressione' in W04 prima di vedere i risultati.
3. Implementa la valutazione con le stesse regole di registrazione/replay.

## Criteri di accettazione
- Set e criterio dichiarati; licenze verificate; esecuzione riproducibile.

## Da non fare
- Non scegliere il set guardando cosa fa peggiorare o migliorare i modelli.

## Esito
Stato: **proposta implementata (10 nov 2026): set `general-v0.1` con 36 item; la scelta finale spetta alla squadra.**
- Opzione scelta per la proposta: set a risposta verificabile **creato da noi** (nessun problema di licenza, nessun giudice): 36 item in DE/FR/IT/EN (aritmetica, unità, estrazione da testo, traduzione di singole parole, conoscenza svizzera e generale, formato, ragionamento), controlli deterministici sul testo. Le altre opzioni (sottoinsieme di un benchmark aperto, con licenza da controllare) restano non valutate.
- `tasks/regression/sanity.yaml` (11 item, controllo di sanità durante le iterazioni) e `final.yaml` (25 item, misura finale, protetta da `--final-test`); generati da `scripts/build_regression_tasks.py`.
- Verificato: `tests/test_regression_set.py` (38 test): ogni item passa con la risposta corretta e fallisce con una risposta vuota; il set finale è protetto.
- **Non verificato:** nessun modello è stato eseguito su questo set; i controlli sul testo sono euristiche (un'altra formulazione corretta può fallire); gli item sono pochi, quindi gli intervalli sono larghi; la conoscenza generale può essere nei dati di addestramento.
- Il criterio di «regressione» (item giusti con l'originale e sbagliati col modello modificato, test di McNemar) va fissato dalla squadra in `docs/analysis_plan.md` §13 prima delle run.

