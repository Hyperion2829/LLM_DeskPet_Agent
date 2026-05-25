#!/bin/bash

MODEL_ID="qwen/Qwen2.5-7B-Instruct"
TARGET_DIR="./models/base/Qwen2.5-7B-Instruct"

# 确保目录存在
mkdir -p $TARGET_DIR

echo " 开始断点续传下载..."

# 循环重试，直到下载成功
# modelscope download 成功会返回 0，失败返回非 0
while true; do
    # 清理损坏的临时文件夹（这是校验失败的元凶）
    rm -rf $TARGET_DIR/._____temp
    
    echo "------------------------------------------"
    modelscope download --model $MODEL_ID --local_dir $TARGET_DIR
    
    if [ $? -eq 0 ]; then
        echo "✅ [SUCCESS] 模型下载完成且校验通过！"
        break
    else
        echo "❌ [ERROR] 下载中断或校验失败，10秒后自动重试..."
        sleep 10
    fi
done