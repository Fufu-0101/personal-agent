from typing import Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
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

        # Define tools
        self.tools = [get_current_time, calculate]

        # Build LangGraph agent with new API
        self.checkpointer = MemorySaver()
        self.graph = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer
        )

    async def chat(self, message: str, conversation_id: str | None = None) -> tuple[str, str]:
        """Chat with the agent and return (response, conversation_id)."""
        config = {"configurable": {"thread_id": conversation_id or "default"}}

        # Invoke the graph
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )

        # Get the last message (assistant's response)
        response_message = result["messages"][-1]
        response = response_message.content if hasattr(response_message, 'content') else str(response_message)

        return response, config["configurable"]["thread_id"]

    def get_conversation_history(self, conversation_id: str | None = None) -> Sequence[BaseMessage]:
        """Get the conversation history for a given thread."""
        config = {"configurable": {"thread_id": conversation_id or "default"}}

        # Get state from checkpointer
        state = self.graph.get_state(config)
        return state.values.get("messages", [])


# Global agent instance
agent_service = AgentService()
