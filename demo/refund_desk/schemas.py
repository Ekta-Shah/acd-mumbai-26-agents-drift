from pydantic import BaseModel


class Handoff(BaseModel):
    """Structured handoff: every field is required, so the next agent cannot lose the amount or the delivery age."""
    amount_inr: int
    delivery_age_days: int
    window_days: int
    summary: str
