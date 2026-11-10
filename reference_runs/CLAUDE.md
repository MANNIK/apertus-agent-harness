# reference_runs

`demo-oracle-sql` è una run **sintetica** (server finto che esegue le query gold dei task di `tasks/demo_sales.yaml`): serve solo a verificare l'harness (`make demo`, deve dare il 100%).
**Non è un risultato di Apertus: non citarla come tale.** Si rigenera con `.venv/bin/python scripts/build_demo_sql.py`; non modificare i file a mano (gli sha256 in `meta.json` non tornerebbero).
Se cambi `tasks/demo_sales.yaml`, i parametri dell'ambiente SQL o il formato dei risultati, rigenerala. La demo della vecchia suite agentica è in `archive/agent-suite/reference_runs/`.
