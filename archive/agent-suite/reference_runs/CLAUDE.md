# reference_runs

`demo-oracle` è una run **sintetica** del vecchio progetto (server finto che esegue i percorsi corretti della suite agentica), serve solo a verificare l'harness
(`make demo`). **Non è un risultato di Apertus: non citarla come tale.** Si rigenera con `.venv/bin/python scripts/build_demo.py`; non modificare i file a mano
(i sha256 in `meta.json` non tornerebbero).
Sarà archiviata insieme alla suite agentica (compito W01) e sostituita da una demo sintetica analoga per il Text-to-SQL (oracolo che esegue le query gold), con le stesse regole.
