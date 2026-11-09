# T05 — Modalità con ragionamento in `mlx_lm.server`
Stato: fatto (storico) · Priorità: media

> **Storico (progetto precedente).** La conclusione è decisiva anche per il nuovo progetto: la condizione di ragionamento va fissata e dichiarata in ogni run (vedi W05).

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
**Verificato il 10 nov 2026 (server `mlx_lm.server` 0.32.2 locale, pesi `apertus-v1.5-8b-mlx-bf16`):**
- **Variabile del template:** `enable_thinking`. In `chat_template.jinja` riga 182: `{%- if enable_thinking is defined and enable_thinking -%} … 'enabled\n' … {%- else -%} … 'disabled\n'`, dentro la riga `Deliberation:` del messaggio developer.
- **Il server la rispetta** passata come `chat_template_kwargs`. Domanda di prova "What is 17 * 23? Answer briefly.", temperatura 0, `max_tokens` 400:
  - senza kwargs: 93 token, 14,2 s, risposta `"<|inner_prefix|>We need to compute 17 * 23 … <|inner_suffix|>391"` → **ragiona**;
  - `{"chat_template_kwargs": {"enable_thinking": false}}`: 4 token, 0,9 s, risposta `"391"` → **non ragiona**;
  - `{"chat_template_kwargs": {"enable_thinking": true}}`: identica al caso senza kwargs (93 token, 14,0 s).
- **Conseguenza:** con questo server il ragionamento è **attivo per impostazione predefinita** (anche se il template, senza la variabile, scriverebbe `disabled`: la differenza non è spiegata; non l'ho indagata). Le run senza flag sono quindi "con ragionamento".
- **Flag aggiunto:** `agentbench run/smoke --thinking on|off` (fonde `chat_template_kwargs.enable_thinking` in `extra_body`, registrato in `meta.json`); senza flag non si invia nulla. 3 test con server finto in `tests/test_thinking_flag.py`.
- La tool call di prova (`smoke`) è arrivata come testo `<|tools_prefix|>[{"get_weather": {...}}]` (non strutturata) e il parser di riserva l'ha letta.

**Non fatto:** esecuzione completa della suite con `--thinking off`; confronto sistematico delle tool call con ragionamento attivo/disattivo.
