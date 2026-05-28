# 安装与配置指南

## 环境要求

- Windows 10 或 11
- 不需要安装 Python 或 Node.js

## 安装

1. 解压 `Mini Live2D AI-x.x.x-win.zip` 到任意目录
2. 解压后目录中包含 `Mini Live2D AI.exe`、`config.json`、`.env.template` 等文件
3. 配置 API Key（见下文）
4. 无需安装，配置完成后双击 `Mini Live2D AI.exe` 即可运行

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
    "llm_model": "deepseek-chat" // LLM 模型名
  },
  "max_history": 5,              // 对话历史轮数
  "vision": {
    "enabled": false,            // 是否启用视觉感知
    "model": "qwen-vl-plus",     // 视觉模型名
    "stable_duration": 30,       // 视觉结果稳定后持续时间，达到时间唤醒
    "handle_cooldown": 600,      // 处理视觉结果后冷却时间，单位秒
    "same_handle_cooldown": 3000,// 同一视觉结果冷却时间，单位秒
    "prompt": "简要描述用户当前正在做什么，包含必要信息，不超过100个字。", // 视觉提示词
    "max_tokens": 200            // 视觉提示词最大长度，单位 token
  },
  "system_prompt":"你现在是黍，一位温和沉静、温和从容，富有姐姐关怀的农业天师，与土地和四季相连的存在，说话偶尔以农耕与因果作比喻，对他人充满耐心与关怀。\n【硬约束】\n1. 必须且只能以 JSON 格式回复，严禁任何额外解释。\n2. 字段规范：{\"text\": \"对话文本\", \"action\": \"动作ID\"}\n\n【可用 action 列表】：[annoyed/resigned/pleased/gentle_smile/tired/stern_remind/reject/cutesy]\n\n\n【视觉感知能力说明】\n除了日常对话，当输入文本中出现 [视觉感知] 标签时，代表其后的内容是视觉模块捕捉到的屏幕实时现状描述。\n处理规则：\n禁止复述：绝对不要直接重复或像旁白一样描述你观察到的屏幕内容。\n主动回应：你需要理解用户当前在电脑上正在做什么，并结合该情境，以“黍”的身份和口吻主动对用户的行为做出回应、发起互动或给予适当的提醒。\n" // 系统提示词，指导 AI 角色的行为和对话风格，需要保留 json 字段规范和动作列表
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

### 启动后窗口报错

确认 `.env` 文件中 `DEEPSEEK_API_KEY` 已填写且正确。

### 启动后 live2d 模型不显示

网络问题，关闭代理或 VPN 后重新启动应用。

### 打开 `backend.exe` 收到报错

正常现象无需处理，正常情况下用户不需要单独打开。启动 `Mini Live2D AI.exe` 时自动运行 `backend.exe`。

### 发送消息后显示"连接后端失败"

后端进程可能未正常启动。尝试：
1. 退出应用（托盘右键 → 退出）
2. 重新启动 `Mini Live2D AI.exe`

### .env 文件放在哪

在解压目录下，与 `Mini Live2D AI.exe` 同级。

### 如何更换 Live2D 模型

替换 `resources/frontend/live2d-models/` 目录下的模型文件，然后修改 `config.json` 中 `model.path` 指向新模型的 `.model3.json` 文件。注意更改可用动作列表。目前版本可能在部分代码中硬编码，所以直接替换模型可能出现问题，后续如果有时间会进行优化。

### 如何卸载

1. 托盘右键退出应用/右键角色选择退出
2. 删除解压目录
