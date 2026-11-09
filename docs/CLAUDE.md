# docs

- `analysis_plan.md` è la **pre-registrazione della vecchia suite agentica** (agente con tool finti): resta come storico, con le sue "Deviations". **La nuova pre-registrazione per
  WSP / Text-to-SQL (compito W04) la sostituisce** per il progetto attuale: ipotesi (a due code, non "migliora" per principio), tre condizioni (originale, WSP, LoRA), metriche,
  dimensione dei campioni, statistica con correzione per confronti multipli, protocollo dev/val/test, controlli di sanità del modello modificato, limiti.
  Non cambiarla dopo aver visto dati di WSP/LoRA: ogni modifica va in "Deviations" in fondo, con data e motivo.
- `technical_report.md` è una **bozza del vecchio progetto**: va riscritta (compito W12) in **inglese** per WSP/Text-to-SQL. Deve elencare ogni modello usato con versione e ruolo
  (regola 6; tabella generata con `agentbench manifest --models models.yaml --lang en`, non a mano), dichiarare l'architettura di deployment (regola 5), riportare
  parametri modificati e costo di adattamento, e tenere i risultati come `TBD (run: …)` finché non esistono run salvate.
- `benchmark_esterni.md`: stima di fattibilità di BFCL/AgentDojo/τ-bench (compiti T10/T11, **obsoleti** per il nuovo progetto; utili solo se in W13 serve una misura di regressione).
- Numeri nei documenti: solo da run salvate; cita la cartella della run. Mai arrotondare a favore.
- Distingui sempre **verificato** (comando/test eseguito) da **supposto**. WSP e i suoi effetti sono, finché non misurati, un'ipotesi.
