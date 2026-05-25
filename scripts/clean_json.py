import json
import re

file_path = "data/sft/test_shu.json"

def process_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        # 先用文本模式读取，干掉那些真正阴险的不可见控制字符
        content = f.read()
        # 仅替换零宽空格、特殊控制符等（不碰全角标点）
        content = re.sub(r'[\u200b-\u200d\uFEFF]', '', content)
    
    try:
        data = json.loads(content)
        with open(file_path, 'w', encoding='utf-8') as f:
            # 这里的 ensure_ascii=False 是关键，它会保留你那些珍贵的全角标点
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 深度清洗完成（已保留全角标点）：{file_path}")
    except Exception as e:
        print(f"❌ JSON 解析失败，说明你的全角字符用错位置了（可能用在结构符上了）: {e}")

if __name__ == "__main__":
    process_json(file_path)