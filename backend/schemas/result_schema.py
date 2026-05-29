from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID


class ResultPolicyItem(BaseModel):
    policy_id: UUID
    seq_order: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class OptimizationResultResponse(BaseModel):
    id: UUID
    total_benefit: int
    policy_count: int
    algorithm: str
    exec_ms: int
    created_at: datetime
    policies: List[ResultPolicyItem] = []

    model_config = ConfigDict(from_attributes=True)