# W04 — Protocollo di valutazione e nuova pre-registrazione
Stato: pronto · Priorità: alta · Serve: —

## Obiettivo
Scrivere, **prima di vedere dati di WSP e LoRA**, il piano di analisi del nuovo progetto in `docs/analysis_plan.md` (inglese).

## Contesto
Il piano attuale riguarda la vecchia suite e resta come storico (spostarlo in `docs/archive/`). Il documento di progetto elenca condizioni, metriche e questioni aperte.

## Passi
1. Ipotesi primaria a due code: WSP cambia l'execution accuracy rispetto all'originale; secondaria: costo di adattamento e parametri modificati rispetto a LoRA.
2. Tre condizioni (originale, WSP, LoRA), stessa configurazione di inferenza (`--thinking`, temperatura, max_tokens, seed) e stesso test set; cosa è congelato.
3. Metriche: execution accuracy, answer correctness, generalizzazione (schemi nuovi), regression rate (vedi W13), latenza, VRAM, parametri modificati (numero e %), costo di adattamento.
4. Statistica: Wilson per ciascuna condizione; McNemar a coppie sui task accoppiati; **correzione per confronti multipli** (es. Holm) dichiarata; dimensione minima del campione e ampiezza degli intervalli attesi.
5. Protocollo anti-overfitting: dev/val per iterare, test una sola volta; registro di tutte le modifiche tentate; criteri di accettazione di una modifica fissati prima.
6. Controlli di sanità del modello modificato (non è semplicemente rotto): pochi prompt non-SQL; cosa invalida il confronto.
7. Limiti noti e sezione `Deviations` vuota con data.

## Criteri di accettazione
- Piano completo, datato, committato prima delle prime run WSP/LoRA.
- Ogni passo successivo che se ne discosta finisce in `Deviations`.

## Da non fare
- Non scriverlo dopo aver visto i risultati. Non fissare la conclusione ('WSP migliora').

## Esito
(da compilare)
