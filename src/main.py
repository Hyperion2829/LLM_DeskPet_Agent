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

app = FastAPI(title="明日方舟-黍 极简 4-bit 推理服务")

# 跨域配置（防止前端请求被浏览器拦截）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= 配置区 =================
MODEL_PATH = "./models/base/Qwen2.5-7B-Instruct"
ADAPTER_PATH = "./models/checkpoints/shu_lora" # 你的 LoRA 补丁路径

# 4-bit 实时量化配置 (专为本地 8G 显存优化)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

# 自动加载模型底座 + LoRA 补丁
print("⏳ 正在本地加载 4-bit 压缩版底座...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    
    device_map={"": 0}, 
    
    low_cpu_mem_usage=True 
)
print("⏳ 正在挂载‘黍’的 LoRA 补丁...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model = model.eval()
print("✅ 极简本地推理服务已就绪！")
# ==========================================

# 兼容 OpenAI 标准的请求体格式 [1.1.4]
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]] # 直接接收组员发送过来的包含系统人设与历史的完整列表 [1.1.2, 1.1.4]
    temperature: float = 0.7
    max_tokens: int = 256
    stream: bool = False

    class Config:
        extra = "allow" # 允许接收前端发来的其他额外参数

# 核心路由：兼容 OpenAI 标准的聊天完成接口 [1.1.2]
@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    print("\n📩 [DEBUG - 收到前端消息列表 (含System Prompt)]:")
    print(json.dumps(request.messages, ensure_ascii=False, indent=2))
    try:
        # 1. 直接将组员维护好的完整 messages 列表转化为 Qwen 格式的输入文本 [1.1.2, 1.1.4]
        text = tokenizer.apply_chat_template(request.messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        # 2. 推理生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                do_sample=True, 
                temperature=0.2,
                top_p=0.9,
                repetition_penalty=1.05
            )
        
        raw_content = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)

        print("\n📤 [DEBUG - 模型最原始输出]:")
        print(raw_content)
        print("="*50)
        
        # 3. 校验格式：确保返回的是标准 JSON（防止模型偶尔因上下文过长而格式微调出错）
        json.loads(raw_content)

    except json.JSONDecodeError:
        # 如果格式崩了，自动通过代码进行格式纠错救灾，确保前端不会因为解析失败而直接闪退
        raw_content = json.dumps({"text": raw_content, "action": "gentle_smile"}, ensure_ascii=False)
    except Exception as e:
        raw_content = json.dumps({"text": f"系统错误: {str(e)}", "action": "gentle_smile"}, ensure_ascii=False)

    # 4. 返回标准 OpenAI 格式的响应体，让组员的 backend.exe 能完美解包 [1.1.2]
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
                    "content": raw_content
                },
                "finish_reason": "stop"
            }
        ]
    }