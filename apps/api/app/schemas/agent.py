from pydantic import BaseModel


class AgentExecuteRequest(BaseModel):
    provider: str
    service: str
    action: str
    params: dict = {}
