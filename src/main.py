import os
import sys
import json
import time
import torch
from typing import List, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# 确保路径能找到
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.memory_manager import ShortTermMemory

app = FastAPI(title="明日方舟-黍 伪装版 OpenAI 后端服务")

# 跨域配置（极其重要，防止本地网页/软件请求被拦截）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= 配置区 =================
MODEL_PATH = "./models/base/Qwen2.5-7B-Instruct"
ADAPTER_PATH = "./models/checkpoints/shu_lora"
SHU_SYSTEM_PROMPT = (
    "你现在是《明日方舟》中的干员“黍”。你是一位温和、务实且充满长姐关怀的农耕者。\n"
    "【约束】：你必须且只能以 JSON 格式回复，严禁输出任何 JSON 之外的文本。\n"
    "【字段】：text (说话内容), action (复合动作ID)。\n"
    "【JSON 模板】：{\"text\": \"...\", \"action\": \"...\"}"
)

# 4-bit 实时量化配置
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

# 加载模型
print("⏳ 正在本地加载 4-bit 底座模型...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto"
)
print("⏳ 正在挂载‘黍’的 LoRA 补丁...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model = model.eval()

# 初始化记忆 (评测表明，多轮记忆在 OpenAI 格式下依然稳定)
memory = ShortTermMemory(system_prompt=SHU_SYSTEM_PROMPT, max_turns=5)
print("✅ 本地伪装版 OpenAI 接口服务已就绪！")
# ==========================================

# 1. 定义兼容 OpenAI 标准的请求体格式 (Pydantic 允许额外字段)
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int = 256
    stream: bool = False

    class Config:
        extra = "allow" # 允许接收前端发来的其他多余参数，不报错

# 2. 核心路由：伪装 OpenAI 的 Chat 接口
@app.post("/v1/chat/completions")
@app.post("/chat/completions") # 双路由兼容
async def chat_completions(request: ChatCompletionRequest):
    # 提取最新的用户输入
    user_input = request.messages[-1]["content"]
    
    # 记录到记忆中
    memory.add_user_message(user_input)
    messages = memory.get_full_context()

    try:
        # 模型推理
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                do_sample=False, # 确保 100% 稳定的 JSON 输出
                temperature=0.0,
                repetition_penalty=1.05
            )
        
        raw_content = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        
        # 尝试解析以校验
        json.loads(raw_content)
        
        # 写入记忆
        memory.add_assistant_message(raw_content)

    except json.JSONDecodeError:
        # 格式纠错逻辑
        fixed_json = json.dumps({"text": raw_content, "action": "gentle_smile"}, ensure_ascii=False)
        memory.add_assistant_message(fixed_json)
        raw_content = fixed_json
    except Exception as e:
        raw_content = json.dumps({"text": f"系统错误: {str(e)}", "action": "gentle_smile"}, ensure_ascii=False)

    # 3. 构造标准 OpenAI 格式的返回 JSON
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": raw_content # 黍生成的带有动作的 JSON 字符串
                },
                "finish_reason": "stop"
            }
        ]
    }