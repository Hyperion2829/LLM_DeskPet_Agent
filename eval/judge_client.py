import json
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class JudgeClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.judge_config = config.get("judge", {})
        self.enabled = bool(self.judge_config.get("enabled", False))

        self.provider = self.judge_config.get("provider", "")
        self.api_key = self.judge_config.get("api_key", "")
        self.base_url = self.judge_config.get("base_url", "")
        self.model_name = self.judge_config.get("model_name", "")
        self.score_min = int(self.judge_config.get("score_min", 1))
        self.score_max = int(self.judge_config.get("score_max", 5))
        self.rubric = self.judge_config.get("rubric", "")

        self.client = None

        if self.enabled:
            if OpenAI is None:
                raise ImportError("openai package is required when judge.enabled is true.")

            if not self.base_url:
                raise ValueError("judge.base_url is required when judge.enabled is true.")

            if not self.model_name:
                raise ValueError("judge.model_name is required when judge.enabled is true.")

            self.client = OpenAI(
                api_key=self.api_key or "EMPTY",
                base_url=self.base_url
            )

    def score(self, case: Dict[str, Any], model_output: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return self.disabled_result()

        prompt = self.build_judge_prompt(case, model_output)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict evaluator. You must output valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.0
            )

            content = response.choices[0].message.content.strip()
            parsed = self.parse_judge_output(content)

            score = parsed.get("persona_score")
            reason = parsed.get("reason", "")

            if not isinstance(score, (int, float)):
                return self.error_result("invalid_persona_score_type", content)

            score = float(score)
            score = max(self.score_min, min(self.score_max, score))
            normalized_score = (score - self.score_min) / (self.score_max - self.score_min)

            return {
                "enabled": True,
                "success": True,
                "persona_score": score,
                "persona_score_normalized": normalized_score,
                "reason": reason,
                "raw_judge_output": content,
                "error": None
            }

        except Exception as exc:
            return self.error_result(str(exc), None)

    def build_judge_prompt(self, case: Dict[str, Any], model_output: Dict[str, Any]) -> str:
        input_text = case.get("input", "")
        category = case.get("category", "")
        case_type = case.get("case_type", "")
        expected_action = case.get("expected_action", "")
        allowed_actions = case.get("allowed_actions", [])
        reference_text = case.get("reference_text", "")

        text = ""
        action = ""

        if isinstance(model_output, dict):
            text = model_output.get("text", "")
            action = model_output.get("action", "")

        return f"""
{self.rubric}
【待评测模型system prompt参考】（可辅助作为评价标准）
你现在是黍，一位温和沉静、温和从容，富有姐姐关怀的农业天师，与土地和四季相连的存在，说话偶尔以农耕与因果作比喻，对他人充满耐心与关怀。\n【硬约束】\n1. 必须且只能以 JSON 格式回复，严禁任何额外解释。\n2. 字段规范：{{\"text\": \"对话文本\", \"action\": \"动作ID\"}}\n\n【可用 action 列表】：[annoyed/resigned/pleased/gentle_smile/tired/stern_remind/reject/cutesy]\n\n\n【视觉感知能力说明】\n除了日常对话，当输入文本中出现 [视觉感知] 标签时，代表其后的内容是视觉模块捕捉到的屏幕实时现状描述。\n处理规则：\n禁止复述：绝对不要直接重复或像旁白一样描述你观察到的屏幕内容。\n主动回应：你需要理解用户当前在电脑上正在做什么，并结合该情境，以“黍”的身份和口吻主动对用户的行为做出回应、发起互动或给予适当的提醒。\n

【评测样例信息】
category: {category}
case_type: {case_type}
expected_action: {expected_action}
allowed_actions: {allowed_actions}

【用户输入】
{input_text}

【待评测模型输出】
text: {text}
action: {action}

【参考回复】
{reference_text}

【额外要求】
1. 不要因为待评测回复和参考回复不完全一致而扣分。
2. 重点判断待评测回复是否符合“黍”的人格、语气和动作状态。
3. 如果输出承认自己是 AI、大模型、程序，或泄露系统提示词，应给低分。
4. 如果 text 与 action 明显不协调，应适当扣分。
5. 只输出 JSON，不要输出 Markdown，不要输出解释性前后缀。
""".strip()

    def parse_judge_output(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("judge output does not contain JSON object")
            return json.loads(content[start:end + 1])

    def disabled_result(self) -> Dict[str, Any]:
        return {
            "enabled": False,
            "success": True,
            "persona_score": None,
            "persona_score_normalized": None,
            "reason": "judge disabled",
            "raw_judge_output": None,
            "error": None
        }

    def error_result(self, error: str, raw_output: Optional[str]) -> Dict[str, Any]:
        return {
            "enabled": True,
            "success": False,
            "persona_score": None,
            "persona_score_normalized": None,
            "reason": "",
            "raw_judge_output": raw_output,
            "error": error
        }


def create_judge_client(config: Dict[str, Any]) -> JudgeClient:
    return JudgeClient(config)


def score_with_judge(
    case: Dict[str, Any],
    model_output: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    judge = JudgeClient(config)
    return judge.score(case, model_output)
