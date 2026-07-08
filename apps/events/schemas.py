from pydantic import BaseModel
from typing import Optional, List

class EventSchema(BaseModel):
    id:              int
    title:           Optional[str]
    source:          Optional[str]
    snippet:         Optional[str]
    summary:         Optional[str]
    event_date_text: Optional[str]
    published_at:    Optional[str]
    categories:      Optional[List[str]]
    url:             Optional[str]
    is_paywall:      Optional[bool]

    model_config = {"from_attributes": True}


# ── infinite scroll response ─────────────────────────────────────────
class EventsResponse(BaseModel):
    items:       List[EventSchema]
    next_cursor: Optional[int] = None
    has_more:    bool