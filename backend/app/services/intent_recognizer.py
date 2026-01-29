"""
Intent Recognition for Memory Management
Uses LLM to understand user intent intelligently
"""
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings


class IntentRecognizer:
    """Use LLM to recognize user intent"""

    def __init__(self):
        anthropic_kwargs = {
            "api_key": settings.anthropic_api_key,
            "model": settings.model_name,
            "temperature": 0.0  # Low temperature for consistent classification
        }
        if settings.anthropic_base_url:
            anthropic_kwargs["base_url"] = settings.anthropic_base_url

        self.llm = ChatAnthropic(**anthropic_kwargs)

        self.system_prompt = """你是一个意图识别助手。分析用户的输入，判断他们的意图。

可能的意图类型：
1. chat - 正常对话
2. delete_memory - 删除特定记忆
3. view_memories - 查看所有记忆
4. clear_memories - 清空所有记忆
5. save_fact - 保存重要信息

请以 JSON 格式返回，包含以下字段：
{
  "intent": "意图类型",
  "confidence": 0.0-1.0 之间的置信度,
  "extracted_info": {
    "query": "要删除/查询的关键词（如果有）",
    "reason": "判断理由"
  }
}

示例：
输入: "忘记我喜欢咖啡"
输出: {"intent": "delete_memory", "confidence": 0.95, "extracted_info": {"query": "我喜欢咖啡", "reason": "用户明确要求忘记某个偏好"}}

输入: "你都知道什么"
输出: {"intent": "view_memories", "confidence": 0.9, "extracted_info": {"query": "", "reason": "用户想查看AI知道的信息"}}

输入: "你好，今天天气怎么样"
输出: {"intent": "chat", "confidence": 0.98, "extracted_info": {"query": "", "reason": "普通问候和闲聊"}}

只返回 JSON，不要其他内容。"""

    async def recognize_intent(self, user_message: str) -> dict:
        """Recognize user intent using LLM"""
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]

            response = await self.llm.ainvoke(messages)
            result = response.content

            # Parse JSON response
            import json
            # Try to extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            intent_data = json.loads(result)

            # Validate intent
            valid_intents = ["chat", "delete_memory", "view_memories", "clear_memories", "save_fact"]
            if intent_data.get("intent") not in valid_intents:
                intent_data["intent"] = "chat"
                intent_data["extracted_info"] = {
                    "query": "",
                    "reason": "无法识别的意图，作为普通对话处理"
                }

            return intent_data

        except Exception as e:
            # Fallback to keyword matching if LLM fails
            print(f"LLM intent recognition failed: {e}, using keyword matching")
            return self._keyword_fallback(user_message)

    def _keyword_fallback(self, user_message: str) -> dict:
        """Fallback to keyword matching if LLM fails"""
        message_lower = user_message.lower()

        # Check for delete memory intent
        if any(word in message_lower for word in ["忘记", "删除记忆", "不要记住"]):
            # Extract query
            query = user_message
            for word in ["忘记", "删除记忆", "不要记住"]:
                if word in message_lower:
                    query = user_message.split(word)[1].strip()
                    break

            return {
                "intent": "delete_memory",
                "confidence": 0.7,
                "extracted_info": {
                    "query": query,
                    "reason": "关键词匹配识别"
                }
            }

        # Check for view memories intent
        if any(word in message_lower for word in ["查看记忆", "记忆列表", "所有记忆", "你知道什么", "你都记得什么"]):
            return {
                "intent": "view_memories",
                "confidence": 0.7,
                "extracted_info": {
                    "query": "",
                    "reason": "关键词匹配识别"
                }
            }

        # Check for clear memories intent
        if any(word in message_lower for word in ["清空记忆", "删除所有记忆", "全部忘记", "重置记忆"]):
            return {
                "intent": "clear_memories",
                "confidence": 0.7,
                "extracted_info": {
                    "query": "",
                    "reason": "关键词匹配识别"
                }
            }

        # Default to chat
        return {
            "intent": "chat",
            "confidence": 0.6,
            "extracted_info": {
                "query": "",
                "reason": "默认对话意图"
            }
        }
