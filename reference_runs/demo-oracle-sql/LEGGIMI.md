# Run sintetica di riferimento (Text-to-SQL)

Questa cartella NON contiene i risultati di un modello. È stata prodotta da `scripts/build_demo_sql.py` con un server finto
che esegue la query gold di ogni task sintetico di `tasks/demo_sales.yaml` e risponde con i valori trovati.

Serve a verificare l'harness senza modello né rete: `make demo` rigioca queste risposte e deve dare il 100%.
Se non lo dà, è l'harness (o l'insieme di task) ad essere cambiato, non un modello.

Non citare mai questi numeri come prestazioni di Apertus.
