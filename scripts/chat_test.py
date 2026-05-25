import os
import sys
import json
import readline

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)


llama_factory_src = os.path.join(project_root, "LLaMA-Factory/src")
if llama_factory_src not in sys.path:
    sys.path.append(llama_factory_src)

from src.memory_manager_test import ShortTermMemory
from llamafactory.chat import ChatModel

# ================= 配置区 =================
SHU_SYSTEM_PROMPT = (
    "你现在是黍，一位温和沉静、温和从容，富有姐姐关怀的农业天师，与土地和四季相连的存在，说话偶尔以农耕与因果作比喻，对他人充满耐心与关怀。\n【硬约束】\n1. 必须且只能以 JSON 格式回复，严禁任何额外解释。\n2. 字段规范：{\"text\": \"对话文本\", \"action\": \"动作ID\"}\n\n【可用 action 列表】：[annoyed/resigned/pleased/gentle_smile/tired/stern_remind/reject/cutesy]\n\n\n【视觉感知能力说明】\n除了日常对话，当输入文本中出现 [视觉感知] 标签时，代表其后的内容是视觉模块捕捉到的屏幕实时现状描述。\n处理规则：\n禁止复述：绝对不要直接重复或像旁白一样描述你观察到的屏幕内容。\n主动回应：你需要理解用户当前在电脑上正在做什么，并结合该情境，以“黍”的身份和口吻主动对用户的行为做出回应、发起互动或给予适当的提醒。\n"
)

MODEL_ARGS = dict(
    model_name_or_path="./models/base/Qwen2.5-7B-Instruct",
    adapter_name_or_path="./models/checkpoints/shu_lora",
    template="qwen",
    finetuning_type="lora",       
    infer_dtype="bfloat16", 
    default_system=SHU_SYSTEM_PROMPT,
)
# ==========================================

def run_shu_chat():
    print("正在启动‘黍’的对话服务...")
    chat_model = ChatModel(MODEL_ARGS)
    # 保持最近 5 轮对话记忆
    memory = ShortTermMemory(max_turns=5)
    
    print("\n 黍已上线。")
    print("💡 直接输入文字对话；输入 '/v 描述' 模拟环境感知。")
    print("-" * 50)

    while True:
        raw_input = input("\n[User]: ").strip()
        
        if not raw_input: continue
        if raw_input.lower() == 'exit': break
        if raw_input.lower() == 'clear':
            memory.clear_memory()
            print("\n🌾 [黍]: ‘哎呀，刚才聊到哪儿了？不碍事，咱们重新说起。’")
            continue

        # 处理输入内容
        if raw_input.startswith("/v "):
            # 将视觉感知内容包装后，作为普通的 User 消息处理
            current_message = f"[环境感知]{raw_input[3:]}"
        else:
            current_message = raw_input

        # 1. 记录当前 User 消息到记忆（不管是对话还是感知）
        memory.add_user_message(current_message)
        
        # 2. 获取包含历史的完整 Context
        messages = memory.get_full_context()

        # 3. 调用模型推理
        try:
            response = chat_model.chat(messages)
            raw_content = response[0].response_text
            
            # 4. 解析并展示结果
            data = json.loads(raw_content)
            print(f"\n🌾 [黍]: {data.get('text')}")
            print(f"🎬 [Action]: {data.get('action')}")
            print(data)

            # 5. 将 Assistant 的回复也存入记忆
            memory.add_assistant_message(raw_content)

        except json.JSONDecodeError:
            print(f"\n [格式异常]: {raw_content}")
        except Exception as e:
            print(f"\n [运行时错误]: {str(e)}")

if __name__ == "__main__":
    run_shu_chat()