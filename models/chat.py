from datetime import datetime
from typing import List
from uuid import UUID

from openai import BaseModel
from pydantic import Field


class AIChatMessage(BaseModel):
    id: UUID
    created_at: datetime
    username: str
    message: str

class AIChatResponse(BaseModel):
    message: str = Field(description="A text message to respond with based on the previous conversation")
    is_response_required: bool = Field(description="Only 'True' if the context requires to return the message.")


class Chat(BaseModel):
    ### Metadata
    id: UUID
    created_at: datetime
    system_prompt: str
    # add more metadata ...
    
    messages: List[AIChatMessage]

    def format(self, last_n_messages: None | int = None):
        if last_n_messages is None:
            return "\n".join([
                f"###username: {m.username}\n###message: {m.message}" for m in self.messages
            ])
