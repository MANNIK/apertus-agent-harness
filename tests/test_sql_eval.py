"""Regole del confronto per esecuzione (sql_eval): dichiarate una volta, valide per tutte le condizioni. Senza DuckDB né modello."""
import datetime as dt
from decimal import Decimal

from agentbench.sql_eval import SqlResult, compare_results, values_equal


def R(rows, cols=("a",)):
    return SqlResult(list(cols), [tuple(r) for r in rows])


def ok(pred, gold, order=False):
    return compare_results(pred, gold, order_matters=order).ok


def test_same_rows_in_other_order_pass_unless_order_matters():
    a, b = R([(1,), (2,), (3,)]), R([(3,), (1,), (2,)])
    assert ok(a, b)
    assert not ok(a, b, order=True)
    assert ok(a, R([(1,), (2,), (3,)]), order=True)


def test_extra_or_missing_rows_fail_and_duplicates_count():
    gold = R([(1,), (2,)])
    assert not ok(R([(1,), (2,), (3,)]), gold)
    assert not ok(R([(1,)]), gold)
    assert not ok(R([(1,), (1,), (2,)]), gold)  # un duplicato in più non è ammesso
    assert not ok(R([(1,), (2,), (2,)]), R([(1,), (1,), (2,)]))  # stessi insiemi ma molteplicità diverse


def test_extra_missing_or_reordered_columns_fail_but_names_are_ignored():
    gold = R([(1, "x")], cols=("n", "s"))
    assert not ok(R([(1, "x", 5)], cols=("n", "s", "extra")), gold)
    assert not ok(R([(1,)], cols=("n",)), gold)
    assert not ok(R([("x", 1)], cols=("s", "n")), gold)  # ordine delle colonne: per posizione
    assert ok(R([(1, "x")], cols=("totally", "different")), gold)  # i nomi non contano


def test_null_handling():
    assert ok(R([(None,)]), R([(None,)]))
    assert not ok(R([(None,)]), R([(0,)]))
    assert not ok(R([(None,)]), R([("",)]))
    assert not ok(R([(0,)]), R([(None,)]))
    assert not values_equal(None, False)


def test_numbers_int_float_decimal_and_tolerance():
    assert values_equal(3, 3.0)
    assert values_equal(Decimal("2.50"), 2.5)
    assert values_equal(0.1 + 0.2, 0.3)  # errore di virgola mobile
    assert values_equal(1_000_000.0000001, 1_000_000.0)
    assert not values_equal(3.14159, 3.14)  # niente arrotondamento implicito a favore del modello
    assert not values_equal(10, 11)
    assert values_equal(2**60, 2**60) and not values_equal(2**60, 2**60 + 1)  # interi grandi esatti
    assert values_equal(float("nan"), float("nan"))


def test_types_booleans_strings_and_dates():
    assert not values_equal(True, 1) and not values_equal(1, True)
    assert values_equal(True, True) and not values_equal(True, False)
    assert not values_equal("Zürich", "zürich")  # maiuscole contano
    assert not values_equal("Zürich", "Zürich ")  # gli spazi contano
    assert not values_equal(dt.date(2024, 3, 5), "2024-03-05")  # una data convertita in testo non equivale
    assert values_equal(dt.date(2024, 3, 5), dt.date(2024, 3, 5))
    assert not values_equal("1", 1)


def test_mixed_types_in_unordered_rows_do_not_crash():
    gold = R([(1,), ("a",), (None,), (True,)])
    pred = R([(None,), (True,), ("a",), (1,)])
    assert ok(pred, gold)


def test_empty_results():
    assert ok(R([], cols=("a", "b")), R([], cols=("x", "y")))
    assert not ok(R([], cols=("a",)), R([(1,)]))
    assert not ok(R([], cols=("a",)), R([], cols=("a", "b")))  # colonne diverse anche a righe vuote


def test_reason_names_the_first_difference():
    m = compare_results(R([(1, "x")], cols=("n", "s")), R([(1, "y")], cols=("n", "s")))
    assert not m.ok and "riga 1, colonna 2" in m.reason
    assert "colonne" in compare_results(R([(1,)]), R([(1, 2)], cols=("a", "b"))).reason
