import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
from collections.abc import AsyncGenerator

class DialogueHealingAgent:
    """ DialogueHealingAgent."""

    def __init__(self):
        """初始化对话模型"""
        try:
            with open("config.json") as f:
                config = json.load(f)
            self.model = ChatOpenAI(
                model=config["model_name"],
                base_url=config["base_url"],
                api_key=config["api_key"],
                temperature=0.7  # 控制生成随机性（0-2，越大越随机）
            )
        except FileNotFoundError:
            print("错误：找不到配置文件 config.json")
            exit()
        except KeyError as e:
            print(f"配置文件缺少必要字段：{e}")
            exit()

    async def stream(self, query: str) -> AsyncGenerator[str, None]:

        """流式返回大模型的响应给客户端."""
        try:
            # 初始化对话历史（可添加系统消息）
            messages = [
                SystemMessage(
                    content="你是一位专业的情感助手，善于倾听和理解他人的情绪。"
                            "请以温暖、耐心的态度与用户交流，帮助他们缓解压力、解决困扰。"
                            "在交谈中多使用共情语句，引导用户表达内心感受，并给予适当的安慰和建议。")
            ]

            # 添加用户消息到历史
            messages.append(HumanMessage(content=query))

            # 流式调用模型生成回复
            for chunk in self.model.stream(messages):
                # 返回文本内容块
                if hasattr(chunk, 'content') and chunk.content:
                    yield  {'content': chunk.content, 'done': False}
            yield {'content': '\n', 'done': True}

        except Exception as e:
            print(f"发生错误：{str(e)}")
            yield "对不起，处理您的请求时发生了错误。"


