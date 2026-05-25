import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List

import yaml

from model_client import create_model_client
from validators import validate_case_output
from judge_client import create_judge_client
from metrics import compute_case_total_score, save_reports


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_eval_cases(path: str) -> List[Dict[str, Any]]:
    cases = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc

            if "id" not in item:
                item["id"] = f"case_{line_no:04d}"

            if "input" not in item:
                raise ValueError(f"Case {item['id']} missing required field: input")

            cases.append(item)

    return cases


def set_seed(seed: int) -> None:
    random.seed(seed)

    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def evaluate_case(
    case: Dict[str, Any],
    model_client: Any,
    judge_client: Any,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    raw_output = model_client.generate_from_case(case)

    validation_result = validate_case_output(
        raw_output=raw_output,
        case=case,
        config=config
    )

    parsed_output = validation_result.get("parsed_output")
    if not isinstance(parsed_output, dict):
        parsed_output = {}

    judge_result = judge_client.score(case, parsed_output)

    total_score = compute_case_total_score(
        validation_result=validation_result,
        judge_result=judge_result,
        config=config
    )

    return {
        "case": case,
        "raw_output": raw_output,
        "validation": validation_result,
        "judge": judge_result,
        "total_score": total_score
    }


def print_case_result(index: int, total: int, result: Dict[str, Any]) -> None:
    case = result.get("case", {})
    validation = result.get("validation", {})
    judge = result.get("judge", {})

    case_id = case.get("id", f"case_{index}")
    category = case.get("category", "unknown")
    passed = validation.get("passed", False)
    action = validation.get("action")
    total_score = result.get("total_score", 0.0)
    errors = validation.get("errors", [])

    status = "PASS" if passed else "FAIL"

    print(f"[{index}/{total}] {status} {case_id} | category={category} | action={action} | score={total_score:.4f}")

    if errors:
        print("  errors:", errors)

    if judge and judge.get("enabled"):
        if judge.get("success"):
            print(f"  judge persona_score={judge.get('persona_score')} ")
        else:
            print(f"  judge error={judge.get('error')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Qwen-7B-Instruct LoRA desktop-pet model.")
    parser.add_argument(
        "--config",
        type=str,
        default="eval_config.yaml",
        help="Path to eval_config.yaml."
    )
    args = parser.parse_args()

    config = load_yaml(args.config)

    runtime_cfg = config.get("runtime", {})
    seed = int(runtime_cfg.get("seed", 42))
    set_seed(seed)

    eval_cases_path = config.get("eval_data", {}).get("cases_path", "./eval_cases.jsonl")
    cases = load_eval_cases(eval_cases_path)

    if not cases:
        raise ValueError(f"No eval cases found in {eval_cases_path}")

    model_client = create_model_client(config)
    judge_client = create_judge_client(config)

    print_each_case = bool(runtime_cfg.get("print_each_case", True))

    results = []
    total = len(cases)

    for index, case in enumerate(cases, start=1):
        result = evaluate_case(
            case=case,
            model_client=model_client,
            judge_client=judge_client,
            config=config
        )

        results.append(result)

        if print_each_case:
            print_case_result(index, total, result)

    report_payload = save_reports(results, config)

    output_cfg = config.get("output", {})
    json_report_path = output_cfg.get("json_report_path", "./reports/eval_report.json")
    markdown_report_path = output_cfg.get("markdown_report_path", "./reports/eval_report.md")

    summary = report_payload.get("summary", {})

    print("")
    print("Evaluation finished.")
    print(f"Total cases: {summary.get('total_cases', 0)}")
    print(f"Passed cases: {summary.get('passed_cases', 0)}")
    print(f"Failed cases: {summary.get('failed_cases', 0)}")
    print(f"Pass rate: {summary.get('pass_rate', 0.0) * 100:.2f}%")
    print(f"Average total score: {summary.get('average_total_score', 0.0):.4f}")
    print(f"JSON report: {json_report_path}")
    print(f"Markdown report: {markdown_report_path}")


if __name__ == "__main__":
    main()
