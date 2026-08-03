from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, TIMESTAMP  , DateTime
from core.database import Base
from sqlalchemy.dialects.postgresql import ARRAY

class News(Base):
    __tablename__ = "news"

    id                  = Column(Integer, primary_key=True)
    url                 = Column(String)
    source              = Column(String)
    item_type           = Column(String)
    title               = Column(Text)
    snippet             = Column(Text)
    read_time           =Column(String)
    author              = Column(String)
    published_at        = Column(String)
    ndis_relevant       = Column(Boolean)
    published_at        = Column(String) 
    published_date      =Column(String)
    summary             = Column(Text)
    categories          = Column(ARRAY(Text))
    links               = Column(JSON)
    created_at          = Column(TIMESTAMP(timezone=True))
    image_filename  = Column(String, nullable=True)
    image_topic     = Column(String, nullable=True)


class NewsAnalytics(Base):
    __tablename__ = "news_analytics"

    id                       = Column(Integer, primary_key=True)
    news_id                  = Column(Integer)
    headline                 = Column(Text)
    keywords                 = Column(ARRAY(Text))
    impactness               = Column(Integer)
    urgency                  = Column(String)
    sentiment_overall        = Column(String)
    sentiment_positive_pct   = Column(Integer)
    sentiment_neutral_pct    = Column(Integer)
    sentiment_negative_pct   = Column(Integer)
    sentiment_aspect_notes   = Column(Text) 
    action_required          = Column(Boolean)
    action_summary           = Column(Text)
    action_deadline          = Column(String)
    target_audience          = Column(ARRAY(Text))
    affected_states          = Column(ARRAY(Text))
    primary_filter           = Column(ARRAY(Text))
    secondary_filter         = Column(ARRAY(Text))
    key_element_type         = Column(String)
    key_element_old_value    = Column(Text)
    key_element_new_value    = Column(Text)
    key_element_description  = Column(Text)
    key_element_effective_date = Column(Text)
    key_element_financial_impact = Column(Text)
    key_element_geographic_scope = Column(Text)

    created_at               = Column(TIMESTAMP(timezone=True))


class StockPhoto(Base):
    __tablename__ = "stock_photos"

    id          = Column(Integer, primary_key=True)
    topic       = Column(String, index=True)
    filename    = Column(String)
    used_count  = Column(Integer, default=0)