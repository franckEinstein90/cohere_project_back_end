from pydantic import BaseModel
from typing import List, Optional, Literal


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    """Pydantic model for the /query endpoint request body.

    Fields:
      - user_prompt: the prompt string from the user
      - conversation: optional list of previous turns (role/content)
    """

    user_prompt: str
    conversation: Optional[List[ConversationTurn]] = None
