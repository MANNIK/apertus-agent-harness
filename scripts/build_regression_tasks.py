"""Genera il set di regressione `general-v0.1` (W13): 36 item su capacità NON ottimizzate (11 sanity + 25 final), senza tool, con controlli deterministici sul testo.

Scopo: sapere se WSP o LoRA peggiorano capacità diverse dal Text-to-SQL (la "regression rate"). Item scritti a mano, risposte verificabili,
quattro lingue (DE/FR/IT/EN), nessun giudice AI. Due insiemi:
  - `sanity`  (11 item, split "regression_sanity"): controllo di sanità del checkpoint durante le iterazioni (docs/analysis_plan.md §9).
  - `final`   (25 item, split "regression_final"): misura finale della regressione; protetto da `--final-test` come il test set.
Gli item sono PROPOSTI da Claude (strumento di sviluppo) e fissati prima di vedere risultati di modelli modificati; la scelta del set spetta alla squadra.
Domande di conoscenza generale: possono essere nei dati di addestramento di Apertus, ma qui interessa solo il confronto tra condizioni.

Uso:  .venv/bin/python scripts/build_regression_tasks.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

OUT = Path(__file__).resolve().parent.parent / "tasks" / "regression"

N = lambda v, tol=0.0: {"type": "final_number", "value": v, "tol": tol}  # noqa: E731
RX = lambda p: {"type": "final_regex", "pattern": p}  # noqa: E731
ALL = lambda *v: {"type": "final_contains_all", "values": list(v)}  # noqa: E731

# (id, lingua, capacità, domanda, controlli, set)  — set: "s" = sanity, "f" = final
ITEMS = [
    ("train_arrival", "en", "arithmetic", "A train leaves at 08:15 and the trip takes 2 hours and 50 minutes. At what time does it arrive? Answer in the format HH:MM.", [RX(r"\b11:05\b")], "f"),
    ("notebooks", "de", "arithmetic", "Ein Heft kostet 3 Franken 50. Wie viele Franken kosten 6 Hefte? Antworte nur mit der Zahl.", [N(21)], "f"),
    ("bottles", "fr", "arithmetic", "Une bouteille contient 1,5 litre. Combien de litres y a-t-il dans 8 bouteilles ?", [N(12)], "s"),
    ("stickers", "it", "arithmetic", "Maria ha 48 figurine e ne regala un quarto. Quante figurine le rimangono?", [N(36)], "f"),
    ("mult", "en", "arithmetic", "What is 17 times 23?", [N(391)], "s"),
    ("percent", "de", "arithmetic", "Was ist 15 % von 240?", [N(36)], "f"),
    ("discount", "fr", "arithmetic", "Quel est le prix après une réduction de 20 % sur 150 francs ?", [N(120)], "f"),
    ("division", "it", "arithmetic", "Quanto fa 1000 diviso per 8?", [N(125)], "s"),
    ("cm", "en", "units", "How many centimetres are in 2.5 metres?", [N(250)], "f"),
    ("minutes", "de", "units", "Wie viele Minuten sind 3,5 Stunden?", [N(210)], "f"),
    ("aare", "en", "extraction", "Text: 'The Aare flows through Bern and joins the Rhine near Koblenz.' Question: Which city does the Aare flow through? Answer with one word.", [RX(r"\bBern\b")], "s"),
    ("albula", "de", "extraction", "Text: «Die Rhätische Bahn betreibt die Albulalinie zwischen Thusis und St. Moritz.» Frage: Zwischen welchen beiden Orten verkehrt die Albulalinie?", [ALL("Thusis", "St. Moritz")], "f"),
    ("marie", "fr", "extraction", "Texte : « Marie habite à Lausanne et travaille à Genève. » Question : Où travaille Marie ?", [RX(r"Gen[eè]ve")], "f"),
    ("pears", "it", "extraction", "Testo: «Luca ha comprato tre mele e due pere.» Domanda: Quante pere ha comprato Luca? Rispondi solo con il numero.", [N(2)], "f"),
    ("dog", "en", "translation", "Translate the English word 'dog' into German. Answer with one word.", [RX(r"\bHund\b")], "s"),
    ("brot", "de", "translation", "Übersetze das deutsche Wort 'Brot' ins Französische. Antworte mit einem Wort.", [RX(r"\bpain\b")], "f"),
    ("maison", "fr", "translation", "Traduis le mot français 'maison' en italien. Réponds par un seul mot.", [RX(r"\bcasa\b")], "f"),
    ("acqua", "it", "translation", "Traduci in inglese la parola italiana 'acqua'. Rispondi con una sola parola.", [RX(r"\bwater\b")], "f"),
    ("capital", "en", "swiss_knowledge", "What is the capital of Switzerland? Answer with one word.", [RX(r"\bBern[ea]?\b")], "s"),
    ("cantons", "de", "swiss_knowledge", "Wie viele Kantone hat die Schweiz? Antworte nur mit der Zahl.", [N(26)], "f"),
    ("biggest_city", "fr", "swiss_knowledge", "Quelle est la plus grande ville de Suisse par sa population ? Réponds par un seul mot.", [RX(r"Z(u|ü)rich")], "f"),
    ("language", "it", "swiss_knowledge", "Qual è la lingua più parlata in Svizzera? Rispondi con una sola parola.", [RX(r"tedesc|german|deutsch")], "f"),
    ("json", "en", "format", "Return a JSON object with the keys \"name\" and \"age\" for a person called Anna who is 30. Output only the JSON.", [ALL('"name"', '"age"', "Anna", "30"), RX(r"\{.*\}")], "s"),
    ("three_colours", "de", "format", "Nenne genau drei Farben, getrennt durch Kommas, ohne weiteren Text.", [RX(r"^\s*[^,\n]+,[^,\n]+,[^,\n]+\s*$")], "f"),
    ("seven", "fr", "format", "Écris le nombre 7 en toutes lettres, sans autre texte.", [RX(r"^\s*sept\W*$")], "f"),
    ("eu", "it", "format", "Rispondi solo con «sì» o «no»: la Svizzera è un paese dell'Unione europea?", [RX(r"^\W*no\W*$")], "s"),
    ("opposite", "en", "language", "Complete the sentence with one word: 'The opposite of hot is ___.'", [RX(r"\bcold\b")], "f"),
    ("spider", "de", "knowledge", "Wie viele Beine hat eine Spinne? Antworte nur mit der Zahl.", [N(8)], "s"),
    ("tuesday", "fr", "knowledge", "Quel jour vient après mardi ? Réponds par un seul mot.", [RX(r"mercredi")], "f"),
    ("week", "it", "knowledge", "Quanti giorni ha una settimana? Rispondi solo con il numero.", [N(7)], "f"),
    ("sort", "en", "reasoning", "Sort these numbers from smallest to largest, separated by commas: 9, 2, 7, 4.", [RX(r"2\s*,\s*4\s*,\s*7\s*,\s*9")], "s"),
    ("plural", "de", "language", "Wie lautet der Plural von 'Haus'? Antworte mit einem Wort.", [RX(r"\bHäuser\b")], "f"),
    ("prime", "en", "reasoning", "Is 91 a prime number? Answer yes or no.", [RX(r"^\W*no\b")], "f"),
    ("nine_nine", "fr", "arithmetic", "Combien font 9 fois 9 ?", [N(81)], "s"),
    ("contrary", "it", "language", "Qual è il contrario di «grande»? Rispondi con una sola parola.", [RX(r"piccol")], "f"),
    ("fractions", "en", "reasoning", "Which is larger: 3/4 or 2/3? Answer with the fraction only.", [RX(r"3\s*/\s*4")], "f"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, flag, split in (("sanity", "s", "regression_sanity"), ("final", "f", "regression_final")):
        tasks = [{"id": f"reg_{i}", "category": cap, "prompt": q, "max_steps": 3,
                  "meta": {"language": lang, "split": split, "capability": cap}, "checks": checks}
                 for i, lang, cap, q, checks, f in ITEMS if f == flag]
        header = ("# GENERATO da scripts/build_regression_tasks.py (set di regressione general-v0.1, W13): non modificare a mano.\n"
                  "# Item proposti da Claude, risposte verificabili, controlli deterministici sul testo (nessun giudice AI). Da confermare dalla squadra.\n")
        (OUT / f"{name}.yaml").write_text(header + yaml.safe_dump(tasks, allow_unicode=True, sort_keys=False, width=100000), encoding="utf-8")
        print(f"{name}: {len(tasks)} item")


if __name__ == "__main__":
    main()
