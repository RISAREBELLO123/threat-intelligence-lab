from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union

class StixLike(BaseModel):
    # canonical IOC value used for dedup/correlation
    indicator: str = Field("", title="IOC (canonical)")
    
    # coarse classification: ipv4|ipv6|domain|url|sha256|sha1|md5|email|asn|cve|cpe|other
    indicator_type: str = ""
    
    # time fields allow recency windows and decay functions downstream
    first_seen: Optional[str] = None  # ISO8601
    last_seen: Optional[str] = None   # ISO8601
    
    # light trust
    confidence: Optional[str] = None
    risk_score: Optional[float] = None
    
    # human context and links
    labels: List[str] = []
    references: List[str] = []
    desc: Optional[str] = None
    
    # provenance and lineage for audits
    source: str = ""
    source_event_id: Optional[Union[str, int]] = None
    raw_sha256: Optional[str] = None
    extra: Dict[str, Any] = {}
    
    # relationship placeholders
    attack_ids: List[str] = []
    cve_ids: List[str] = []
    cwe_ids: List[str] = []
    
    @field_validator('confidence', mode='before')
    @classmethod
    def convert_confidence_to_string(cls, v):
        """Convert numeric confidence values to strings"""
        if v is None:
            return None
        return str(v)
    
    class Config:
        extra = "ignore"