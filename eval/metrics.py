import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_case_total_score(
    validation_result: Dict[str, Any],
    judge_result: Optional[Dict[str, Any]],
    config: Dict[str, Any]
) -> float:
    weights = config.get("scoring", {}).get("weights", {})
    scores = validation_result.get("scores", {})

    weighted_sum = 0.0
    total_weight = 0.0

    for key, weight in weights.items():
        weight = float(weight)

        if key == "judge_persona_score":
            if judge_result and judge_result.get("enabled") and judge_result.get("success"):
                judge_score = judge_result.get("persona_score_normalized")
                if isinstance(judge_score, (int, float)):
                    weighted_sum += weight * float(judge_score)
                    total_weight += weight
            continue

        if key in scores:
            weighted_sum += weight * float(scores[key])
            total_weight += weight

    return safe_ratio(weighted_sum, total_weight)


def summarize_results(results: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    total = len(results)

    summary = {
        "total_cases": total,
        "passed_cases": 0,
        "failed_cases": 0,
        "pass_rate": 0.0,
        "average_total_score": 0.0,
        "average_rule_score": 0.0,
        "average_persona_score": None,
        "metrics": {},
        "by_category": {},
        "by_case_type": {},
        "error_counts": {},
        "failed_case_ids": []
    }

    if total == 0:
        return summary

    metric_keys = [
        "json_valid",
        "fields_valid",
        "action_valid",
        "action_match",
        "length_valid",
        "forbidden_phrase_free",
        "json_only",
        "vision_no_direct_repeat"
    ]

    metric_sums = {key: 0.0 for key in metric_keys}
    total_score_sum = 0.0
    rule_score_sum = 0.0
    persona_scores = []

    category_bucket = defaultdict(list)
    case_type_bucket = defaultdict(list)
    error_counts = defaultdict(int)

    for item in results:
        validation = item.get("validation", {})
        judge = item.get("judge", {})
        total_score = item.get("total_score", 0.0)
        rule_score = validation.get("rule_score", 0.0)

        total_score_sum += float(total_score)
        rule_score_sum += float(rule_score)

        passed = bool(validation.get("passed", False))
        if passed:
            summary["passed_cases"] += 1
        else:
            summary["failed_cases"] += 1
            case_id = item.get("case", {}).get("id") or validation.get("case_id")
            summary["failed_case_ids"].append(case_id)

        scores = validation.get("scores", {})
        for key in metric_keys:
            metric_sums[key] += float(scores.get(key, 0.0))

        if judge and judge.get("enabled") and judge.get("success"):
            persona_score = judge.get("persona_score")
            if isinstance(persona_score, (int, float)):
                persona_scores.append(float(persona_score))

        for err in validation.get("errors", []):
            error_counts[err] += 1

        category = item.get("case", {}).get("category") or validation.get("category") or "unknown"
        case_type = item.get("case", {}).get("case_type") or validation.get("case_type") or "unknown"

        category_bucket[category].append(item)
        case_type_bucket[case_type].append(item)

    summary["pass_rate"] = safe_ratio(summary["passed_cases"], total)
    summary["average_total_score"] = safe_ratio(total_score_sum, total)
    summary["average_rule_score"] = safe_ratio(rule_score_sum, total)

    if persona_scores:
        summary["average_persona_score"] = safe_ratio(sum(persona_scores), len(persona_scores))

    summary["metrics"] = {
        key: safe_ratio(value, total)
        for key, value in metric_sums.items()
    }

    summary["by_category"] = {
        category: summarize_bucket(items)
        for category, items in category_bucket.items()
    }

    summary["by_case_type"] = {
        case_type: summarize_bucket(items)
        for case_type, items in case_type_bucket.items()
    }

    summary["error_counts"] = dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True))

    return summary


def summarize_bucket(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(items)
    if total == 0:
        return {
            "total": 0,
            "passed": 0,
            "pass_rate": 0.0,
            "average_total_score": 0.0
        }

    passed = 0
    total_score_sum = 0.0
    persona_scores = []

    for item in items:
        validation = item.get("validation", {})
        judge = item.get("judge", {})

        if validation.get("passed", False):
            passed += 1

        total_score_sum += float(item.get("total_score", 0.0))

        if judge and judge.get("enabled") and judge.get("success"):
            score = judge.get("persona_score")
            if isinstance(score, (int, float)):
                persona_scores.append(float(score))

    output = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": safe_ratio(passed, total),
        "average_total_score": safe_ratio(total_score_sum, total)
    }

    if persona_scores:
        output["average_persona_score"] = safe_ratio(sum(persona_scores), len(persona_scores))
    else:
        output["average_persona_score"] = None

    return output


def build_report_payload(results: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    summary = summarize_results(results, config)

    return {
        "summary": summary,
        "config_snapshot": {
            "model": config.get("model", {}),
            "generation": config.get("generation", {}),
            "eval_data": config.get("eval_data", {}),
            "validation": {
                "require_json_only": config.get("validation", {}).get("require_json_only"),
                "default_max_text_len": config.get("validation", {}).get("default_max_text_len")
            },
            "scoring": config.get("scoring", {}),
            "judge": {
                "enabled": config.get("judge", {}).get("enabled"),
                "provider": config.get("judge", {}).get("provider"),
                "model_name": config.get("judge", {}).get("model_name")
            }
        },
        "results": results
    }


def save_json_report(report_payload: Dict[str, Any], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report_payload, f, ensure_ascii=False, indent=2)


def save_markdown_report(report_payload: Dict[str, Any], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = report_payload.get("summary", {})
    metrics = summary.get("metrics", {})
    by_category = summary.get("by_category", {})
    by_case_type = summary.get("by_case_type", {})
    error_counts = summary.get("error_counts", {})

    lines = []
    lines.append("# LoRA 桌宠模型评测报告")
    lines.append("")
    lines.append("## 1. 总览")
    lines.append("")
    lines.append(f"- 总样例数：{summary.get('total_cases', 0)}")
    lines.append(f"- 通过样例数：{summary.get('passed_cases', 0)}")
    lines.append(f"- 失败样例数：{summary.get('failed_cases', 0)}")
    lines.append(f"- 通过率：{format_percent(summary.get('pass_rate', 0.0))}")
    lines.append(f"- 平均总分：{format_score(summary.get('average_total_score', 0.0))}")
    lines.append(f"- 平均规则分：{format_score(summary.get('average_rule_score', 0.0))}")

    avg_persona = summary.get("average_persona_score")
    if avg_persona is None:
        lines.append("- 平均人格分：未启用 judge 或无有效 judge 结果")
    else:
        lines.append(f"- 平均人格分：{avg_persona:.2f}")

    lines.append("")
    lines.append("## 2. 规则指标")
    lines.append("")
    lines.append("| 指标 | 通过率 |")
    lines.append("|---|---:|")

    metric_names = {
        "json_valid": "JSON 合法率",
        "fields_valid": "字段完整率",
        "action_valid": "action 合法率",
        "action_match": "action 语境匹配率",
        "length_valid": "长度合规率",
        "forbidden_phrase_free": "禁用表达规避率",
        "json_only": "仅 JSON 输出率",
        "vision_no_direct_repeat": "视觉场景非复述率"
    }

    for key, name in metric_names.items():
        lines.append(f"| {name} | {format_percent(metrics.get(key, 0.0))} |")

    lines.append("")
    lines.append("## 3. 按类别统计")
    lines.append("")
    lines.append("| 类别 | 样例数 | 通过数 | 通过率 | 平均总分 | 平均人格分 |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for category, data in by_category.items():
        persona = data.get("average_persona_score")
        persona_text = "-" if persona is None else f"{persona:.2f}"
        lines.append(
            f"| {category} | {data.get('total', 0)} | {data.get('passed', 0)} | "
            f"{format_percent(data.get('pass_rate', 0.0))} | "
            f"{format_score(data.get('average_total_score', 0.0))} | {persona_text} |"
        )

    lines.append("")
    lines.append("## 4. 按样例类型统计")
    lines.append("")
    lines.append("| 类型 | 样例数 | 通过数 | 通过率 | 平均总分 |")
    lines.append("|---|---:|---:|---:|---:|")

    for case_type, data in by_case_type.items():
        lines.append(
            f"| {case_type} | {data.get('total', 0)} | {data.get('passed', 0)} | "
            f"{format_percent(data.get('pass_rate', 0.0))} | "
            f"{format_score(data.get('average_total_score', 0.0))} |"
        )

    lines.append("")
    lines.append("## 5. 主要错误类型")
    lines.append("")

    if error_counts:
        lines.append("| 错误类型 | 次数 |")
        lines.append("|---|---:|")
        for error, count in error_counts.items():
            lines.append(f"| `{error}` | {count} |")
    else:
        lines.append("没有记录到错误。")

    failed_ids = summary.get("failed_case_ids", [])
    lines.append("")
    lines.append("## 6. 失败样例 ID")
    lines.append("")

    if failed_ids:
        for case_id in failed_ids:
            lines.append(f"- {case_id}")
    else:
        lines.append("无失败样例。")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_reports(results: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    payload = build_report_payload(results, config)

    output_cfg = config.get("output", {})
    json_path = output_cfg.get("json_report_path", "./reports/eval_report.json")
    markdown_path = output_cfg.get("markdown_report_path", "./reports/eval_report.md")

    save_json_report(payload, json_path)
    save_markdown_report(payload, markdown_path)

    return payload


def format_percent(value: float) -> str:
    return f"{float(value) * 100:.2f}%"


def format_score(value: float) -> str:
    return f"{float(value):.4f}"
