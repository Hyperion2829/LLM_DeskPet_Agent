from collections import deque

class ShortTermMemory:
    def __init__(self, max_turns=5):
        """
        初始化记忆模块
        :param system_prompt: 黍的人设和JSON规则
        :param max_turns: 记忆的最大轮数（一问一答为一轮）
        """
        # 使用双端队列，自动处理过期记忆（一问一答各占一个元素，所以长度 * 2）
        self.history = deque(maxlen=max_turns * 2)

    def add_user_message(self, content):
        """记录用户的输入"""
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        """记录模型的JSON回复（直接存入原始字符串）"""
        self.history.append({"role": "assistant", "content": content})

    def get_full_context(self):
        
        return list(self.history)

    def clear_memory(self):
        """清空记忆（比如用户点击了‘重置会话’）"""
        self.history.clear()