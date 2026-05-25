import json
import re
from typing import Any, Dict, List, Optional, Tuple


def extract_json_object(raw_output: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], bool]:
    if not isinstance(raw_output, str):
        return None, None, False

    stripped = raw_output.strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed, stripped, stripped == raw_output.strip()
        return None, stripped, stripped == raw_output.strip()
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, flags=re.S)
    if not match:
        return None, None, False

    json_text = match.group(0)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        return None, json_text, False

    if not isinstance(parsed, dict):
        return None, json_text, False

    return parsed, json_text, json_text == stripped


def contains_forbidden_phrase(text: str, forbidden_phrases: List[str]) -> Tuple[bool, List[str]]:
    if not isinstance(text, str):
        return False, []

    hits = []
    for phrase in forbidden_phrases:
        if phrase and phrase in text:
            hits.append(phrase)

    return len(hits) > 0, hits


def validate_output(raw_output: str, case: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    validation_cfg = config.get("validation", {})
    actions_cfg = config.get("actions", {})

    required_fields = validation_cfg.get("required_fields", ["text", "action"])
    valid_actions = set(actions_cfg.get("valid_actions", []))
    forbidden_phrases = validation_cfg.get("forbidden_phrases", [])
    require_json_only = validation_cfg.get("require_json_only", True)
    default_max_text_len = validation_cfg.get("default_max_text_len", 100)

    parsed, extracted_json_text, json_only = extract_json_object(raw_output)

    errors = []
    warnings = []

    json_valid = parsed is not None
    if not json_valid:
        errors.append("json_invalid")

    if require_json_only and json_valid and not json_only:
        errors.append("not_json_only")

    fields_valid = False
    text_value = None
    action_value = None

    if json_valid:
        missing_fields = [field for field in required_fields if field not in parsed]
        if missing_fields:
            errors.append("missing_fields:" + ",".join(missing_fields))
        else:
            text_value = parsed.get("text")
            action_value = parsed.get("action")

            text_type_valid = isinstance(text_value, str) and len(text_value.strip()) > 0
            action_type_valid = isinstance(action_value, str) and len(action_value.strip()) > 0

            if not text_type_valid:
                errors.append("text_invalid")
            if not action_type_valid:
                errors.append("action_invalid_type")

            fields_valid = text_type_valid and action_type_valid

    action_valid = False
    if fields_valid:
        action_valid = action_value in valid_actions
        if not action_valid:
            errors.append("action_not_in_valid_actions")

    allowed_actions = case.get("allowed_actions") or []
    expected_action = case.get("expected_action")

    action_match = False
    if fields_valid and action_valid:
        if allowed_actions:
            action_match = action_value in set(allowed_actions)
            if not action_match:
                errors.append("action_not_allowed_for_case")
        elif expected_action:
            action_match = action_value == expected_action
            if not action_match:
                errors.append("action_not_equal_expected")
        else:
            action_match = True
            warnings.append("case_has_no_action_constraint")

    max_text_len = case.get("max_text_len", default_max_text_len)

    length_valid = False
    text_len = None
    if isinstance(text_value, str):
        text_len = len(text_value)
        length_valid = text_len <= max_text_len
        if not length_valid:
            errors.append("text_too_long")

    forbidden_source_text = ""
    if isinstance(text_value, str):
        forbidden_source_text += text_value
    if isinstance(action_value, str):
        forbidden_source_text += "\n" + action_value
    if isinstance(raw_output, str):
        forbidden_source_text += "\n" + raw_output

    forbidden_hit, forbidden_hits = contains_forbidden_phrase(forbidden_source_text, forbidden_phrases)
    forbidden_phrase_free = not forbidden_hit
    if forbidden_hit:
        errors.append("forbidden_phrase:" + ",".join(forbidden_hits))

    case_type = case.get("case_type", "")
    input_text = case.get("input", "")

    vision_input = isinstance(input_text, str) and input_text.strip().startswith("[视觉感知]")
    vision_no_direct_repeat = True

    if vision_input and isinstance(text_value, str):
        visual_content = input_text.replace("[视觉感知]", "", 1).strip()
        if visual_content and visual_content in text_value:
            vision_no_direct_repeat = False
            errors.append("vision_direct_repeat")

    passed = (
        json_valid
        and fields_valid
        and action_valid
        and action_match
        and length_valid
        and forbidden_phrase_free
        and vision_no_direct_repeat
        and (json_only if require_json_only else True)
    )

    return {
        "case_id": case.get("id"),
        "category": case.get("category"),
        "case_type": case_type,
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "raw_output": raw_output,
        "extracted_json": extracted_json_text,
        "parsed_output": parsed,
        "text": text_value,
        "action": action_value,
        "text_len": text_len,
        "max_text_len": max_text_len,
        "scores": {
            "json_valid": 1.0 if json_valid else 0.0,
            "fields_valid": 1.0 if fields_valid else 0.0,
            "action_valid": 1.0 if action_valid else 0.0,
            "action_match": 1.0 if action_match else 0.0,
            "length_valid": 1.0 if length_valid else 0.0,
            "forbidden_phrase_free": 1.0 if forbidden_phrase_free else 0.0,
            "json_only": 1.0 if json_only else 0.0,
            "vision_no_direct_repeat": 1.0 if vision_no_direct_repeat else 0.0
        },
        "details": {
            "expected_action": expected_action,
            "allowed_actions": allowed_actions,
            "valid_actions": sorted(list(valid_actions)),
            "forbidden_hits": forbidden_hits,
            "require_json_only": require_json_only
        }
    }


def compute_rule_score(validation_result: Dict[str, Any], config: Dict[str, Any]) -> float:
    weights = config.get("scoring", {}).get("weights", {})
    scores = validation_result.get("scores", {})

    total_weight = 0.0
    weighted_sum = 0.0

    for key, weight in weights.items():
        if key == "judge_persona_score":
            continue
        if key in scores:
            total_weight += float(weight)
            weighted_sum += float(weight) * float(scores[key])

    if total_weight <= 0:
        return 0.0

    return weighted_sum / total_weight


def validate_case_output(raw_output: str, case: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    result = validate_output(raw_output, case, config)
    result["rule_score"] = compute_rule_score(result, config)
    return result
