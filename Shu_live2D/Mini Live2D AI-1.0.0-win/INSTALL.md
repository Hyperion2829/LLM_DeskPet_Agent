# 安装与配置指南

## 环境要求

- Windows 10 或 11
- 不需要安装 Python 或 Node.js

## 安装

1. 解压 `Mini Live2D AI-x.x.x-win.zip` 到任意目录
2. 解压后目录中包含 `Mini Live2D AI.exe`、`config.json`、`.env.template` 等文件
3. 无需安装，配置完成后双击 `Mini Live2D AI.exe` 即可运行

## 配置 API Key

应用需要 LLM 服务才能对话，默认使用 DeepSeek。

### 1. 创建 .env 文件

将安装目录下的 `.env.template` 复制一份，改名为 `.env`：

```
安装目录/
├── .env.template   ← 复制这个
└── .env            ← 重命名为这个，然后编辑
```

### 2. 填写 API Key

用文本编辑器（记事本即可）打开 `.env`，填入你的 Key：

```ini
# LLM 配置（必需，否则无法对话）
DEEPSEEK_API_KEY=sk-你的key

# DeepSeek 官方 API 地址，一般不用改
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 视觉模型配置（可选，不填请禁用视觉感知）
DASHSCOPE_API_KEY=sk-你的key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 获取 API Key

| 服务 | 用途 | 获取地址 |
|------|------|---------|
| DeepSeek | 文本对话（必需） | https://platform.deepseek.com/api_keys |
| DashScope | 视觉感知（可选） | https://dashscope.console.aliyun.com/apiKey |

DashScope（通义千问）的模型有免费试用额度。

### 3. 编辑 config.json（可选）

`config.json` 包含所有可调参数，用文本编辑器打开即可修改。

**常用调整项**：

```json
{
  "api": {
    "llm_model": "deepseek-chat"  // LLM 模型名
  },
  "vision": {
    "enabled": false,           // 是否启用视觉感知
    "stable_duration": 30,      // 视觉结果稳定后持续时间，达到时间唤醒
    "handle_cooldown": 600,     // 处理视觉结果后冷却时间，单位秒
    "same_handle_cooldown": 3000,// 同一视觉结果冷却时间，单位秒
    "prompt": "简要描述用户当前正在做什么，包含必要信息，不超过100个字。", // 视觉提示词
    "max_tokens": 200 // 视觉提示词最大长度，单位 token
  }
}
```

完整参数见 `config.json` 内容，改完重启应用生效。

## 使用

### 基本操作

1. 双击 `Mini Live2D AI.exe` 启动
2. 角色会出现在屏幕右下角，悬浮在其他窗口之上
3. 点击底部输入框，输入文字，按 Enter 或点击"发送"
4. AI 回复以气泡形式显示，角色会播放对应动作

### 右键菜单

在窗口上右键点击：

| 选项 | 功能 |
|------|------|
| 显示历史 | 查看最近的对话记录 |
| 视觉感知 | 开关屏幕感知功能（需要配置 DashScope Key） |
| 退出 | 关闭应用 |

### 托盘图标

- **左键**：显示/隐藏角色窗口
- **右键**：显示/隐藏、退出

窗口最小化后应用仍在托盘运行，不会占用任务栏。

### 视觉感知

启用后，角色会检测你当前正在使用的软件窗口，并用 AI 视觉模型识别屏幕内容，主动与你搭话。

## 常见问题

### 启动后窗口空白或报错

确认 `.env` 文件中 `DEEPSEEK_API_KEY` 已填写且正确。

### 发送消息后显示"连接后端失败"

后端进程可能未正常启动。尝试：
1. 退出应用（托盘右键 → 退出）
2. 重新启动 `Mini Live2D AI.exe`

### .env 文件在哪

在解压目录下，与 `Mini Live2D AI.exe` 同级。

### 角色不说话/没反应

1. 检查 `.env` 中 API Key 是否正确
2. 检查 DeepSeek 账户余额/额度是否用完

### 如何更换 Live2D 模型

替换 `resources/frontend/live2d-models/` 目录下的模型文件，然后修改 `config.json` 中 `model.path` 指向新模型的 `.model3.json` 文件。注意更改可用动作列表。目前版本可能在部分代码中硬编码，需要自行调整。

### 如何卸载

1. 托盘右键退出应用/右键角色选择退出
2. 直接删除解压目录即可（无注册表、无残留）
