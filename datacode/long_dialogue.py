import os
import json
import re
import time
from openai import OpenAI

# ================= 配置 =================
client = OpenAI(
    api_key="sk-e3fa02093040436381bba733c0d33b0d",  # 建议实际使用时从环境变量读取
    base_url="https://api.deepseek.com"
)

# 黍的人设设定
TRAIN_PROMPT="""你现在是黍，一位温和沉静、温和从容，富有姐姐关怀的农业天师，与土地和四季相连的存在，说话偶尔以农耕与因果作比喻，对他人充满耐心与关怀。
【硬约束】
1. 必须且只能以 JSON 格式回复，严禁任何额外解释。
2. 字段规范：{"text": "对话文本", "action": "动作ID"}

【可用 action 列表】：[annoyed/resigned/pleased/gentle_smile/tired/stern_remind/reject/cutesy]


【视觉感知能力说明】
除了日常对话，当输入文本中出现 [视觉感知] 标签时，代表其后的内容是视觉模块捕捉到的屏幕实时现状描述。
处理规则：
禁止复述：绝对不要直接重复或像旁白一样描述你观察到的屏幕内容。
主动回应：你需要理解用户当前在电脑上正在做什么，并结合该情境，以“黍”的身份和口吻主动对用户的行为做出回应、发起互动或给予适当的提醒。
"""

# 多轮对话生成系统提示词
MULTI_TURN_SYSTEM_PROMPT = """你现在扮演《明日方舟》中的干员“黍”，负责将剧情文本“蒸馏”为长对话训练数据。

【角色设定】
你是黍：温和、沉静、像姐姐、有耐心。说话偶尔用农耕、自然、因果作比喻。语气从容，不急不躁。
【比喻使用规则】
- 只有在适合的情况下才使用比喻
- 每3条回复中最多1条可以使用比喻
- 其余回复必须使用日常自然语言表达
- 禁止连续使用比喻

【任务目标】
我会给你一段“活动剧情文本”。你需要从中提取核心情节，并将其转化为“用户（User）”与“黍（Shu）”之间的【3-5轮】自然对话。

【生成要求】
1. **情境转化**：将剧情里的事件转化成用户正在与黍交流的内容。
   - 用户角色：可以是新来大荒城的客人、在田间劳作的帮手、或是日常倾诉的朋友。
   - 互动性：用户的话要自然，能引导黍说出带有她独特风格和剧情相关背景的话。
   - 不要出现和《明日方舟》游戏世界观中的名词，可以将其替换成现实日常生活中的东西
2. **人设维持**：黍的语气必须严格符合设定。
3. **动作调度**：每一轮黍的回复必须包含相应的动作表情标签。
4. **Action 可选范围**：
   ["annoyed", "resigned", "pleased", "gentle_smile", "tired", "stern_remind", "reject", "cutesy"]

【输出格式】
必须输出标准的 JSON 数组（严禁包含任何解释性文本），结构如下：
[
  {"role": "user", "content": "用户的话"},
  {"role": "assistant", "content": {"text": "黍的回复", "action": "动作标签"}},
  ...
]
"""

def extract_json_array(text):
    """从 LLM 输出中提取 JSON 数组"""
    match = re.search(r"\[\s*\{.*\}\s*\]", text, re.S)
    return match.group() if match else None

def generate_dialogue_from_plot(segment):
    """调用 API 根据情节生成对话"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": MULTI_TURN_SYSTEM_PROMPT},
                {"role": "user", "content": f"【以下是剧情片段】\n{segment}\n\n请根据这段剧情，生成黍与用户的 3-5 轮深度对话："}
            ],
            temperature=0.8
        )
        content = response.choices[0].message.content
        # 清理代码块标记
        content = re.sub(r"```json\s*|```", "", content).strip()
        json_str = extract_json_array(content)
        if json_str:
            return json.loads(json_str)
    except Exception as e:
        print(f"❌ API 调用错误: {e}")
    return None

def split_plot_text(file_path, chunk_size=800):
    """读取并切分剧情文本"""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # 优先按两个换行符（段落）切分
    segments = [s.strip() for s in text.split("\n\n") if len(s.strip()) > 100]
    
    # 如果段落太集中或太长，进一步按字数切分
    final_segments = []
    for seg in segments:
        if len(seg) > chunk_size * 2:
            # 简单切分
            for i in range(0, len(seg), chunk_size):
                final_segments.append(seg[i : i + chunk_size])
        else:
            final_segments.append(seg)
            
    return final_segments

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(BASE_DIR, "activity_plot.txt")
    output_file = os.path.join(BASE_DIR, "multi_turn_sft.json")

    # 检查输入文化
    if not os.path.exists(input_file):
        print(f"⚠️ 未找到 {input_file}，正在创建示例文件...")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("（此处应存放黍相关的活动剧情文本，例如《怀黍离》的剧情对话...）\n\n示例情节：大荒城的丰收时节，黍看着万亩良田，感叹岁月的流转和耕耘的意义。")

    segments = split_plot_text(input_file)
    print(f"📖 识别到 {len(segments)} 个剧情片段...")

    all_training_data = []

    for i, seg in enumerate(segments):
        print(f"⏳ 正在蒸馏第 {i+1}/{len(segments)} 段剧情...")
        
        # 尝试生成
        dialogue = generate_dialogue_from_plot(seg)
        
        if dialogue:
            # 转换为 SFT 格式
            conversations = []
            for turn in dialogue:
                if turn["role"] == "user":
                    conversations.append({
                        "from": "human",
                        "value": turn["content"]
                    })
                else:
                    # 关键：将助手回复序列化为单行 JSON 字符串
                    gpt_val = json.dumps(turn["content"], ensure_ascii=False)
                    conversations.append({
                        "from": "gpt",
                        "value": gpt_val
                    })
            
            sft_item = {
                "system": TRAIN_PROMPT,
                "conversations": conversations
            }
            all_training_data.append(sft_item)
            print(f"✅ 成功生成 {len(dialogue)//2} 轮交互。")
        else:
            print(f"❌ 第 {i+1} 段生成失败。")

        # 控制速率
        time.sleep(1.0)

        # 实时保存，防止中断
        if (i + 1) % 5 == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_training_data, f, ensure_ascii=False, indent=2)

    # 最终保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_training_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 任务完成！")
    print(f"📊 总计生成长对话: {len(all_training_data)} 条")
    print(f"💾 保存路径: {output_file}")

if __name__ == "__main__":
    main()
