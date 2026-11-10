# Immagine minimale per rieseguire l'harness da un checkout pulito, anche senza rete (regola 5: deployabile on-premise / air-gapped).
# NON contiene alcun modello: per una run vera si passa un endpoint OpenAI-compatibile locale (LLM_BASE_URL, LLM_NAME).
# La vecchia suite agentica e la sua demo sono archiviate (archive/agent-suite/) e non stanno nell'immagine; l'immagine
# con i dati Text-to-SQL e l'applicazione si completa in W03/W10/W11.
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY models.yaml ./
# Predefinito: controlla le regole del hackathon sul registro dei modelli (nessun modello, nessuna rete).
CMD ["agentbench", "compliance", "--models", "models.yaml"]
