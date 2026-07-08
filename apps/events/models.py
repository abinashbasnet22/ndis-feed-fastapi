from sqlalchemy import Column, Integer, String, Text, Boolean, ARRAY, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

class Event(Base):
    __tablename__ = "events"

    id              = Column(Integer, primary_key=True)
    url             = Column(String)
    source          = Column(String)
    title           = Column(Text)
    snippet         = Column(Text)
    body_text       = Column(Text)
    event_date_text = Column(String)
    categories      = Column(ARRAY(Text))
    links           = Column(JSONB)
    summary         = Column(Text)
    ndis_relevant   = Column(Boolean)
    full_scraped    = Column(Boolean)
    is_paywall      = Column(Boolean)
    published_at    = Column(String)
    scraped_at      = Column(String)
    created_at      = Column(TIMESTAMP(timezone=True))