# T05 — Modalità con ragionamento in `mlx_lm.server`
Stato: pronto · Priorità: media · Serve: server MLX acceso

## Obiettivo
Sapere se il server locale rispetta un'opzione per attivare/disattivare il ragionamento (`chat_template_kwargs`), e come si comporta il modello con e senza. La scheda del modello dice che con il ragionamento le tool call non sono supportate; il gateway ufficiale offre due modelli separati (`...-thinking` e non).

## Passi
1. Leggi `../../models/apertus-v1.5-8b-mlx-bf16/chat_template.jinja` e trova **il nome reale** della variabile che controlla il ragionamento (non assumerlo: scrivilo nell'Esito con la riga del template). Indizio già visto, da verificare leggendo il contesto: alla riga 182 il template contiene `enable_thinking is defined and enable_thinking`.
2. Con una richiesta di prova (`curl` verso `/v1/chat/completions` o uno script in `scripts/`), prova a passare quella variabile tramite `chat_template_kwargs` e verifica se la risposta cambia (presenza di `<|inner_prefix|>…<|inner_suffix|>`).
3. Se funziona: aggiungi a `agentbench run` un'opzione per passarla (`extra_body` è già registrato in `meta.json`) e un test con il server finto.
4. Esegui la suite con ragionamento attivo (se possibile) e riporta cosa succede alle tool call.

## Criteri di accettazione
- Esito chiaro: "il server la rispetta / non la rispetta", con la prova (richiesta e risposta).
- Nessuna modifica ai risultati ufficiali senza il flag esplicito.

## Esito
(da compilare)
