"""Ambiente Text-to-SQL: database DuckDB locale in **sola lettura**, tool `run_sql` e schema nel prompt.

Il modello non può modificare nulla né uscire dalla memoria/file del task:
- il database viene costruito dalle istruzioni `setup.sql_init` con una connessione normale, poi **richiuso e riaperto in sola lettura**
  (è il motore a rifiutare INSERT/CREATE/DROP, non un filtro sul testo);
- accesso a file e rete disabilitato (`enable_external_access=false`), estensioni non installabili/caricabili, configurazione bloccata;
- una sola istruzione per chiamata, e solo di tipo SELECT (include WITH, FROM, DESCRIBE, SHOW);
- timeout (interruzione della query), memoria limitata, righe mostrate al modello limitate, risultato memorizzato limitato.

`duckdb` è un extra opzionale (`pip install .[sql]`): il pacchetto principale si importa anche senza.

Quale query conta per l'execution accuracy: l'**ultima `run_sql` riuscita** della traiettoria (`last_result`). Le regole del confronto
stanno in `sql_eval.py`.
"""
from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from .sql_eval import SqlResult
from .tools import ToolBox, ToolError

SQL_SYSTEM = (
    "You are a data analyst with access to a read-only SQL database (DuckDB dialect). "
    "Answer the user's question by running SQL with the run_sql tool. Read the schema you are given, "
    "and use only the tables and columns it lists. If a query fails, read the error, fix the query and retry. "
    "Do not invent data: base the answer on query results. When you are done, give the final answer in the same language "
    "as the question, and state the values you found. Your last successful run_sql query should be the one that answers the question."
)

DEFAULT_LIMITS: dict[str, Any] = {
    "timeout_s": 10.0,        # una query oltre il limite viene interrotta
    "memory_limit": "512MB",
    "max_rows_shown": 50,     # righe mostrate al modello
    "max_rows_stored": 100_000,  # oltre questo il risultato non viene memorizzato e la query dà errore
    "max_cell_chars": 200,
    "sample_rows": 3,         # righe d'esempio per tabella nel testo dello schema
}


def data_directory() -> str:
    """Cartella dei dati: variabile `AGENTBENCH_DATA_DIR` oppure `<radice del progetto>/data` (checkout o installazione editabile)."""
    return os.environ.get("AGENTBENCH_DATA_DIR") or str(Path(__file__).resolve().parents[2] / "data")


def _require_duckdb():
    try:
        import duckdb
    except ImportError as e:  # pragma: no cover - dipende dall'ambiente
        raise RuntimeError("serve DuckDB: installa l'extra sql (`uv sync --extra sql` oppure `pip install .[sql]`)") from e
    return duckdb


def _fmt(v: Any, max_chars: int) -> str:
    s = "NULL" if v is None else str(v)
    s = s.replace("\n", " ")
    return s if len(s) <= max_chars else s[: max_chars - 1] + "…"


class SqlBox(ToolBox):
    """ToolBox con un database DuckDB in sola lettura. Un'istanza per ogni esecuzione di un task (stato fresco)."""

    def __init__(self, setup: dict[str, Any] | None = None) -> None:
        super().__init__(setup)
        setup = setup or {}
        init = setup.get("sql_init")
        if not init or not isinstance(init, list):
            raise ValueError("un task con run_sql richiede `setup.sql_init`: lista di istruzioni SQL che costruiscono il database")
        unknown = set(setup.get("limits", {})) - set(DEFAULT_LIMITS)
        if unknown:
            raise ValueError(f"limiti sconosciuti {sorted(unknown)} (disponibili: {', '.join(DEFAULT_LIMITS)})")
        self.limits = {**DEFAULT_LIMITS, **setup.get("limits", {})}
        self._duckdb = _require_duckdb()
        self._tmp = tempfile.TemporaryDirectory(prefix="agentbench-sql-")
        path = str(Path(self._tmp.name) / "db.duckdb")
        con = self._duckdb.connect(path)
        data_dir = data_directory()
        try:
            for stmt in init:
                con.execute(stmt.replace("{DATA}", data_dir))  # i task usano {DATA}/… per i file CSV del progetto
        finally:
            con.close()
        self.con = self._duckdb.connect(path, read_only=True, config={
            "enable_external_access": False,
            "memory_limit": self.limits["memory_limit"],
            "threads": 1,
            "autoinstall_known_extensions": False,
            "autoload_known_extensions": False,
        })
        self.con.execute("SET lock_configuration=true")
        self.last_result: SqlResult | None = None
        self.last_sql: str | None = None

    # ------------------------------------------------------------------ esecuzione

    def _run(self, query: str, timeout_s: float) -> SqlResult:
        """Esegue una query SELECT con timeout; solleva ToolError con un messaggio utile al modello."""
        duckdb = self._duckdb
        try:
            stmts = self.con.extract_statements(query)
        except duckdb.Error as e:
            raise ToolError(str(e)) from None
        if len(stmts) != 1:
            raise ToolError("send exactly one SQL statement per call")
        if stmts[0].type != duckdb.StatementType.SELECT:
            raise ToolError(f"only read-only SELECT queries are allowed (got {stmts[0].type.name})")
        timer = threading.Timer(timeout_s, self.con.interrupt)
        timer.start()
        try:
            cur = self.con.execute(query)
            columns = [d[0] for d in cur.description]
            cap = int(self.limits["max_rows_stored"])
            rows = cur.fetchmany(cap + 1)
        except duckdb.InterruptException:
            raise ToolError(f"query interrupted: it took longer than {timeout_s:g} s") from None
        except duckdb.Error as e:
            raise ToolError(str(e)) from None
        finally:
            timer.cancel()
        if len(rows) > cap:
            raise ToolError(f"the result has more than {cap} rows: add a filter or an aggregation")
        return SqlResult(columns, [tuple(r) for r in rows])

    def _t_run_sql(self, query: str) -> str:
        res = self._run(query, float(self.limits["timeout_s"]))
        self.last_result, self.last_sql = res, query
        shown = int(self.limits["max_rows_shown"])
        cell = int(self.limits["max_cell_chars"])
        lines = [" | ".join(res.columns)]
        lines += [" | ".join(_fmt(v, cell) for v in row) for row in res.rows[:shown]]
        n = len(res.rows)
        lines.append(f"({n} row{'s' if n != 1 else ''})" if n <= shown else f"(showing the first {shown} of {n} rows)")
        return "\n".join(lines)

    def gold_result(self, sql: str) -> SqlResult:
        """Esegue la query gold sullo stesso database (stessi limiti, timeout triplo)."""
        return self._run(sql, 3 * float(self.limits["timeout_s"]))

    # ------------------------------------------------------------------ schema nel prompt

    def schema_text(self) -> str:
        """Testo dello schema aggiunto al messaggio dell'utente: uguale per tutte le condizioni (serializzazione congelata).

        Per ogni tabella: colonne con tipo e le prime `sample_rows` righe. Le tabelle sono in ordine alfabetico."""
        tables = [r[0] for r in self.con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name").fetchall()]
        n = int(self.limits["sample_rows"])
        cell = int(self.limits["max_cell_chars"])
        out = ["Database schema (DuckDB):"]
        for t in tables:
            cols = self.con.execute(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='main' AND table_name=? "
                "ORDER BY ordinal_position", [t]).fetchall()
            out.append(f"\nTable {t}(" + ", ".join(f"{c} {ty}" for c, ty in cols) + ")")
            if n > 0:
                rows = self.con.execute(f'SELECT * FROM "{t}" LIMIT {n}').fetchall()
                if rows:
                    out.append("Example rows:")
                    out += ["  " + " | ".join(_fmt(v, cell) for v in r) for r in rows]
        return "\n".join(out)

    def close(self) -> None:
        try:
            self.con.close()
        finally:
            self._tmp.cleanup()


def make_box(setup: dict[str, Any] | None, tools: list[str]) -> ToolBox:
    """Il ToolBox giusto per un task: con `run_sql` serve il database, altrimenti i tool finti del vecchio progetto."""
    return SqlBox(setup) if "run_sql" in tools else ToolBox(setup)
