from pydantic import BaseModel, HttpUrl
from typing import List, Dict


class User(BaseModel):
    id: str
    name: str
    tools: List[str] = []
    agent_card_url: HttpUrl = ""
    knowledge: str = ""