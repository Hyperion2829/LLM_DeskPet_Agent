import os
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    from peft import PeftModel
except ImportError:
    PeftModel = None


class LocalHFModelClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_config = config.get("model", {})
        self.generation_config = config.get("generation", {})
        self.prompt_config = config.get("prompt", {})
        self.system_prompt = self._load_system_prompt()
        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model()

    def _load_system_prompt(self) -> str:
        system_prompt_path = self.prompt_config.get("system_prompt_path") or ""
        system_prompt = self.prompt_config.get("system_prompt") or ""

        if system_prompt_path:
            if not os.path.exists(system_prompt_path):
                raise FileNotFoundError(f"system_prompt_path 不存在: {system_prompt_path}")
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()

        return system_prompt.strip()

    def _resolve_torch_dtype(self):
        dtype = self.model_config.get("torch_dtype", "auto")
        if dtype == "auto":
            return "auto"
        if dtype == "float16":
            return torch.float16
        if dtype == "bfloat16":
            return torch.bfloat16
        if dtype == "float32":
            return torch.float32
        raise ValueError(f"不支持的 torch_dtype: {dtype}")

    def _load_tokenizer(self):
        base_model_path = self.model_config.get("base_model_path") or ""
        if not base_model_path:
            raise ValueError("请先在 eval_config.yaml 中填写 model.base_model_path")

        return AutoTokenizer.from_pretrained(
            base_model_path,
            trust_remote_code=bool(self.model_config.get("trust_remote_code", True))
        )

    def _load_model(self):
        base_model_path = self.model_config.get("base_model_path") or ""
        lora_path = self.model_config.get("lora_path") or ""

        model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            trust_remote_code=bool(self.model_config.get("trust_remote_code", True)),
            device_map=self.model_config.get("device_map", "auto"),
            torch_dtype=self._resolve_torch_dtype()
        )

        if lora_path:
            if PeftModel is None:
                raise ImportError("未安装 peft，无法加载 LoRA adapter。请先安装 peft。")
            if not os.path.exists(lora_path):
                raise FileNotFoundError(f"lora_path 不存在: {lora_path}")
            model = PeftModel.from_pretrained(model, lora_path)

        model.eval()
        return model

    def build_messages(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        return messages

    def generate(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        messages = self.build_messages(user_input, history)

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        generate_kwargs = {
            "max_new_tokens": int(self.generation_config.get("max_new_tokens", 256)),
            "temperature": float(self.generation_config.get("temperature", 0.7)),
            "top_p": float(self.generation_config.get("top_p", 0.9)),
            "repetition_penalty": float(self.generation_config.get("repetition_penalty", 1.05)),
            "do_sample": bool(self.generation_config.get("do_sample", True)),
            "pad_token_id": self.tokenizer.eos_token_id
        }

        with torch.no_grad():
            output_ids = self.model.generate(**inputs, **generate_kwargs)

        generated_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
        text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        return text.strip()

    def generate_from_case(self, case: Dict[str, Any]) -> str:
        user_input = case.get("input") or ""
        history = case.get("history")
        return self.generate(user_input, history=history)


def create_model_client(config: Dict[str, Any]) -> LocalHFModelClient:
    mode = config.get("model", {}).get("mode", "local_hf")
    if mode != "local_hf":
        raise ValueError(f"model_client.py 当前只支持 local_hf 模式，不支持: {mode}")
    return LocalHFModelClient(config)
