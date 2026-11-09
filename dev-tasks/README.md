# dev-tasks — compiti da svolgere con Claude Code

Un file per compito (`Txx_nome.md`). Leggi prima `../CLAUDE.md` e `../../CLAUDE.md`: contengono le regole del hackathon e i limiti del progetto.

## Come si lavora
1. Scegli un compito con stato **pronto** (non "bloccato"). Parti dalla priorità più alta.
2. Un compito alla volta; lavora in un ramo git se il repository esiste (compito T01).
3. Fai solo ciò che il compito chiede. Se serve altro, scrivilo nella sezione "Esito" come nuova proposta.
4. Alla fine: test passati, `make compliance` senza errori, documenti allineati.
5. Compila in fondo al file la sezione **Esito**: cosa hai fatto, cosa hai **verificato davvero** (comando e risultato) e cosa **non** hai potuto verificare. Cambia la riga `Stato:` in cima.
6. Non inventare risultati: se un comando non gira, scrivilo.

## Indice (ordine consigliato)
| ID | Compito | Priorità | Stato | Serve |
| --- | --- | --- | --- | --- |
| T01 | Repository git e pulizia della cartella | alta | pronto | — |
| T02 | Dichiarare gli endpoint consentiti (gateway CSCS/Keera) nella conformità | alta | pronto | — |
| T03 | Correggere i difetti noti della suite | alta | pronto | — |
| T04 | Rieseguire le prove reali con registrazione e misurare la ripetibilità | alta | pronto | server MLX acceso (Nikola) |
| T05 | Verificare la modalità con ragionamento (`enable_thinking`) in `mlx_lm.server` | media | pronto | server MLX acceso |
| T06 | Pipeline di confronto pesi originali contro pesi modificati | alta | **bloccato** | risposte del collega |
| T07 | Prova di Docker sul Mac e verifica "senza rete" | media | pronto | Docker sul Mac |
| T08 | Giudice open-weights con un vero modello | media | pronto | modello giudice che sta in 32 GB |
| T09 | Estendere la suite (lingue, chiamate parallele, catene lunghe) | media | pronto | — |
| T10 | Benchmark da paper: BFCL via EvalScope | media | pronto | controllo licenze |
| T11 | Benchmark da paper: AgentDojo e τ-bench con simulatore open-weights | bassa | pronto | T10 fatto |
| T12 | Prova del gateway CSCS/Keera | alta | **bloccato** fino al 27 nov 08:00 | chiave di squadra |
| T13 | Bozza del rapporto tecnico (inglese) | alta | pronto | — |

Messaggi in sospeso per Nikola (non sono compiti di codice): risposta degli organizzatori (progetti personali, pesi propri), risposta del collega (tecnica, formato, intensità, hardware).
