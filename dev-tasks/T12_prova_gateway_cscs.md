# T12 — Prova del gateway CSCS/Keera
Stato: **bloccato fino al 27 nov 2026, ore 08:00** (la chiave di squadra si sblocca allora; si chiede a Sabine Wildemann sul posto o su Discord) · Priorità: alta il giorno dell'hackathon

## Obiettivo
Rifare la suite sul modello **ufficiale** servito da CSCS e confrontarla con la nostra copia MLX locale, per separare gli errori della conversione di terzi dal comportamento di Apertus.

## Dati (dalla scheda "Perks")
- Endpoint: `https://gateway.keera.ch/api/v1`. Modelli: `apertus-v1-5-8b`, `apertus-v1-5-70b` (con tool call); le versioni `-thinking` non supportano tool call.
- Non è noto se il gateway sia compatibile OpenAI al 100% né quali limiti di richieste abbia: scoprilo con la prima chiamata.

## Passi
1. Prerequisito: T02 fatto (host consentito). La chiave la imposta Nikola: `export LLM_API_KEY=…` **nel proprio terminale**; non scriverla in nessun file, log o messaggio.
2. `LLM_BASE_URL=https://gateway.keera.ch/api/v1 LLM_NAME=apertus-v1-5-8b .venv/bin/agentbench smoke`: la tool call arriva strutturata o come testo? Annota il messaggio grezzo (senza la chiave).
3. Suite completa, stessa configurazione della run locale (stesso prompt, temperatura 0): `--out runs/keera-8b-…`. Rispetta eventuali limiti di richieste (pause, ritentativi) e annotali.
4. `agentbench compare` tra la run locale e quella del gateway: scrivi quanti task cambiano e quali. Distingui differenze dovute al server (parametri, template) da quelle del modello solo se hai prove.
5. Se c'è tempo: stessa suite su `apertus-v1-5-70b`.
6. `make compliance` e `make manifest` sulle nuove run.

## Criteri di accettazione
- Run registrate con `calls.jsonl`; confronto locale/gateway con intervalli e McNemar; note sulle differenze.

## Da non fare
- Non stampare né salvare la chiave. Non superare i limiti d'uso. Non cambiare i parametri tra le due run senza dichiararlo.

## Esito
(da compilare)
