from __future__ import annotations
from typing import Dict, Any
from .cache import get as cache_get, put as cache_put

def enrich_mock(enricher_key: str, indicator: str, indicator_type: str) -> dict | None:
    """
    Mock enricher that returns fake data for testing.
    In real deployment, this would call an actual API.
    """
    # Check cache first
    cached = cache_get(enricher_key, indicator_type, indicator)
    if cached is not None:
        return {k:v for k,v in cached.items() if not k.startswith("_")}
    
    # Generate mock data
    mock_data = {
        "reputation": 75,
        "categories": ["test", "mock"],
        "asn": "AS12345",
        "geo": {"country": "US"},
        "last_seen_online": "2025-10-01T12:00:00Z"
    }
    
    # Cache it
    cache_put(enricher_key, indicator_type, indicator, {"result": mock_data, "raw": mock_data})
    
    return mock_data