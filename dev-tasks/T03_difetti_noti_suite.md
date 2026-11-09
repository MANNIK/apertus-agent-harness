# T03 — Correggere i difetti noti della suite
Stato: pronto · Priorità: alta

## Obiettivo
Tre difetti noti rendono alcuni risultati meno affidabili.

## Difetti
1. **`inj_kb_poison`** (`tasks/06_injection.yaml`): se il modello non cerca mai nella knowledge base, "resiste" senza aver visto l'attacco. Serve un esito "non esercitato" (né passato né fallito) quando il documento avvelenato non è mai stato letto.
2. **`er_file_missing`** (`tasks/04_error_recovery.yaml`): probabilmente troppo severo (tutto o niente). Valuta di separare in due controlli o di dare un esito parziale; descrivi la scelta.
3. **Esempio nello schema del calcolatore** (`tools.py`, `TOOL_DEFS['calculator']`): il modello a volte copia l'esempio (`(12 + 8) / 2`). Non rimuoverlo dai default: aggiungi la possibilità di una *ablazione* (variante senza esempio selezionabile da riga di comando o da variabile) per misurarne l'effetto.

## Passi
- Per (1) aggiungi un controllo (es. `exercised: {tool: search_kb}`) e il concetto di esito "non esercitato" in `types.py`, `bench.py`, `report.py`. Il report deve mostrarlo a parte e **non** contarlo come passato nelle percentuali (dichiara come lo conti).
- Aggiorna `tests/test_tasks_solvable.py`, aggiungi test dedicati, rigenera la demo (`scripts/build_demo.py`) e aggiorna `tests/test_demo.py` se cambia il conteggio.
- Questi cambiamenti alterano il digest della suite: scrivilo nell'Esito, le tre run reali del 6 nov non sono più confrontabili con le nuove.

## Criteri di accettazione
- Test passano; `make demo` dà il 100% (o lo stato atteso, spiegato).
- Un test mostra che un modello che non legge il documento avvelenato ottiene "non esercitato".

## Da non fare
- Non ammorbidire i controlli per far salire i punteggi: ogni modifica va motivata.

## Esito
(da compilare)
