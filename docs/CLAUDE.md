# docs

- `analysis_plan.md` è la **pre-registrazione attuale** (WSP vs LoRA vs originale, Text-to-SQL, v0.1 del 10 nov 2026, in inglese). Contiene i punti **[OPEN]** che la squadra deve chiudere
  e datare nel "Decisions log" **prima della prima run WSP/LoRA**; dopo quella run ogni modifica va in "Deviations" con data e motivo. Non cambiarla guardando i risultati.
  Le tabelle di potenza (ampiezza di Wilson, discordanze minime per McNemar) vengono da `scripts/power_table.py`: ricalcolale se cambia la dimensione del test.
- `archive/analysis_plan_agentic_suite.md` è la pre-registrazione della **vecchia suite agentica**: solo storico, con le sue "Deviations".
- `technical_report.md` è una **bozza del vecchio progetto**: va riscritta (compito W12) in **inglese** per WSP/Text-to-SQL. Deve elencare ogni modello usato con versione e ruolo
  (regola 6; tabella generata con `agentbench manifest --models models.yaml --lang en`, non a mano), dichiarare l'architettura di deployment (regola 5), riportare
  parametri modificati e costo di adattamento, e tenere i risultati come `TBD (run: …)` finché non esistono run salvate.
- `benchmark_esterni.md`: stima di fattibilità di BFCL/AgentDojo/τ-bench (compiti T10/T11, **obsoleti** per il nuovo progetto; utili solo se in W13 serve una misura di regressione).
- Numeri nei documenti: solo da run salvate; cita la cartella della run. Mai arrotondare a favore.
- Distingui sempre **verificato** (comando/test eseguito) da **supposto**. WSP e i suoi effetti sono, finché non misurati, un'ipotesi.
