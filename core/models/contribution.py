from pydantic import BaseModel

class ContributionIn(BaseModel):
    user_id: int
    amount: int
    rsn: str