# W04 — Protocollo di valutazione e nuova pre-registrazione
Stato: bozza scritta, punti [OPEN] da chiudere con la squadra · Priorità: alta · Serve: —

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
8. **Aggiunte del 10 nov 2026:** (a) confronto WSP/LoRA **a parità di parametri addestrabili/modificati**, di dati e di budget, oppure curva accuratezza vs % di parametri
   con i punti dichiarati; (b) soglia fissata prima per dichiarare "nessun margine" (baseline troppo alta o troppo bassa, vedi W05) e cosa si fa in quel caso;
   (c) la lingua della domanda (DE/FR/IT/EN) come strato dell'analisi; (d) i tentativi scartati sono riportati nel rapporto, non solo quelli riusciti.

## Criteri di accettazione
- Piano completo, datato, committato prima delle prime run WSP/LoRA.
- Ogni passo successivo che se ne discosta finisce in `Deviations`.

## Da non fare
- Non scriverlo dopo aver visto i risultati. Non fissare la conclusione ('WSP migliora').

## Esito
Stato: **bozza v0.1 scritta (10 nov 2026); da chiudere i punti [OPEN] prima della prima run WSP/LoRA.** Non ancora "completo" ai sensi del criterio di accettazione.

**Fatto**
- Vecchio piano spostato con `git mv` in `docs/archive/analysis_plan_agentic_suite.md` (contenuto invariato).
- Nuovo `docs/analysis_plan.md` (inglese): ipotesi H1–H3 a due code, tre condizioni con configurazione congelata, dati e split per schema, metriche (compresi regression rate, parametri modificati,
  costo di adattamento), statistica (Wilson, McNemar esatto, correzione di Holm sulla famiglia H1–H3, bootstrap per schema come analisi di sensibilità), protocollo anti-overfitting con registro di ogni tentativo,
  regola di parità di budget WSP/LoRA, cancello di fattibilità per W05, controlli di sanità, limiti, "Decisions log" e "Deviations" vuoti.
- `scripts/power_table.py` calcola le tabelle di potenza con `agentbench.stats`. **Eseguito il 10 nov 2026**: semi-ampiezza di Wilson 4,0–6,9 punti per n = 200–500; miglioramento netto minimo per McNemar
  esatto da 3,2 a 8,0 punti a seconda di N (200/300/500), quota di discordanti (10%/20%) e soglia (0,05 o 0,0167). Sono proprietà dei test, non risultati di run.
- `docs/CLAUDE.md` aggiornato.

**Punti [OPEN] che spettano alla squadra (non decisi da Claude)**
modalità di ragionamento (`--thinking on|off`); k ripetizioni se MLX non è deterministico; insieme e limiti del controllo di regressione/sanità (W13); regola di accettazione di una modifica WSP e budget di tentativi;
regola di parità di budget (proposta nel piano: LoRA con parametri addestrabili ≤ quelli di WSP, più un LoRA convenzionale di riferimento); protocollo LoRA (dati, rango, budget GPU); soglie del cancello di fattibilità
(proposte: limite superiore di Wilson < 15% o limite inferiore > 85% sul val); dimensione effettiva del test (dipende da W02).

**Non verificato**
- Le soglie numeriche del cancello sono **proposte mie**, non derivate da dati.
- Le tabelle di potenza assumono quote di discordanti del 10% e 20%: valori ipotetici, non misurati.
- Il test set sarà solo una parte dei 200–500 task di W02, quindi le tabelle sono ottimistiche finché non c'è la dimensione reale.
- Non esiste ancora il documento `docs/dati.md` (W02) a cui il piano rimanda.
