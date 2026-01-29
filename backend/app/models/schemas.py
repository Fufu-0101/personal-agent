from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: float


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    message_count: int
    last_updated: float
