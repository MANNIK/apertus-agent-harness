# Immagine minimale per rieseguire l'harness da un checkout pulito, anche senza rete (regola 5: deployabile on-premise / air-gapped).
# NON contiene alcun modello: per una run vera si passa un endpoint OpenAI-compatibile locale (LLM_BASE_URL, LLM_NAME).
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY tasks ./tasks
COPY prompts ./prompts
COPY rubrics ./rubrics
COPY models.yaml ./
COPY reference_runs ./reference_runs
# Predefinito: rigioca la run sintetica (nessun modello, nessuna rete) e controlla le regole.
CMD ["sh", "-c", "agentbench run --replay reference_runs/demo-oracle --out /tmp/demo && agentbench compliance /tmp/demo --models models.yaml"]
