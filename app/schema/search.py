from pydantic import BaseModel


class SearchPrompt(BaseModel):
    prompt: str


class SearchResponse(BaseModel):
    contract_title: str
    customer_name: str
    contract_value: int
    currancy_type: str
    question: str
    answer: str
