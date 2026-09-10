"""Pure helpers for indexing and selecting routing patterns."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def literal_prefix(text: str) -> Optional[str]:
    """Return the first literal token from a regular-expression pattern."""
    if not text:
        return None
    literal: List[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            next_char = text[index + 1]
            if next_char in {"s", "S", "d", "D", "w", "W", "t", "n", "r"}:
                break
            literal.append(next_char)
            index += 2
            continue
        if char in "[](){}.*+?|$^":
            break
        literal.append(char)
        index += 1
    token = "".join(literal).strip().lower()
    if not token:
        return None
    return token.split()[0]


def pattern_prefixes(pattern_spec: str) -> List[str]:
    """Return literal lookup prefixes for a routing pattern."""
    spec = (pattern_spec or "").strip()
    if not spec:
        return []
    if spec.startswith("^"):
        spec = spec[1:]
    prefixes: List[str] = []
    if spec.startswith("(?:"):
        close_index = spec.find(")")
        if close_index > 3:
            inner = spec[3:close_index]
            for alternative in inner.split("|"):
                token = literal_prefix(alternative)
                if token:
                    prefixes.append(token)
            if prefixes:
                return sorted(set(prefixes))
    token = literal_prefix(spec)
    if token:
        prefixes.append(token)
    return sorted(set(prefixes))


def build_routing_indexes(
    rules: List[Dict[str, Any]],
    route_lookup: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Compile routing rules and build prefix and fallback indexes."""
    indexed_rules = [dict(rule) for rule in rules]
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    fallback: List[Dict[str, Any]] = []
    for rule in indexed_rules:
        pattern_spec = rule.get("pattern_spec") or ""
        if rule.get("pattern_type") == "json_regex" and isinstance(pattern_spec, str):
            try:
                rule["_compiled_pattern"] = re.compile(pattern_spec, re.IGNORECASE)
            except re.error:
                rule["_compiled_pattern"] = None
        prefixes = pattern_prefixes(str(pattern_spec))
        rule["_prefixes"] = prefixes
        if prefixes:
            for prefix in prefixes:
                buckets.setdefault(prefix, []).append(rule)
        else:
            fallback.append(rule)
    for bucket in buckets.values():
        bucket.sort(key=_routing_sort_key)
    fallback.sort(key=_routing_sort_key)
    return indexed_rules, buckets, fallback, route_lookup


def match_json_pattern(
    input_data: Any,
    pattern_spec: str,
    pattern_type: str,
) -> Tuple[bool, Dict[str, Any]]:
    """Match structured input against one supported pattern type."""
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except json.JSONDecodeError:
            input_data = {"raw_input": input_data}

    try:
        if pattern_type == "json_path":
            return _match_json_path(input_data, pattern_spec)
        if pattern_type == "json_value":
            return _match_json_value(input_data, pattern_spec)
        if pattern_type == "json_regex":
            return _match_json_regex(input_data, pattern_spec)
        return False, {}
    except Exception:
        return False, {}


def _match_json_path(data: Dict[str, Any], path_spec: str) -> Tuple[bool, Dict[str, Any]]:
    if not path_spec.startswith("$."):
        return False, {}
    keys = path_spec[2:].split(".")
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False, {}
    return True, {path_spec: current}


def _match_json_value(data: Dict[str, Any], value_spec: str) -> Tuple[bool, Dict[str, Any]]:
    if isinstance(data, dict):
        for key, value in data.items():
            if str(value).lower() == value_spec.lower():
                return True, {key: value}
    return False, {}


def _match_json_regex(data: Dict[str, Any], regex_pattern: str) -> Tuple[bool, Dict[str, Any]]:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and re.match(regex_pattern, value, re.IGNORECASE):
                return True, {key: value}
    return False, {}


def match_routing_rule(
    pattern: Dict[str, Any],
    normalized_text: str,
    parsed_input: Optional[Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    """Match one routing rule against structured or plain-text input."""
    pattern_type = pattern.get("pattern_type")
    pattern_spec = pattern.get("pattern_spec") or ""
    if parsed_input:
        return match_json_pattern(parsed_input, pattern_spec, pattern_type)
    if pattern_type == "json_regex":
        compiled = pattern.get("_compiled_pattern")
        match = compiled.match(normalized_text) if compiled is not None else re.match(
            pattern_spec, normalized_text, re.IGNORECASE
        )
        if not match:
            return False, {}
        extracted = {"input_text": normalized_text}
        if match.groups():
            extracted["groups"] = list(match.groups())
            for index, value in enumerate(match.groups(), start=1):
                extracted[f"group{index}"] = value
        return True, extracted
    if pattern_type == "json_value":
        matched = str(pattern_spec).lower() in normalized_text.lower()
        return (matched, {"input_text": normalized_text}) if matched else (False, {})
    if pattern_type == "json_path":
        return True, {"intent": normalized_text, "type": "general_command"}
    return False, {}


def _routing_sort_key(item: Dict[str, Any]) -> Tuple[int, str]:
    """Sort routes by descending priority and stable pattern name."""
    return (-int(item.get("priority", 0) or 0), str(item.get("pattern_name", "")))


def route_candidates_for_text(
    normalized_text: str,
    buckets: Dict[str, List[Dict[str, Any]]],
    fallback: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return deduplicated routing candidates for normalized input text."""
    text = normalized_text.strip().lower()
    if not text:
        return list(fallback)
    tokens = text.split()
    candidates: List[Dict[str, Any]] = []
    seen: set[str] = set()
    probe_keys: List[str] = []

    def add_key(key: str) -> None:
        key = (key or "").strip().lower()
        if key and key not in probe_keys:
            probe_keys.append(key)

    if tokens:
        first = tokens[0]
        add_key(first)
        if len(tokens) > 1:
            add_key(" ".join(tokens[:2]))
        for variant in list(probe_keys):
            add_key(variant.split("(", 1)[0])
            add_key(variant.split(".", 1)[0])
            add_key(variant.split("::", 1)[0])
    add_key(text)
    for key in probe_keys:
        for rule in buckets.get(key, []):
            pattern_name = str(rule.get("pattern_name", ""))
            if pattern_name in seen:
                continue
            seen.add(pattern_name)
            candidates.append(rule)
    for rule in fallback:
        pattern_name = str(rule.get("pattern_name", ""))
        if pattern_name in seen:
            continue
        seen.add(pattern_name)
        candidates.append(rule)
    candidates.sort(key=_routing_sort_key)
    return candidates
