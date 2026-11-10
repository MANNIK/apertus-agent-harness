# docs

- `analysis_plan.md` è la **pre-registrazione attuale** (WSP vs LoRA vs originale, Text-to-SQL, v0.1 del 10 nov 2026, in inglese). Contiene i punti **[OPEN]** che la squadra deve chiudere
  e datare nel "Decisions log" **prima della prima run WSP/LoRA**; dopo quella run ogni modifica va in "Deviations" con data e motivo. Non cambiarla guardando i risultati.
  Le tabelle di potenza (ampiezza di Wilson, discordanze minime per McNemar) vengono da `scripts/power_table.py`: ricalcolale se cambia la dimensione del test.
- `archive/analysis_plan_agentic_suite.md` è la pre-registrazione della **vecchia suite agentica**: solo storico, con le sue "Deviations".
- `technical_report.md`: **bozza riscritta il 10 nov 2026** (inglese, WSP/Text-to-SQL). Elenca ogni modello con versione e ruolo (tabella **generata** da `agentbench manifest --models models.yaml --lang en`, non a mano: un test lo verifica),
  architettura di deployment ancora TBD (regola 5). Ogni riga dei risultati deve citare una run (`(run: …)`): un numero senza run salvata non passa il test. Va aggiornata quando esistono run valide, i checkpoint WSP/LoRA e l'architettura.
- `dati.md`: licenze (verificato / parziale / non verificato), il dataset `zurich-sql` v0.1, limiti. `wsp_candidate_methods.md`: 3 metodi WSP (proposta, nessuno scelto). `lora_budget.md`: protocollo e budget LoRA (proposta). `deployment_options.md`: opzioni della regola 5.
- `benchmark_esterni.md`: stima di fattibilità di BFCL/AgentDojo/τ-bench (compiti T10/T11, **obsoleti** per il nuovo progetto; utili solo se in W13 serve una misura di regressione).
- Numeri nei documenti: solo da run salvate; cita la cartella della run. Mai arrotondare a favore.
- Distingui sempre **verificato** (comando/test eseguito) da **supposto**. WSP e i suoi effetti sono, finché non misurati, un'ipotesi.
