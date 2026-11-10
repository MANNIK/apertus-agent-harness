"""Tabelle di potenza per il piano di analisi (docs/analysis_plan.md, W04).

Non usa dati di run: calcola solo proprietà dei test (Wilson, McNemar esatto) con `agentbench.stats`,
per dire in anticipo quanto sono larghi gli intervalli e quante discordanze servono. Nessun modello, nessuna rete.

Uso: .venv/bin/python scripts/power_table.py
"""
from agentbench.stats import mcnemar_exact, wilson

SIZES = (200, 300, 500)
PROPORTIONS = (0.3, 0.5, 0.7)
DISCORDANT_FRACTIONS = (0.10, 0.20)
ALPHAS = (0.05, 0.05 / 3)  # senza correzione; Holm, primo passo con 3 confronti


def wilson_table() -> None:
    print("Semi-ampiezza dell'intervallo di Wilson al 95% (punti percentuali)")
    print("n    " + "  ".join(f"p={p:.0%}" for p in PROPORTIONS))
    for n in SIZES:
        cells = []
        for p in PROPORTIONS:
            lo, hi = wilson(round(p * n), n)
            cells.append(f"{50 * (hi - lo):5.1f}")
        print(f"{n:<4} " + "  ".join(cells))


def mcnemar_table() -> None:
    print("\nMcNemar esatto, due code: miglioramento netto minimo (punti percentuali su N task) per p < soglia")
    print("N    discordanti  soglia   b/c minimo       differenza netta")
    for n in SIZES:
        for frac in DISCORDANT_FRACTIONS:
            nd = round(frac * n)
            for alpha in ALPHAS:
                found = None
                for b in range(nd // 2 + 1, nd + 1):
                    if mcnemar_exact(b, nd - b) < alpha:
                        found = b
                        break
                if found is None:
                    print(f"{n:<4} {nd:>4} ({frac:.0%})  {alpha:.4f}  non raggiungibile")
                else:
                    net = 100 * (2 * found - nd) / n
                    print(f"{n:<4} {nd:>4} ({frac:.0%})  {alpha:.4f}  {found}/{nd - found:<10} {net:5.1f} pp")


if __name__ == "__main__":
    wilson_table()
    mcnemar_table()
