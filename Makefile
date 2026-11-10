# Comandi ripetibili. `make help` li elenca. Nessun comando usa servizi esterni: il modello è un endpoint
# OpenAI-compatibile scelto da te (LLM_BASE_URL, LLM_NAME, LLM_API_KEY).
AB = .venv/bin/agentbench
PY = .venv/bin/python
.DEFAULT_GOAL := help
.PHONY: help setup test demo smoke run compare compliance manifest judge docker-build docker-demo airgap-check clean data zurich-tasks

help:  ## mostra questa guida
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ —/'

setup:  ## installa tutto in locale (uv, Python, dipendenze) senza toccare il resto del sistema
	bash scripts/bootstrap.sh

test:  ## esegue i test (nessun modello necessario)
	$(PY) -m pytest -q

demo:  ## rigioca la run sintetica Text-to-SQL (oracolo che esegue le query gold): deve dare il 100%, senza modello né rete; serve l'extra sql
	$(AB) run --replay reference_runs/demo-oracle-sql --out runs/demo-replay --tasks tasks

smoke:  ## prova veloce contro il modello configurato (LLM_BASE_URL, LLM_NAME)
	$(AB) smoke

run:  ## run contro il modello configurato; finché non c'è il set Text-to-SQL (W03) serve --tasks: make run TASKS=cartella REPEATS=1
	$(AB) run --repeats $(or $(REPEATS),1) $(if $(TASKS),--tasks $(TASKS),)

compare:  ## confronta due run: make compare A=runs/base B=runs/modificato
	$(AB) compare $(A) $(B)

compliance:  ## controlla le regole del hackathon (modelli dichiarati, open-weights, endpoint locali, integrità)
	$(AB) compliance --models models.yaml

manifest:  ## genera l'elenco dei modelli per il rapporto tecnico (regola 6)
	$(AB) manifest --models models.yaml

judge:  ## giudice open-weights opzionale: make judge RUN=runs/xxx JUDGE_MODEL=... JUDGE_BASE_URL=...
	$(AB) judge $(RUN)

docker-build:  ## costruisce l'immagine (serve Docker)
	docker build -t apertus-agent-harness .

docker-demo:  ## esegue il comando predefinito dell'immagine (oggi: controllo di conformità, senza rete)
	docker run --rm --network none apertus-agent-harness

airgap-check:  ## comando predefinito senza rete nel container + prova che la rete è davvero bloccata (fallisce se il comando non passa o se la rete risponde)
	docker run --rm --network none apertus-agent-harness
	@if docker run --rm --network none --entrypoint python apertus-agent-harness -c "import urllib.request; urllib.request.urlopen('http://example.com', timeout=3)" >/dev/null 2>&1; then echo "✗ la rete NON è bloccata nel container"; exit 1; else echo "✓ comando passato e connessioni in uscita bloccate (--network none)"; fi

data:  ## riscarica i CSV CC0 della Città di Zurigo (rilegge la licenza dall'API; cambia gli sha256: vedi docs/dati.md)
	$(PY) scripts/fetch_zurich.py --force

zurich-tasks:  ## rigenera i task zurich-sql da data/zurich/ e scripts/zurich_spec.py (deterministico)
	$(PY) scripts/build_zurich_tasks.py

clean:  ## cancella solo i file temporanei di Python
	find . -name __pycache__ -type d -prune -exec rm -rf {} + ; rm -rf .pytest_cache
