"""
Personal Agent with LLM-based Intent Recognition
Hybrid Memory Architecture + Smart Intent Understanding
"""
from typing import Sequence, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import json
from app.core.config import settings


# ============ Tools ============
@tool
def get_current_time() -> str:
    """获取当前时间"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如: 2 + 2, 10 * 5"""
    try:
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


# ============ Memory Service ============
class MongoMemoryService:
    """MongoDB-based memory service"""

    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        self.client: Optional[AsyncIOMotorClient] = None
        self.connection_string = connection_string
        self._db = None
        self._conversations = None
        self._long_term = None

    async def _get_collections(self):
        if self._conversations is None:
            self.client = AsyncIOMotorClient(self.connection_string)
            self._db = self.client["agent_memory"]
            self._conversations = self._db["conversations"]
            self._long_term = self._db["long_term_memory"]

            await self._conversations.create_index([("thread_id", 1)])
            await self._conversations.create_index([("timestamp", -1)])
            await self._long_term.create_index([("thread_id", 1)])
            await self._long_term.create_index([("importance", -1)])

        return self._conversations, self._long_term

    async def save_conversation(self, thread_id: str, user_message: str, assistant_response: str):
        try:
            conversations, _ = await self._get_collections()
            doc = {
                "thread_id": thread_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "timestamp": datetime.utcnow(),
            }
            await conversations.insert_one(doc)
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def get_conversation_history(self, thread_id: str, limit: int = 20) -> list[dict]:
        try:
            conversations, _ = await self._get_collections()
            cursor = conversations.find({"thread_id": thread_id}).sort("timestamp", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return list(reversed(docs))
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def save_fact(self, thread_id: str, fact_type: str, content: str, importance: float = 0.5):
        try:
            _, long_term = await self._get_collections()
            doc = {
                "thread_id": thread_id,
                "fact_type": fact_type,
                "content": content,
                "importance": importance,
                "timestamp": datetime.utcnow(),
            }
            await long_term.update_one(
                {"thread_id": thread_id, "fact_type": fact_type, "content": content},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving fact: {e}")

    async def get_facts(self, thread_id: str, limit: int = 10) -> list[str]:
        try:
            _, long_term = await self._get_collections()
            cursor = long_term.find({"thread_id": thread_id}).sort("importance", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [doc["content"] for doc in docs]
        except Exception as e:
            print(f"Error getting facts: {e}")
            return []

    async def delete_fact(self, thread_id: str, content: str) -> bool:
        try:
            _, long_term = await self._get_collections()
            result = await long_term.delete_many({
                "thread_id": thread_id,
                "content": {"$regex": content, "$options": "i"}
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting fact: {e}")
            return False

    async def clear_all_facts(self, thread_id: str) -> int:
        try:
            _, long_term = await self._get_collections()
            result = await long_term.delete_many({"thread_id": thread_id})
            return result.deleted_count
        except Exception as e:
            print(f"Error clearing facts: {e}")
            return 0

    async def list_all_facts(self, thread_id: str) -> list[dict]:
        try:
            _, long_term = await self._get_collections()
            cursor = long_term.find({"thread_id": thread_id}).sort("importance", -1)
            docs = await cursor.to_list(length=None)
            return docs
        except Exception as e:
            print(f"Error listing facts: {e}")
            return []

    async def close(self):
        if self.client:
            self.client.close()
            self._conversations = None
            self._long_term = None


# ============ LLM Intent Recognizer ============
class IntentRecognizer:
    """Use LLM to intelligently recognize user intent"""

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

输入: "别记着我喜欢吃辣"
输出: {"intent": "delete_memory", "confidence": 0.92, "extracted_info": {"query": "喜欢吃辣", "reason": "用户要求不要记住这个偏好"}}

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
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            intent_data = json.loads(result)

            # Validate intent
            valid_intents = ["chat", "delete_memory", "view_memories", "clear_memories"]
            if intent_data.get("intent") not in valid_intents:
                intent_data["intent"] = "chat"
                intent_data["extracted_info"] = {
                    "query": "",
                    "reason": "无法识别的意图，作为普通对话处理"
                }

            return intent_data

        except Exception as e:
            print(f"LLM intent recognition failed: {e}, using keyword fallback")
            return self._keyword_fallback(user_message)

    def _keyword_fallback(self, user_message: str) -> dict:
        """Fallback to keyword matching if LLM fails"""
        message_lower = user_message.lower()

        if any(word in message_lower for word in ["忘记", "删除记忆", "不要记住", "别记着"]):
            query = user_message
            for word in ["忘记", "删除记忆", "不要记住", "别记着"]:
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

        if any(word in message_lower for word in ["查看记忆", "记忆列表", "所有记忆", "你知道什么", "你都记得什么"]):
            return {
                "intent": "view_memories",
                "confidence": 0.7,
                "extracted_info": {
                    "query": "",
                    "reason": "关键词匹配识别"
                }
            }

        if any(word in message_lower for word in ["清空记忆", "删除所有记忆", "全部忘记", "重置记忆"]):
            return {
                "intent": "clear_memories",
                "confidence": 0.7,
                "extracted_info": {
                    "query": "",
                    "reason": "关键词匹配识别"
                }
            }

        return {
            "intent": "chat",
            "confidence": 0.6,
            "extracted_info": {
                "query": "",
                "reason": "默认对话意图"
            }
        }


# ============ Agent Service ============
class AgentService:
    def __init__(self):
        # Initialize LLM (Anthropic-compatible for GLM-4.7)
        anthropic_kwargs = {
            "api_key": settings.anthropic_api_key,
            "model": settings.model_name,
            "temperature": 0.7
        }
        if settings.anthropic_base_url:
            anthropic_kwargs["base_url"] = settings.anthropic_base_url

        self.llm = ChatAnthropic(**anthropic_kwargs)

        # Store reference to memory service
        self.mongo_memory = MongoMemoryService(
            connection_string=settings.mongodb_connection_string
        )

        # Initialize intent recognizer
        self.intent_recognizer = IntentRecognizer()

        # Define tools
        self.tools = [get_current_time, calculate]

        # Layer 1: Short-term memory (in-memory checkpoint)
        self.checkpointer = MemorySaver()

        # Build LangGraph agent
        self.graph = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer
        )

    async def chat(self, message: str, conversation_id: str | None = None) -> tuple[str, str]:
        """Chat with the agent and return (response, conversation_id)."""
        config = {"configurable": {"thread_id": conversation_id or "default"}}
        thread_id = config["configurable"]["thread_id"]

        # Step 1: Use LLM to recognize intent
        intent_result = await self.intent_recognizer.recognize_intent(message)
        intent = intent_result.get("intent", "chat")
        confidence = intent_result.get("confidence", 0.5)
        extracted_info = intent_result.get("extracted_info", {})

        print(f"[DEBUG] Intent: {intent}, Confidence: {confidence}, Info: {extracted_info}")

        # Step 2: Handle memory management intents
        if intent == "delete_memory" and confidence > 0.7:
            query = extracted_info.get("query", message)
            deleted = await self.mongo_memory.delete_fact(thread_id, query)

            if deleted:
                return f"✅ 已删除关于「{query}」的记忆", thread_id
            else:
                return f"❌ 没有找到关于「{query}」的记忆", thread_id

        if intent == "view_memories" and confidence > 0.7:
            facts = await self.mongo_memory.list_all_facts(thread_id)

            if not facts:
                return "📝 当前没有任何长期记忆", thread_id

            result = "📝 我的记忆列表：\n\n"
            for i, fact in enumerate(facts, 1):
                result += f"{i}. **{fact['fact_type']}**\n"
                result += f"   {fact['content']}\n\n"

            return result.strip(), thread_id

        if intent == "clear_memories" and confidence > 0.7:
            count = await self.mongo_memory.clear_all_facts(thread_id)
            return f"✅ 已清空 {count} 条记忆", thread_id

        # Step 3: Normal conversation with memory enhancement
        facts = await self.mongo_memory.get_facts(thread_id)

        enhanced_message = message
        if facts:
            context = "\n".join([f"- {fact}" for fact in facts])
            enhanced_message = f"[用户背景信息]\n{context}\n\n[当前消息]\n{message}"

        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=enhanced_message)]},
            config=config
        )

        response_message = result["messages"][-1]
        response = response_message.content if hasattr(response_message, 'content') else str(response_message)

        await self._extract_and_save_facts(thread_id, message, response)
        await self.mongo_memory.save_conversation(thread_id, message, response)

        return response, thread_id

    async def _extract_and_save_facts(self, thread_id: str, user_message: str, assistant_response: str):
        """Extract and save important facts from conversation"""
        message_lower = user_message.lower()

        if "我叫" in user_message or "我是" in user_message:
            if "我叫" in user_message:
                name_part = user_message.split("我叫")[1].strip()
                name = name_part.split()[0] if name_part else ""
                if name:
                    await self.mongo_memory.save_fact(thread_id, "name", f"用户叫{name}", importance=0.9)

        if "喜欢" in user_message or "不爱" in user_message or "讨厌" in user_message:
            await self.mongo_memory.save_fact(thread_id, "preference", user_message, importance=0.7)

        if "记住" in user_message:
            await self.mongo_memory.save_fact(thread_id, "important_fact", user_message.replace("记住", "").strip(), importance=0.8)

    async def get_conversation_history(self, conversation_id: str | None = None) -> Sequence[BaseMessage]:
        config = {"configurable": {"thread_id": conversation_id or "default"}}
        state = self.graph.get_state(config)
        return state.values.get("messages", [])

    async def get_long_term_memory(self, conversation_id: str | None = None) -> list[str]:
        thread_id = conversation_id or "default"
        return await self.mongo_memory.get_facts(thread_id)

    async def close(self):
        await self.mongo_memory.close()


# Global agent instance
agent_service = AgentService()
