import os
import json
import time
from tqdm import tqdm
from openai import OpenAI

client = OpenAI(
    api_key="sk-e3fa02093040436381bba733c0d33b0d", # 替换你的API KEY
    base_url="https://api.deepseek.com"
)

# 原始视觉感知种子库
view_pool = [
    # ===== tired =====
    ("时间显示已经很晚了，屏幕上是追了很久的连续剧", "tired"),
    ("桌面堆着资料，屏幕停在未完成的任务界面，用户长时间没有操作", "tired"),
    ("长篇的PDF文献打开着，但页面停留在第一页已经很久了", "tired"),
    ("满屏的Excel表格数据，各种图表交织在一起，显得非常繁杂", "tired"),
    ("鼠标在桌面上毫无目的地框选图标，一遍又一遍", "tired"),

    # ===== annoyed =====
    ("桌面上充满了各种窗口，其中与学习有关的窗口已经许久没有操作而待机", "annoyed"),
    ("电脑上多个窗口来回切换，包括工作相关的窗口和动画窗口", "annoyed"),

    # ===== resigned =====
    ("任务界面打开着，但长时间没有输入，光标静静闪烁", "resigned"),
    ("文档停在一半，页面没有继续编辑的痕迹，用户没有动作", "resigned"),
    ("IDE编辑器里满屏都是红色的报错代码，光标停留在第一行", "resigned"),
    ("画图软件的画布上只有几根凌乱的草稿线条", "resigned"),
    ("屏幕停留在社交软件的列表页，没有点开任何对话", "resigned"),
    ("游戏界面显示‘游戏失败’的结算画面，战绩有些惨淡", "resigned"),
    ("输入框里打了一半的话被删除，只剩空白", "resigned"),

    # ===== pleased =====
    ("屏幕上显示任务完成提示，界面整洁，没有未处理事项", "pleased"),
    ("文件已经保存关闭，桌面恢复干净，只剩几个常用窗口", "pleased"),
    ("清空待办事项后的干净桌面，只有一个回收站的图标", "pleased"),
    ("屏幕停留在机票或酒店的预订界面，似乎在规划旅行", "pleased"),

    # ===== gentle_smile =====
    ("电脑处于空闲状态，用户随意浏览页面", "gentle_smile"),
    ("桌面干净，只有一个窗口打开，页面停留在轻松内容上", "gentle_smile"),
    ("聊天窗口打开，但没有新消息，界面显得安静", "gentle_smile"),
    ("视频播放界面暂停，进度条停在中间，用户似乎离开了", "gentle_smile"),
    ("屏幕亮起又熄灭，没有任何新通知", "gentle_smile"),

    # ===== stern_remind =====
    ("屏幕显示时间已是凌晨，任务列表却几乎未完成", "stern_remind"),
    ("学习界面打开着，但还有许多娱乐应用", "stern_remind"),
    ("凌晨三点，电脑上依然亮着大型游戏的激烈战斗画面", "stern_remind"),

    # ===== cutesy =====
    ("聊天界面打开，光标停在输入框里，像是在等人回应", "cutesy"),
    ("停在对话窗口，界面干净没有其他干扰", "cutesy"),
    ("正在播放一段非常可爱的萌宠视频，画面很温馨", "cutesy"),

    # ===== 混合/自由发挥 =====
    ("打开着论文文档，但页面只写了开头", None),
    ("屏幕停留在无关页面", None),
    ("网课视频暂停在中间，笔记本空白没有记录内容", None),
    ("实验数据表打开着，但数据混乱没有整理", None),
    ("PPT制作界面空白，只有标题栏被填写", None),
    ("社交软件停留在列表页，没有点开任何对话", None)
]

mega_views = []
MULTIPLY_FACTOR = 20 # 放大 10 倍

print(f"🚀 开始视觉种子裂变！预计将 {len(view_pool)} 条数据裂变为 {len(view_pool) * MULTIPLY_FACTOR} 条...")

for text, action in tqdm(view_pool, desc="裂变进度"):
    action_desc = action if action else "中性/自由发挥"
    
    prompt = f"""
    我有一个原始的【电脑/手机屏幕画面描述】：
    "{text}" (该画面对应的用户状态/情绪是：{action_desc})
    
    请帮我发散思维，写出 {MULTIPLY_FACTOR} 个状态相近，但【软件、操作、具体画面细节完全不同】的新画面描述。
    要求：
    1. 必须是纯客观的视觉描述，描述屏幕上静态的一瞬间（不要带有主观评价）。
    2. 语言简练真实，字数在10-30字之间。
    3. 严格输出一个纯 JSON 格式的字符串数组（只包含句子，不需要包含标签）。
    示例：["新画面描述1", "新画面描述2", "新画面描述3"]
    """
    
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )
        content = resp.choices[0].message.content.replace("```json","").replace("```","")
        new_sentences = json.loads(content)
        
        if isinstance(new_sentences, list):
            for sentence in new_sentences:
                if isinstance(sentence, str):
                    mega_views.append([sentence, action])
        else:
            raise ValueError("输出的不是列表")
            
    except Exception as e:
        # 如果大模型偶尔没按格式输出，保留原句保底
        mega_views.append([text, action])
    time.sleep(0.3)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
save_path = os.path.join(BASE_DIR, "mega_view_inputs.json")

with open(save_path, "w", encoding="utf-8") as f:
    json.dump(mega_views, f, ensure_ascii=False, indent=2)

print(f"🎉 裂变完成！已生成 {len(mega_views)} 条海量视觉种子，保存在 mega_view_inputs.json")