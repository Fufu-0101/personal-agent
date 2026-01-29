"""
Hybrid Memory Architecture for Personal Agent with Memory Management
"""
from typing import Sequence, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
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
    """MongoDB-based memory service with management capabilities"""

    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        self.client: Optional[AsyncIOMotorClient] = None
        self.connection_string = connection_string
        self._db = None
        self._conversations = None
        self._long_term = None

    async def _get_collections(self):
        """Lazy initialization of MongoDB connection"""
        if self._conversations is None:
            self.client = AsyncIOMotorClient(self.connection_string)
            self._db = self.client["agent_memory"]
            self._conversations = self._db["conversations"]
            self._long_term = self._db["long_term_memory"]

            # Create indexes
            await self._conversations.create_index([("thread_id", 1)])
            await self._conversations.create_index([("timestamp", -1)])
            await self._long_term.create_index([("thread_id", 1)])
            await self._long_term.create_index([("importance", -1)])

        return self._conversations, self._long_term

    async def save_conversation(
        self,
        thread_id: str,
        user_message: str,
        assistant_response: str
    ):
        """Save conversation to MongoDB"""
        try:
            conversations, long_term = await self._get_collections()

            doc = {
                "thread_id": thread_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "timestamp": datetime.utcnow(),
            }

            await conversations.insert_one(doc)
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def get_conversation_history(
        self,
        thread_id: str,
        limit: int = 20
    ) -> list[dict]:
        """Get conversation history from MongoDB"""
        try:
            conversations, _ = await self._get_collections()

            cursor = conversations.find(
                {"thread_id": thread_id}
            ).sort("timestamp", -1).limit(limit)

            docs = await cursor.to_list(length=limit)

            # Return in chronological order
            return list(reversed(docs))
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def save_fact(
        self,
        thread_id: str,
        fact_type: str,
        content: str,
        importance: float = 0.5
    ):
        """Save an important fact to long-term memory"""
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
        """Retrieve important facts for a thread"""
        try:
            _, long_term = await self._get_collections()

            cursor = long_term.find(
                {"thread_id": thread_id}
            ).sort("importance", -1).limit(limit)

            docs = await cursor.to_list(length=limit)

            return [doc["content"] for doc in docs]
        except Exception as e:
            print(f"Error getting facts: {e}")
            return []

    async def delete_fact(
        self,
        thread_id: str,
        content: str
    ) -> bool:
        """Delete a specific fact from long-term memory"""
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
        """Clear all facts for a thread"""
        try:
            _, long_term = await self._get_collections()

            result = await long_term.delete_many({"thread_id": thread_id})
            return result.deleted_count
        except Exception as e:
            print(f"Error clearing facts: {e}")
            return 0

    async def search_facts(
        self,
        thread_id: str,
        keyword: str
    ) -> list[dict]:
        """Search facts by keyword"""
        try:
            _, long_term = await self._get_collections()

            cursor = long_term.find({
                "thread_id": thread_id,
                "content": {"$regex": keyword, "$options": "i"}
            })

            docs = await cursor.to_list(length=None)
            return docs
        except Exception as e:
            print(f"Error searching facts: {e}")
            return []

    async def list_all_facts(self, thread_id: str) -> list[dict]:
        """List all facts with details"""
        try:
            _, long_term = await self._get_collections()

            cursor = long_term.find({"thread_id": thread_id}).sort("importance", -1)
            docs = await cursor.to_list(length=None)

            return docs
        except Exception as e:
            print(f"Error listing facts: {e}")
            return []

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self._conversations = None
            self._long_term = None


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

        # Store reference to memory service for tools
        self.mongo_memory = MongoMemoryService(
            connection_string=settings.mongodb_connection_string
        )

        # Define tools with memory management
        async def forget_memory(query: str) -> str:
            """删除记忆：告诉 AI 忘记某件事。例如：忘记我喜欢咖啡"""
            try:
                deleted = await self.mongo_memory.delete_fact(
                    "default",
                    query
                )

                if deleted:
                    return f"✅ 已删除关于「{query}」的记忆"
                else:
                    return f"❌ 没有找到关于「{query}」的记忆"
            except Exception as e:
                return f"❌ 删除记忆时出错：{str(e)}"

        async def list_memories() -> str:
            """查看所有记忆"""
            try:
                facts = await self.mongo_memory.list_all_facts("default")

                if not facts:
                    return "📝 当前没有任何长期记忆"

                result = "📝 我的记忆列表：\n\n"
                for i, fact in enumerate(facts, 1):
                    result += f"{i}. **{fact['fact_type']}** (重要性: {fact['importance']})\n"
                    result += f"   {fact['content']}\n"
                    result += f"   时间: {fact['timestamp'].strftime('%Y-%m-%d %H:%M')}\n\n"

                return result.strip()
            except Exception as e:
                return f"❌ 查看记忆时出错：{str(e)}"

        async def clear_all_memories() -> str:
            """清空所有记忆（慎用）"""
            try:
                count = await self.mongo_memory.clear_all_facts("default")
                return f"✅ 已清空 {count} 条记忆"
            except Exception as e:
                return f"❌ 清空记忆时出错：{str(e)}"

        # Convert async functions to tools
        # Note: LangGraph tools need to be sync, so we'll handle this differently
        self.tools = [get_current_time, calculate]

        # Layer 1: Short-term memory (in-memory checkpoint)
        self.checkpointer = MemorySaver()

        # Build LangGraph agent
        self.graph = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer
        )

    async def chat(
        self,
        message: str,
        conversation_id: str | None = None
    ) -> tuple[str, str]:
        """Chat with the agent and return (response, conversation_id)."""
        config = {"configurable": {"thread_id": conversation_id or "default"}}
        thread_id = config["configurable"]["thread_id"]

        # Check for memory management commands
        message_lower = message.lower()

        # Handle "忘记 X" command
        if message_lower.startswith("忘记") or message_lower.startswith("删除记忆"):
            query = message.replace("忘记", "").replace("删除记忆", "").strip()
            deleted = await self.mongo_memory.delete_fact(thread_id, query)

            if deleted:
                return f"✅ 已删除关于「{query}」的记忆", thread_id
            else:
                return f"❌ 没有找到关于「{query}」的记忆", thread_id

        # Handle "查看记忆" command
        if "查看记忆" in message or "记忆列表" in message or "所有记忆" in message:
            facts = await self.mongo_memory.list_all_facts(thread_id)

            if not facts:
                return "📝 当前没有任何长期记忆", thread_id

            result = "📝 我的记忆列表：\n\n"
            for i, fact in enumerate(facts, 1):
                result += f"{i}. **{fact['fact_type']}**\n"
                result += f"   {fact['content']}\n\n"

            return result.strip(), thread_id

        # Handle "清空记忆" command
        if "清空记忆" in message or "删除所有记忆" in message:
            count = await self.mongo_memory.clear_all_facts(thread_id)
            return f"✅ 已清空 {count} 条记忆", thread_id

        # Normal conversation
        # Retrieve long-term memory context
        facts = await self.mongo_memory.get_facts(thread_id)

        # Enhance message with long-term memory context
        enhanced_message = message
        if facts:
            context = "\n".join([f"- {fact}" for fact in facts])
            enhanced_message = f"[用户背景信息]\n{context}\n\n[当前消息]\n{message}"

        # Invoke the graph
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=enhanced_message)]},
            config=config
        )

        # Get the last message (assistant's response)
        response_message = result["messages"][-1]
        response = response_message.content if hasattr(response_message, 'content') else str(response_message)

        # Extract and save important facts
        await self._extract_and_save_facts(thread_id, message, response)

        # Save conversation to MongoDB (mid-term memory)
        await self.mongo_memory.save_conversation(thread_id, message, response)

        return response, thread_id

    async def _extract_and_save_facts(
        self,
        thread_id: str,
        user_message: str,
        assistant_response: str
    ):
        """Extract and save important facts from conversation"""
        # Simple keyword-based extraction (can be improved with LLM)
        message_lower = user_message.lower()

        # Detect name
        if "我叫" in user_message or "我是" in user_message:
            if "我叫" in user_message:
                name_part = user_message.split("我叫")[1].strip()
                name = name_part.split()[0] if name_part else ""
                if name:
                    await self.mongo_memory.save_fact(
                        thread_id,
                        "name",
                        f"用户叫{name}",
                        importance=0.9
                    )

        # Detect preferences
        if "喜欢" in user_message or "不爱" in user_message or "讨厌" in user_message:
            await self.mongo_memory.save_fact(
                thread_id,
                "preference",
                user_message,
                importance=0.7
            )

        # Detect important events
        if "记住" in user_message:
            await self.mongo_memory.save_fact(
                thread_id,
                "important_fact",
                user_message.replace("记住", "").strip(),
                importance=0.8
            )

    async def get_conversation_history(
        self,
        conversation_id: str | None = None
    ) -> Sequence[BaseMessage]:
        """Get the conversation history for a given thread."""
        config = {"configurable": {"thread_id": conversation_id or "default"}}

        # Get state from in-memory checkpointer
        state = self.graph.get_state(config)
        return state.values.get("messages", [])

    async def get_long_term_memory(
        self,
        conversation_id: str | None = None
    ) -> list[str]:
        """Get long-term memory facts for a thread"""
        thread_id = conversation_id or "default"
        return await self.mongo_memory.get_facts(thread_id)

    async def close(self):
        """Close MongoDB connections"""
        await self.mongo_memory.close()


# Global agent instance
agent_service = AgentService()
