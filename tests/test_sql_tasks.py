"""Task Text-to-SQL sintetici (tasks/demo_sales.yaml): ogni task è risolvibile con la sua query gold, le query sbagliate falliscono
e l'execution accuracy non dipende dal testo della query. Prova anche il ciclo completo contro un server finto."""
import json
from pathlib import Path

import pytest

pytest.importorskip("duckdb")

from agentbench.bench import run_suite  # noqa: E402
from agentbench.checks import CHECKS, Ctx  # noqa: E402
from agentbench.cli import main  # noqa: E402
from agentbench.client import ChatClient  # noqa: E402
from agentbench.sql_env import make_box  # noqa: E402
from agentbench.tasks import load_tasks  # noqa: E402
from agentbench.types import ToolCall, Trajectory  # noqa: E402
from mock_server import MockServer, final, native  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TASKS = {t.id: t for t in load_tasks(ROOT / "tasks")}


def gold_spec(task):
    return next(c for c in task.checks if c["type"] == "sql_result_match")


def judge_query(task, query):
    """Esegue `query` come farebbe il modello e applica il controllo di execution accuracy del task."""
    box = make_box(task.setup, task.tools)
    try:
        res = box.execute(ToolCall("c1", "run_sql", {"query": query}, "native"), task.tools)
        assert res.ok, res.content
        return CHECKS["sql_result_match"](gold_spec(task), Ctx(Trajectory(), box))
    finally:
        box.close()


def test_demo_tasks_are_sql_tasks_with_labels():
    assert len(TASKS) == 8
    for t in TASKS.values():
        assert t.tools == ["run_sql"] and t.id.startswith("demo_")
        assert t.meta["language"] in {"de", "fr", "it", "en"} and t.meta["schema_id"] == "demo_sales" and t.meta["split"] == "demo"
        assert gold_spec(t)["gold"].lstrip().upper().startswith("SELECT")


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_every_task_is_solvable_with_its_gold_query(tid):
    ok, detail = judge_query(TASKS[tid], gold_spec(TASKS[tid])["gold"])
    assert ok, detail


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_wrong_results_fail(tid):
    t = TASKS[tid]
    gold = gold_spec(t)["gold"].strip().rstrip(";")
    wrong = {
        "extra column": f"SELECT *, 1 AS extra FROM ({gold}) AS g",
        "no rows": f"SELECT * FROM ({gold}) AS g LIMIT 0",
        "duplicated rows": f"SELECT * FROM ({gold}) AS a UNION ALL SELECT * FROM ({gold}) AS b",
    }
    for name, q in wrong.items():
        ok, detail = judge_query(t, q)
        assert not ok, f"{tid}: la variante '{name}' non doveva passare ({detail})"


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_execution_accuracy_does_not_depend_on_the_query_text(tid):
    gold = gold_spec(TASKS[tid])["gold"].strip().rstrip(";")
    ok, detail = judge_query(TASKS[tid], f"/* un commento */\n   {gold}\n  ;")
    assert ok, detail


def test_different_but_equivalent_queries_pass_and_column_names_do_not_matter():
    assert judge_query(TASKS["demo_count_en"], "SELECT COUNT(id) AS n FROM verkauf")[0]
    assert judge_query(TASKS["demo_ti_total_fr"], "SELECT SUM(v.betrag_chf) AS totale FROM verkauf v WHERE v.kanton IN ('TI')")[0]
    assert judge_query(TASKS["demo_distinct_products_en"], "SELECT COUNT(*) FROM (SELECT DISTINCT produkt FROM verkauf)")[0]


def test_traps_are_really_traps():
    assert not judge_query(TASKS["demo_avg_amount_en"], "SELECT AVG(COALESCE(betrag_chf, 0)) FROM verkauf")[0]  # NULL contato come 0
    assert not judge_query(TASKS["demo_march_sales_en"], "SELECT COUNT(*) FROM verkauf WHERE datum LIKE '03.%'")[0]  # formato gg.mm.aaaa letto male
    assert not judge_query(TASKS["demo_ge_sales_de"], "SELECT id, betrag_chf FROM verkauf WHERE kanton = 'ZH'")[0]


def test_order_matters_only_when_the_task_says_so():
    big = TASKS["demo_big_cantons_it"]
    base = "SELECT k.name FROM kanton k JOIN verkauf v ON v.kanton = k.kuerzel GROUP BY k.name HAVING COUNT(*) >= 3"
    assert judge_query(big, base + " ORDER BY k.name")[0]
    assert not judge_query(big, base + " ORDER BY k.name DESC")[0]  # ordine richiesto dalla domanda
    # senza order_matters l'ordine non conta
    assert judge_query(TASKS["demo_ge_sales_de"], "SELECT id, betrag_chf FROM verkauf WHERE kanton = 'GE' ORDER BY id DESC")[0]


def test_no_successful_query_means_failure():
    t = TASKS["demo_count_en"]
    box = make_box(t.setup, t.tools)
    try:
        ok, detail = CHECKS["sql_result_match"](gold_spec(t), Ctx(Trajectory(), box))
    finally:
        box.close()
    assert not ok and "nessuna query" in detail


# ----------------------------------------------------------------------------- ciclo completo contro un server finto

def policy_for(scripts):
    """Riconosce il task dalla riga `Question: …` del messaggio utente (lo schema lo precede)."""
    def policy(messages, tools, body):
        assert [t["function"]["name"] for t in tools] == ["run_sql"]
        user = next(m["content"] for m in messages if m["role"] == "user")
        for question, script in scripts.items():
            if f"Question: {question}" in user:
                turn = sum(1 for m in messages if m["role"] == "assistant")
                return script[turn] if turn < len(script) else final("done")
        return final("(nessun copione)")
    return policy


def run(policy, ids, out):
    with MockServer(policy) as srv:
        client = ChatClient(srv.url, "mock", retries=0, timeout=10)
        recs = run_suite(client, [TASKS[i] for i in ids], 1, out)
    return {r["task_id"]: r for r in recs}, srv


def test_full_loop_good_model_passes_and_bad_models_fail(tmp_path):
    q = {k: TASKS[k].prompt for k in ("demo_count_en", "demo_top_product_de", "demo_ge_sales_de")}
    good = {
        q["demo_count_en"]: [native("run_sql", {"query": "SELECT COUNT(*) FROM verkauf"}), final("There are 10 sales in total.")],
        q["demo_top_product_de"]: [native("run_sql", {"query": "SELECT produkt, SUM(betrag_chf) s FROM verkauf GROUP BY produkt ORDER BY s DESC LIMIT 1"}),
                                   native("run_sql", {"query": "SELECT produkt FROM verkauf GROUP BY produkt ORDER BY SUM(betrag_chf) DESC LIMIT 1"}),
                                   final("Die Uhr.")],
        q["demo_ge_sales_de"]: [native("run_sql", {"query": "SELECT nope FROM verkauf"}),  # errore, poi si corregge
                                native("run_sql", {"query": "SELECT id, betrag_chf FROM verkauf WHERE kanton = 'GE'"}), final("Zwei Verkäufe.")],
    }
    bad = {
        q["demo_count_en"]: [native("run_sql", {"query": "SELECT COUNT(*) FROM verkauf WHERE betrag_chf IS NOT NULL"}), final("There are 9 sales.")],
        q["demo_top_product_de"]: [final("Wahrscheinlich der Käse.")],  # non interroga il database
        q["demo_ge_sales_de"]: [native("run_sql", {"query": "DELETE FROM verkauf"}), final("Gelöscht.")],
    }
    recs, srv = run(policy_for(good), list(q), tmp_path / "good")
    assert all(r["passed"] for r in recs.values()), {k: [c for c in r["checks"] if not c["ok"]] for k, r in recs.items()}
    assert recs["demo_ge_sales_de"]["error_kinds"] == ["tool_error"]  # l'errore SQL è stato restituito al modello
    first_user = next(m["content"] for m in srv.requests[0]["messages"] if m["role"] == "user")
    assert first_user.startswith("Database schema (DuckDB):") and "Table verkauf(" in first_user and "Question: " in first_user

    recs, _ = run(policy_for(bad), list(q), tmp_path / "bad")
    assert not any(r["passed"] for r in recs.values())
    assert any("nessuna query" in c["detail"] for c in recs["demo_top_product_de"]["checks"])
    assert recs["demo_ge_sales_de"]["error_kinds"] == ["tool_error"]  # il DELETE è stato rifiutato


def test_cli_run_uses_the_sql_system_prompt_and_saves_task_labels(tmp_path, capsys):
    out = tmp_path / "out"
    q = TASKS["demo_count_en"].prompt
    script = policy_for({q: [native("run_sql", {"query": "SELECT COUNT(*) FROM verkauf"}), final("10")]})
    with MockServer(script) as srv:
        with pytest.raises(SystemExit) as e:
            main(["run", "--base-url", srv.url, "--model", "mock", "--tasks", str(ROOT / "tasks"), "--only", "demo_count_en", "--out", str(out)])
    assert e.value.code == 0
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["system_prompt"].startswith("You are a data analyst")
    rec = json.loads((out / "results.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert rec["meta"]["language"] == "en" and rec["passed"]



def test_primary_score_ignores_whether_the_model_wrote_a_final_answer(tmp_path):
    """Caso reale visto con Apertus: risultato giusto, poi la stessa query ripetuta fino a max_steps senza risposta finale."""
    t = next(x for x in load_tasks(ROOT / "tasks" / "zurich" / "dev") if x.id == "bevq_total_1")
    gold = next(c for c in t.checks if c["type"] == "sql_result_match")["gold"]
    with MockServer(policy_for({t.prompt: [native("run_sql", {"query": gold})] * 8})) as srv:
        recs = run_suite(ChatClient(srv.url, "mock", retries=0, timeout=10), [t], 1, tmp_path / "out")
    r = recs[0]
    by = {c["type"]: c for c in r["checks"]}
    assert r["stopped"] == "max_steps" and not by["completed"]["ok"] and by["completed"]["diagnostic"]
    assert by["sql_result_match"]["ok"] and r["passed"], "la query è giusta: il punteggio primario deve passare"
    assert not by["final_number"]["ok"] and by["final_number"]["diagnostic"]  # senza testo finale la risposta non c'è, ma non conta
