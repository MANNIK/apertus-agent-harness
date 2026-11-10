"""Ambiente SQL (sql_env): sola lettura, nessun accesso a file/rete, timeout, limiti e schema nel prompt. Serve l'extra `sql` (DuckDB)."""
from pathlib import Path

import pytest

pytest.importorskip("duckdb")

from agentbench.sql_env import SQL_SYSTEM, SqlBox, make_box  # noqa: E402
from agentbench.tools import ToolBox  # noqa: E402
from agentbench.types import ToolCall  # noqa: E402

SETUP = {"sql_init": ["CREATE TABLE t(a INTEGER, b VARCHAR)", "INSERT INTO t VALUES (1,'x'),(2,NULL),(3,'z')"]}


def call(box, query):
    return box.execute(ToolCall("c1", "run_sql", {"query": query}, "native"), ["run_sql"])


@pytest.fixture
def box():
    b = SqlBox(SETUP)
    yield b
    b.close()


def test_select_returns_a_readable_table_and_records_the_result(box):
    r = call(box, "SELECT a, b FROM t ORDER BY a")
    assert r.ok and r.content.splitlines() == ["a | b", "1 | x", "2 | NULL", "3 | z", "(3 rows)"]
    assert box.last_result.rows == [(1, "x"), (2, None), (3, "z")] and box.last_result.columns == ["a", "b"]
    assert "(1 row)" in call(box, "SELECT count(*) FROM t WHERE a = 1 GROUP BY a").content.splitlines()[-1]


@pytest.mark.parametrize("query", [
    "INSERT INTO t VALUES (9, 'q')",
    "UPDATE t SET a = 5",
    "DELETE FROM t",
    "CREATE TABLE u(x INT)",
    "DROP TABLE t",
    "COPY t TO '/tmp/agentbench_should_not_exist.csv'",
    "ATTACH '/tmp/agentbench_should_not_exist.duckdb'",
    "SELECT * FROM read_csv('/etc/hosts')",
    "SELECT * FROM 'https://example.com/data.csv'",
    "SET memory_limit = '8GB'",
    "PRAGMA table_info('t')",
    "INSTALL httpfs",
    "SELECT 1; SELECT 2",
    "this is not sql",
])
def test_anything_but_a_single_select_is_refused_and_nothing_changes(box, query):
    r = call(box, query)
    assert not r.ok and r.error_kind == "tool_error" and r.content.startswith("Error:")
    assert call(box, "SELECT count(*) FROM t").content.splitlines()[1] == "3"
    assert not Path("/tmp/agentbench_should_not_exist.csv").exists()
    assert not Path("/tmp/agentbench_should_not_exist.duckdb").exists()


def test_with_describe_show_and_from_first_are_allowed(box):
    for q in ("WITH x AS (SELECT 1 AS n) SELECT * FROM x", "DESCRIBE t", "SHOW TABLES", "FROM t"):
        assert call(box, q).ok, q


def test_failed_query_does_not_replace_the_last_successful_result(box):
    call(box, "SELECT a FROM t ORDER BY a")
    first = box.last_result
    assert not call(box, "SELECT nonexistent FROM t").ok
    assert box.last_result is first and box.last_sql == "SELECT a FROM t ORDER BY a"


def test_sql_error_message_is_returned_to_the_model(box):
    r = call(box, "SELECT nonexistent FROM t")
    assert not r.ok and "nonexistent" in r.content


def test_timeout_interrupts_the_query_and_the_box_stays_usable():
    b = SqlBox({**SETUP, "limits": {"timeout_s": 0.3}})
    try:
        r = call(b, "SELECT count(*) FROM range(100000000) a, range(100000000) b")
        assert not r.ok and "interrupted" in r.content
        assert call(b, "SELECT count(*) FROM t").ok
    finally:
        b.close()


def test_rows_shown_are_limited_but_the_full_result_is_kept_for_scoring():
    b = SqlBox({"sql_init": ["CREATE TABLE n AS SELECT range AS i FROM range(200)"], "limits": {"max_rows_shown": 5}})
    try:
        r = call(b, "SELECT i FROM n")
        assert r.ok and r.content.splitlines()[-1] == "(showing the first 5 of 200 rows)" and len(r.content.splitlines()) == 7
        assert len(b.last_result.rows) == 200
    finally:
        b.close()


def test_too_large_result_is_an_error_and_is_not_stored():
    b = SqlBox({"sql_init": ["CREATE TABLE n AS SELECT range AS i FROM range(200)"], "limits": {"max_rows_stored": 100}})
    try:
        call(b, "SELECT 1")
        r = call(b, "SELECT i FROM n")
        assert not r.ok and "more than 100 rows" in r.content
        assert b.last_result.rows == [(1,)]
    finally:
        b.close()


def test_schema_text_lists_tables_types_and_example_rows_deterministically():
    texts = []
    for _ in range(2):
        b = SqlBox(SETUP)
        texts.append(b.schema_text())
        b.close()
    assert texts[0] == texts[1]
    assert "Table t(a INTEGER, b VARCHAR)" in texts[0]
    assert "  1 | x" in texts[0] and "  2 | NULL" in texts[0]


def test_setup_is_validated():
    with pytest.raises(ValueError, match="sql_init"):
        SqlBox({})
    with pytest.raises(ValueError, match="limiti sconosciuti"):
        SqlBox({**SETUP, "limits": {"nope": 1}})


def test_missing_or_invalid_arguments_are_reported_like_any_tool(box):
    r = box.execute(ToolCall("c1", "run_sql", {}, "native"), ["run_sql"])
    assert not r.ok and r.error_kind == "bad_args"


def test_make_box_chooses_the_right_box_and_close_removes_the_temp_files():
    assert type(make_box({}, ["get_weather"])) is ToolBox
    b = make_box(SETUP, ["run_sql"])
    assert isinstance(b, SqlBox)
    tmp = Path(b._tmp.name)
    assert tmp.exists()
    b.close()
    assert not tmp.exists()


def test_sql_system_prompt_mentions_the_tool():
    assert "run_sql" in SQL_SYSTEM
