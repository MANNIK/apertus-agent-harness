import json

from agentbench.parser import extract_tool_calls

KNOWN = {"get_weather", "send_email"}


def test_native_tool_calls():
    msg = {"content": None, "tool_calls": [
        {"id": "x1", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "Lugano"}'}}]}
    calls, text = extract_tool_calls(msg, KNOWN)
    assert [(c.id, c.name, c.arguments, c.source) for c in calls] == [("x1", "get_weather", {"city": "Lugano"}, "native")]
    assert text == ""


def test_native_with_broken_arguments_is_flagged():
    msg = {"content": "", "tool_calls": [{"id": "x", "function": {"name": "get_weather", "arguments": "{city: Lugano"}}]}
    calls, _ = extract_tool_calls(msg, KNOWN)
    assert calls[0].parse_error and calls[0].arguments == {}


def test_apertus_prefix_tags_single_key_format():
    content = '<|tools_prefix|>[{"get_weather": {"city": "Lugano"}}]<|tools_suffix|>'
    calls, text = extract_tool_calls({"content": content}, KNOWN)
    assert len(calls) == 1 and calls[0].source == "prefix_tag"
    assert (calls[0].name, calls[0].arguments) == ("get_weather", {"city": "Lugano"})
    assert text == ""


def test_prefix_tags_name_arguments_format_and_surrounding_text():
    payload = json.dumps([{"name": "send_email", "arguments": {"to": "a@b.c", "subject": "s", "body": "b"}}])
    content = f"Sending now. <|tools_prefix|>{payload}<|tools_suffix|>"
    calls, text = extract_tool_calls({"content": content}, KNOWN)
    assert calls[0].name == "send_email" and calls[0].arguments["to"] == "a@b.c"
    assert text == "Sending now."


def test_multiple_calls_in_one_block():
    content = '<|tools_prefix|>[{"get_weather": {"city": "Bern"}}, {"get_weather": {"city": "Chur"}}]<|tools_suffix|>'
    calls, _ = extract_tool_calls({"content": content}, KNOWN)
    assert [c.arguments["city"] for c in calls] == ["Bern", "Chur"]


def test_unterminated_prefix_tag_suffix_stripped_by_server():
    calls, _ = extract_tool_calls({"content": '<|tools_prefix|>[{"get_weather": {"city": "Lugano"}}]'}, KNOWN)
    assert calls[0].name == "get_weather" and calls[0].source == "prefix_tag"


def test_malformed_json_inside_tags_becomes_visible_failure():
    calls, _ = extract_tool_calls({"content": '<|tools_prefix|>[{"get_weather": {"city": }]<|tools_suffix|>'}, KNOWN)
    assert calls[0].name == "<unparseable>" and calls[0].parse_error


def test_xml_tool_call_tag():
    content = '<tool_call>{"name": "get_weather", "arguments": {"city": "Chur"}}</tool_call>'
    calls, _ = extract_tool_calls({"content": content}, KNOWN)
    assert calls[0].source == "xml_tag" and calls[0].arguments == {"city": "Chur"}


def test_bare_json_when_special_tokens_were_stripped():
    calls, text = extract_tool_calls({"content": '[{"get_weather": {"city": "Lugano"}}]'}, KNOWN)
    assert calls[0].source == "bare_json" and text == ""


def test_fenced_json_block():
    content = 'Let me check.\n```json\n{"name": "get_weather", "arguments": {"city": "Chur"}}\n```'
    calls, text = extract_tool_calls({"content": content}, KNOWN)
    assert calls[0].source == "json_text" and text == "Let me check."


def test_plain_json_answer_is_not_mistaken_for_a_tool_call():
    content = '{"city": "Lugano", "temperature": 12}'  # un normale oggetto JSON, nessun tool con quel nome
    calls, text = extract_tool_calls({"content": content}, KNOWN)
    assert calls == [] and text == content


def test_json_naming_unknown_tool_is_plain_text():
    calls, _ = extract_tool_calls({"content": '[{"book_flight": {"to": "ZRH"}}]'}, KNOWN)
    assert calls == []


def test_plain_text_answer():
    calls, text = extract_tool_calls({"content": "  Paris.  "}, KNOWN)
    assert calls == [] and text == "Paris."


# ----------------------------------------------------------------------------- ragionamento (<|inner_prefix|>)

def test_split_reasoning_complete_block():
    from agentbench.parser import split_reasoning
    visible, reasoning = split_reasoning("<|inner_prefix|>Forse 15 gradi? No, aspetto il tool.<|inner_suffix|>Servono 12 °C.")
    assert visible == "Servono 12 °C." and "15 gradi" in reasoning


def test_split_reasoning_truncated_thinking_leaves_no_visible_text():
    from agentbench.parser import split_reasoning
    visible, reasoning = split_reasoning("<|inner_prefix|>**Analyzing the request** the user wants")
    assert visible == "" and reasoning.startswith("**Analyzing")


def test_split_reasoning_closing_tag_without_opening():
    from agentbench.parser import split_reasoning
    visible, _ = split_reasoning("pensieri iniziali<|inner_suffix|>Risposta")
    assert visible == "Risposta"


def test_numbers_in_reasoning_do_not_reach_final_text():
    calls, text = extract_tool_calls(
        {"role": "assistant", "content": "<|inner_prefix|>Potrebbero essere 99 gradi<|inner_suffix|>A Lugano ci sono 12 °C."}, set())
    assert not calls and text == "A Lugano ci sono 12 °C." and "99" not in text


def test_tool_call_after_reasoning_is_parsed():
    msg = {"role": "assistant",
           "content": '<|inner_prefix|>Uso get_weather.<|inner_suffix|><|tools_prefix|>[{"get_weather": {"city": "Lugano"}}]'}
    calls, text = extract_tool_calls(msg, {"get_weather"})
    assert [c.name for c in calls] == ["get_weather"] and calls[0].arguments == {"city": "Lugano"} and text == ""
