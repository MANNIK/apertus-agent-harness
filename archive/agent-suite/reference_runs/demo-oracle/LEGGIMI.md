# Run sintetica di riferimento

Questa cartella NON contiene i risultati di un modello. È stata prodotta da `scripts/build_demo.py`
con un server finto che esegue i percorsi corretti di tutti i task della suite.

Serve a verificare l'harness senza modello né rete: `make demo` rigioca queste risposte e deve dare il 100%.
Se non lo dà, è l'harness (o la suite di task) ad essere cambiato, non un modello.

Non citare mai questi numeri come prestazioni di Apertus.
