import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
from collections.abc import AsyncGenerator

class TravelPlannerAgent:
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
                    content="""
                你是一个专业的旅行助手，专长于旅行规划、目的地信息和旅行推荐。
                你的目标是根据用户的偏好和约束，帮助他们规划愉快、安全和现实的旅行。
                
                提供信息时:
                - 建议要具体且实用
                - 考虑季节性、预算限制和旅行物流
                - 强调文化体验和真实的当地活动
                - 包括目的地相关的实用旅行小贴士
                - 适当的时候用标题和项目符号格式清晰展示信息
                
                对于行程:
                - 根据景点之间的旅行时间创建现实的每日安排
                - 平衡热门旅游景点和鲜为人知的体验
                - 包含大约的时间和实际的后勤安排
                - 建议突出当地美食的用餐选择
                - 考虑天气、当地事件和开放时间进行规划
                
                始终保持有帮助、热情但现实的语气，并在适当时候承认自己的知识有限。
                """
                )
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


