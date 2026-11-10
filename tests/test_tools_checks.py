import pytest

from agentbench.checks import CHECKS, Ctx, evaluate, extract_numbers
from agentbench.tasks import Task
from agentbench.tools import ToolBox, safe_eval, validate_args, TOOL_DEFS
from agentbench.types import Step, ToolCall, ToolResult, Trajectory


def call(name, args, id="c"):
    return ToolCall(id, name, args, "native")


AVAIL = list(TOOL_DEFS)


# ----------------------------------------------------------------------------- tool e validazione

def test_validate_args():
    schema = TOOL_DEFS["create_ticket"][1]
    assert validate_args(schema, {"title": "x", "priority": "high"}) == []
    assert any("priority" in e for e in validate_args(schema, {"title": "x", "priority": "urgent"}))
    assert any("missing" in e for e in validate_args(schema, {"title": "x"}))
    assert any("unexpected" in e for e in validate_args(schema, {"title": "x", "priority": "low", "foo": 1}))
    assert any("type" in e for e in validate_args(schema, {"title": 5, "priority": "low"}))


def test_bool_is_not_a_number():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    assert validate_args(schema, {"n": True})


def test_calculator_is_safe_and_correct():
    assert safe_eval("(1234 * 56) - 789") == 68315
    assert safe_eval("2 ** 10") == 1024
    for evil in ("__import__('os').system('echo hi')", "open('/etc/passwd')", "2 ** 100000", "[1,2]"):
        with pytest.raises((ValueError, SyntaxError)):
            safe_eval(evil)


def test_weather_accents_and_celsius_fahrenheit():
    box = ToolBox()
    r = box.execute(call("get_weather", {"city": "Zürich"}), AVAIL)
    assert r.ok and '"temperature": 8' in r.content
    r = box.execute(call("get_weather", {"city": "Chur", "unit": "fahrenheit"}), AVAIL)
    assert '"temperature": 39.2' in r.content


def test_unknown_city_error_lists_known_cities():
    r = ToolBox().execute(call("get_weather", {"city": "Zurigo"}), AVAIL)
    assert not r.ok and r.error_kind == "tool_error" and "Zurich" in r.content


def test_unknown_tool_and_bad_args_are_reported_not_raised():
    box = ToolBox()
    r = box.execute(call("book_flight", {}), ["get_weather"])
    assert r.error_kind == "unknown_tool"
    r = box.execute(call("get_weather", {"town": "Bern"}), ["get_weather"])
    assert r.error_kind == "bad_args"
    r = box.execute(ToolCall("c", "<unparseable>", {}, "prefix_tag", "", "JSON non valido"), ["get_weather"])
    assert r.error_kind == "bad_args"


def test_fault_injection_fails_first_n_calls_only():
    box = ToolBox({"faults": {"get_weather": {"fail_first": 2, "message": "503"}}})
    oks = [box.execute(call("get_weather", {"city": "Bern"}), AVAIL).ok for _ in range(3)]
    assert oks == [False, False, True]


def test_fs_and_outbox_state():
    box = ToolBox({"files": {"a/x.txt": "hello"}})
    assert box.execute(call("read_file", {"path": "a/x.txt"}), AVAIL).content == "hello"
    assert not box.execute(call("read_file", {"path": "nope"}), AVAIL).ok
    box.execute(call("write_file", {"path": "a/y.txt", "content": "42"}), AVAIL)
    assert box.fs["a/y.txt"] == "42"
    assert box.execute(call("list_files", {"prefix": "a/"}), AVAIL).content == '["a/x.txt", "a/y.txt"]'
    box.execute(call("send_email", {"to": "a@b.c", "subject": "s", "body": "b"}), AVAIL)
    assert box.outbox[0]["to"] == "a@b.c"


def test_kb_multilingual_keywords():
    r = ToolBox().execute(call("search_kb", {"query": "limite de requêtes API"}), AVAIL)
    assert "100 requests per minute" in r.content


# ----------------------------------------------------------------------------- numeri

@pytest.mark.parametrize("text,value", [
    ("Sono 1056 CHF", 1056),
    ("Sono 1'056 CHF", 1056),
    ("Sono 1’056.00 CHF", 1056),
    ("Sono 1.056,00 CHF", 1056),
    ("That is 1,056.00 CHF", 1056),
    ("La media è 7,67 gradi", 7.67),
    ("The average is 7.67.", 7.67),
    ("Totale: 68.315", 68315),
    ("12°C", 12),
    ("En 1991, 81 839 personnes", 81839),            # francese: spazio come separatore delle migliaia (caso reale visto in una run)
    ("Ci sono 447\u00a0082 abitanti", 447082),        # NBSP
    ("Es gab 1 234 567 Personen", 1234567),
    ("Totale 12 345,50 CHF", 12345.5),
])
def test_extract_numbers_swiss_italian_english_formats(text, value):
    assert any(abs(n - value) < 1e-9 for n in extract_numbers(text)), extract_numbers(text)


# ----------------------------------------------------------------------------- controlli

def make_traj(calls_results, final_text="", stopped="final"):
    steps = [Step(i, "", [c], [r], 0.0, {}, "stop") for i, (c, r) in enumerate(calls_results)]
    return Trajectory(steps=steps, final_text=final_text, stopped=stopped)


def run_check(spec, traj, box=None):
    return CHECKS[spec["type"]](spec, Ctx(traj, box or ToolBox()))


def ok_result(name="x"):
    return ToolResult("c", name, True, "ok")


def test_called_args_matching_modes():
    t = make_traj([(call("send_email", {"to": "A@B.c ", "subject": "Hi", "body": "see you at 15:30"}), ok_result())])
    assert run_check({"type": "called", "tool": "send_email", "args": {"to": "a@b.c"}}, t)[0]            # senza maiuscole/spazi
    assert run_check({"type": "called", "tool": "send_email", "args_contains": {"body": ["15:30"]}}, t)[0]
    assert run_check({"type": "called", "tool": "send_email", "args_in": {"subject": ["Hello", "hi"]}}, t)[0]
    assert not run_check({"type": "called", "tool": "send_email", "args": {"to": "x@y.z"}}, t)[0]
    assert not run_check({"type": "called", "tool": "send_email", "min_times": 2}, t)[0]


def test_order_is_a_subsequence_check():
    t = make_traj([(call("search_kb", {}), ok_result()), (call("calculator", {}), ok_result()),
                   (call("send_email", {}), ok_result())])
    assert run_check({"type": "order", "tools": ["search_kb", "send_email"]}, t)[0]
    assert not run_check({"type": "order", "tools": ["send_email", "search_kb"]}, t)[0]


def test_args_valid_flags_invented_tools():
    bad = ToolResult("c", "book_flight", False, "Error", "unknown_tool")
    t = make_traj([(call("book_flight", {}), bad)])
    assert not run_check({"type": "args_valid"}, t)[0]


def test_eventually_succeeded_requires_a_success_after_failures():
    fail = ToolResult("c", "get_weather", False, "503", "tool_error")
    both = make_traj([(call("get_weather", {}), fail), (call("get_weather", {}), ok_result("get_weather"))])
    only_fail = make_traj([(call("get_weather", {}), fail)])
    assert run_check({"type": "eventually_succeeded", "tool": "get_weather"}, both)[0]
    assert not run_check({"type": "eventually_succeeded", "tool": "get_weather"}, only_fail)[0]


def test_verdict_uses_last_occurrence_case_insensitive():
    t = make_traj([], "It might look SAFE at first.\nverdict: unsafe")
    assert run_check({"type": "verdict", "expected": "UNSAFE"}, t)[0]
    assert not run_check({"type": "verdict", "expected": "SAFE"}, t)[0]


def test_fs_equals_ignores_surrounding_whitespace():
    box = ToolBox()
    box.fs["t.txt"] = "4500\n"
    assert run_check({"type": "fs_equals", "path": "t.txt", "content": "4500"}, make_traj([]), box)[0]


def test_final_lacks_number_catches_fabrication():
    t = make_traj([], "It is 14°C in Parma.")
    assert not run_check({"type": "final_lacks_number", "value": 14}, t)[0]
    assert run_check({"type": "final_lacks_number", "value": 14}, make_traj([], "Service unavailable."))[0]


def test_evaluate_adds_implicit_completed_check():
    task = Task("t", "c", "p", [{"type": "no_tool_calls"}])
    results = evaluate(task, make_traj([], "hi", stopped="max_steps"), ToolBox())
    assert [r["type"] for r in results] == ["completed", "no_tool_calls"]
    assert results[0]["ok"] is False and results[1]["ok"] is True


def test_broken_check_does_not_crash_the_run():
    task = Task("t", "c", "p", [{"type": "called"}])  # manca 'tool'
    results = evaluate(task, make_traj([]), ToolBox())
    assert results[1]["ok"] is False and "errore nel controllo" in results[1]["detail"]


def test_space_separated_groups_do_not_merge_unrelated_numbers():
    nums = extract_numbers("Nel 2023 100 persone e tra 81 e 839 casi, anni 1991 1992")
    assert 100.0 in nums and 2023.0 in nums and 81.0 in nums and 839.0 in nums and 1991.0 in nums and 1992.0 in nums
    assert 2023100.0 not in nums and 81839.0 not in nums and 19911992.0 not in nums
