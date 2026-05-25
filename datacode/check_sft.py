import json
import os

# ✅ 你的数据目录（推荐用 raw string）
BASE_DIR = r"C:\Users\13489\Desktop\NLP\trysth"

FILES = [
    "train_sft.json",
    "reverse_sft.json",
    "multi_turn_sft.json"
]

VALID_ACTIONS = {
    "annoyed",
    "resigned",
    "pleased",
    "gentle_smile",
    "tired",
    "stern_remind",
    "reject",
    "cutesy"
}


def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def validate_gpt_output(text, idx, file_name):
    errors = []

    try:
        data = json.loads(text)
    except Exception as e:
        return [f"[{file_name}][{idx}] ❌ GPT输出不是合法JSON: {e}"]

    if not isinstance(data, dict):
        return [f"[{file_name}][{idx}] ❌ GPT输出不是dict"]

    if "text" not in data:
        errors.append(f"[{file_name}][{idx}] ❌ 缺少 text")

    if "action" not in data:
        errors.append(f"[{file_name}][{idx}] ❌ 缺少 action")

    action = data.get("action")
    if action not in VALID_ACTIONS:
        errors.append(f"[{file_name}][{idx}] ❌ 非法 action: {action}")

    return errors


def validate_conversations(convs, idx, file_name):
    errors = []

    if not isinstance(convs, list) or len(convs) < 2:
        return [f"[{file_name}][{idx}] ❌ conversations 结构错误"]

    for i, turn in enumerate(convs):
        if not isinstance(turn, dict):
            errors.append(f"[{file_name}][{idx}] ❌ turn不是dict")
            continue

        if "from" not in turn or "value" not in turn:
            errors.append(f"[{file_name}][{idx}] ❌ turn字段缺失")
            continue

        if turn["from"] not in {"human", "gpt"}:
            errors.append(f"[{file_name}][{idx}] ❌ 非法from: {turn['from']}")

    # ✅ 最后一条必须是gpt
    last_turn = convs[-1]
    if last_turn.get("from") == "gpt":
        errors.extend(validate_gpt_output(last_turn.get("value", ""), idx, file_name))
    else:
        errors.append(f"[{file_name}][{idx}] ❌ 最后一条不是gpt")

    return errors


def validate_file(file_name):
    file_path = os.path.join(BASE_DIR, file_name)

    print(f"\n📂 检查文件: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在")
        return

    data, err = load_json(file_path)

    if err:
        print(f"❌ JSON解析失败: {err}")
        return

    if not isinstance(data, list):
        print("❌ 顶层不是list")
        return

    total = len(data)
    error_count = 0

    for idx, item in enumerate(data):

        if not isinstance(item, dict):
            print(f"[{file_name}][{idx}] ❌ item不是dict")
            error_count += 1
            continue

        if "conversations" not in item:
            print(f"[{file_name}][{idx}] ❌ 缺少 conversations")
            error_count += 1
            continue

        errors = validate_conversations(item["conversations"], idx, file_name)

        if errors:
            error_count += 1
            for e in errors:
                print(e)

    print("--------")
    print(f"总数: {total}")
    print(f"错误: {error_count}")
    print(f"通过率: {(total - error_count) / total:.2%}")


if __name__ == "__main__":
    print(f"📁 当前检测目录: {BASE_DIR}")

    for file_name in FILES:
        validate_file(file_name)
