from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, Message
from app.services.agent import agent_service
from datetime import datetime

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the agent."""
    try:
        response, conversation_id = await agent_service.chat(
            message=request.message,
            conversation_id=request.conversation_id
        )

        return ChatResponse(
            message=response,
            conversation_id=conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/history")
async def get_history(conversation_id: str):
    """Get conversation history."""
    try:
        messages = agent_service.get_conversation_history(conversation_id)

        # Convert to simpler format
        history = []
        for msg in messages:
            if isinstance(msg, str):
                role = "assistant"
                content = msg
            elif hasattr(msg, 'type') and msg.type == 'human':
                role = "user"
                content = msg.content if hasattr(msg, 'content') else str(msg)
            elif hasattr(msg, 'type') and msg.type == 'ai':
                role = "assistant"
                content = msg.content if hasattr(msg, 'content') else str(msg)
            else:
                # Fallback for other message types
                role = "assistant"
                content = str(msg)

            history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().timestamp()
            })

        return {"conversation_id": conversation_id, "messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
