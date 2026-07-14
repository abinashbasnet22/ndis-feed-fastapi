from pydantic import BaseModel, model_validator
from typing import Optional, List, Any


class NewsSchema(BaseModel):
    id:            int
    title:         Optional[str]
    source:        Optional[str]
    snippet:       Optional[str]
    summary:       Optional[str]
    author:        Optional[str]
    published_at:  Optional[str]
    published_date: Optional[str]
    categories:    Optional[List[str]]
    url:           Optional[str]
    item_type:     Optional[str]

    model_config = {"from_attributes": True}


class SentimentSchema(BaseModel):
    overall:      Optional[str]
    positive_pct: Optional[int]
    neutral_pct:  Optional[int]
    negative_pct: Optional[int]


class KeyElementSchema(BaseModel):
    type:              Optional[str]
    description:       Optional[str]
    effective_date:    Optional[str]
    old_value:         Optional[str]
    new_value:         Optional[str]
    financial_impact:  Optional[str]
    geographic_scope:  Optional[str]


class KeywordNewsItem(BaseModel):
    id:                       int
    headline:                 Optional[str]
    snippet:                  Optional[str]
    published_date:           Optional[str]
    time_ago:                 Optional[str]
    sentiment_overall:        Optional[str]
    sentiment_positive_pct:   Optional[int]
    sentiment_negative_pct:   Optional[int]
    sentiment_neutral_pct:    Optional[int]
    keywords:                 Optional[List[str]]
    urgency:                  Optional[str]
    impactness:               Optional[int]
    url:                      Optional[str]

    model_config = {"from_attributes": True}    


class NewsAnalyticsSchema(BaseModel):
    id:                 int
    news_id:            Optional[int]
    headline:           Optional[str]
    keywords:           Optional[List[str]]
    impactness:         Optional[int]
    urgency:            Optional[str]
    sentiment:          Optional[SentimentSchema] = None
    action_required:    Optional[bool]
    action_summary:     Optional[str]
    action_deadline:    Optional[str]
    target_audience:    Optional[List[str]]
    affected_states:    Optional[List[str]]
    primary_filter:     Optional[List[str]]
    secondary_filter:   Optional[List[str]]
    key_element:        Optional[KeyElementSchema] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def nest_flat_fields(cls, data: Any):
        if data is None:
            return None

        # works whether `data` is the raw ORM object or a plain dict
        if isinstance(data, dict):
            get = data.get
        else:
            get = lambda k, default=None: getattr(data, k, default)

        return {
            "id":               get("id"),
            "news_id":          get("news_id"),
            "headline":         get("headline"),
            "keywords":         get("keywords"),
            "impactness":       get("impactness"),
            "urgency":          get("urgency"),
            "sentiment": {
                "overall":      get("sentiment_overall"),
                "positive_pct": get("sentiment_positive_pct"),
                "neutral_pct":  get("sentiment_neutral_pct"),
                "negative_pct": get("sentiment_negative_pct"),
            },
            "action_required":  get("action_required"),
            "action_summary":   get("action_summary"),
            "action_deadline":  get("action_deadline"),
            "target_audience":  get("target_audience"),
            "affected_states":  get("affected_states"),
            "primary_filter":   get("primary_filter"),
            "secondary_filter": get("secondary_filter"),
            "key_element": {
                "type":             get("key_element_type"),
                "description":      get("key_element_description"),
                "effective_date":   get("key_element_effective_date"),
                "old_value":        get("key_element_old_value"),
                "new_value":        get("key_element_new_value"),
                "financial_impact": get("key_element_financial_impact"),
                "geographic_scope": get("key_element_geographic_scope"),
            },
        }


class NewsFeedItem(BaseModel):
    news:       NewsSchema
    analytics:  Optional[NewsAnalyticsSchema] = None
    time_ago:   Optional[str] = None


class FeedResponse(BaseModel):
    items:       List[NewsFeedItem]
    next_cursor: Optional[int] = None
    has_more:    bool




class KeywordFeedResponse(BaseModel):
    keyword:     str
    items:       List[KeywordNewsItem]
    next_cursor: Optional[int] = None
    has_more:    bool