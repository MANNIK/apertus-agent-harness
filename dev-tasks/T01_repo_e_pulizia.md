# T01 — Repository git e pulizia della cartella
Stato: pronto · Priorità: alta

## Obiettivo
Avere un repository git pulito per il progetto, senza pesi né dati pesanti, con una prima cronologia sensata.

## Contesto
`apertus-agent-harness/` non è un repository git. Sopra c'è `models/` (16 GB, fuori dal progetto) e `apertus-agent-harness.zip` (copia vecchia del 5 nov).

## Passi
1. Dentro `apertus-agent-harness/` (non nella cartella superiore): `git init`, ramo `main`.
2. Controlla `.gitignore`: deve escludere `.venv/ .uv/ runs/ __pycache__/ *.egg-info/ .pytest_cache/ build/ dist/` (già presenti) e aggiungere `.DS_Store`, `.env`, `*.safetensors`, `models/`.
3. `reference_runs/` **deve** essere versionata (serve a `make demo` e ai test). `runs/` no.
4. Primo commit con tutto il progetto (messaggio chiaro, in italiano). Poi, se Nikola vuole, un repository remoto: **non crearlo né fare push** senza che lo chieda.
5. Non cancellare `apertus-agent-harness.zip`: sposta in `../_archivio/` se esiste la cartella, altrimenti lascialo e segnalalo.

## Criteri di accettazione
- `git status` pulito dopo il commit; `git ls-files | wc -l` ragionevole e nessun file oltre 5 MB (`git ls-files -z | xargs -0 ls -l` per controllare).
- `git check-ignore -v runs models` conferma che sono ignorati.
- I test passano ancora.

## Da non fare
- Nessun `git push`, nessuna creazione di repository remoti, nessuna modifica fuori da `apertus-agent-harness/`.
- Non mettere nel commit chiavi, token, `.env`, pesi.

## Esito
(da compilare)
