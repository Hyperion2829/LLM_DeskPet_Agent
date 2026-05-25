# download_local.py
# 本地模型高速下载脚本
import os
from modelscope import snapshot_download

# 定义本地保存的路径
MODEL_ID = 'qwen/Qwen2.5-7B-Instruct'
LOCAL_DIR = os.path.abspath("./models/base/Qwen2.5-7B-Instruct")

if not os.path.exists(LOCAL_DIR):
    os.makedirs(LOCAL_DIR)

print("====================================================")
print(f"🚀 开始从魔搭 (ModelScope) 极速下载 14G 底座模型...")
print(f"📍 本地存储路径: {LOCAL_DIR}")
print("====================================================")

try:
    # 调用魔搭官方下载接口，自动处理断点续传和校验
    path = snapshot_download(
        MODEL_ID,
        local_dir=LOCAL_DIR,
        ignore_file_pattern=[r'\.git/', r'\.gitattributes']
    )
    print("\n" + "="*50)
    print("🎉 Qwen2.5 14G 完整底座已成功下载至本地电脑！")
    print(f"📂 存储路径: {path}")
    print("="*50)
except Exception as e:
    print(f"\n❌ 下载失败，原因: {e}")
    print("提示：请确保网络连接通畅，并在终端重新运行 'python download_local.py'。")