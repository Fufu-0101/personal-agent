from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from zhipuai import ZhipuAI
from app.core.config import settings


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


class AgentService:
    def __init__(self):
        # Initialize LLM
        if settings.llm_provider == "zhipuai":
            # Use ZhipuAI (GLM-4.7)
            self.zhipuai_client = ZhipuAI(api_key=settings.zhipuai_api_key)
            self.use_zhipuai = True
        elif settings.llm_provider == "anthropic":
            # Use Anthropic-compatible API (including GLM-4.7 via Anthropic interface)
            anthropic_kwargs = {
                "api_key": settings.anthropic_api_key,
                "model": settings.model_name,
                "temperature": 0.7
            }
            if settings.anthropic_base_url:
                anthropic_kwargs["base_url"] = settings.anthropic_base_url
            self.llm = ChatAnthropic(**anthropic_kwargs)
            self.use_zhipuai = False
        else:
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.model_name,
                temperature=0.7
            )
            self.use_zhipuai = False

        # Build LangGraph
        self.graph = self._build_graph()

        # Memory for conversation persistence
        self.checkpointer = MemorySaver()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph for the agent."""

        def call_model(state: AgentState):
            """Call the LLM with the current messages."""
            messages = state["messages"]

            if self.use_zhipuai:
                # Convert LangChain messages to ZhipuAI format
                zhipuai_messages = []
                for msg in messages:
                    if isinstance(msg, HumanMessage) or (hasattr(msg, 'type') and msg.type == 'human'):
                        zhipuai_messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage) or (hasattr(msg, 'type') and msg.type == 'ai'):
                        zhipuai_messages.append({"role": "assistant", "content": msg.content})
                    else:
                        # Fallback
                        zhipuai_messages.append({"role": "user", "content": str(msg)})

                # Call ZhipuAI
                response = self.zhipuai_client.chat.completions.create(
                    model=settings.model_name,
                    messages=zhipuai_messages,
                    temperature=0.7
                )
                response_message = response.choices[0].message
                return {"messages": [AIMessage(content=response_message.content)]}
            else:
                # Use LangChain LLM
                response = self.llm.invoke(messages)
                return {"messages": [response]}

        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", call_model)

        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)

        # Compile graph
        return workflow.compile()

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
