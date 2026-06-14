from __future__ import annotations

from datetime import date
from uuid import UUID
from schemas.profile_schema import UserProfileRequest

from pydantic import BaseModel, ConfigDict, computed_field


class PolicyIntervalResponse(BaseModel):
    policy_id: UUID
    title: str
    category: str
    benefit_start: date
    benefit_end: date
    total_benefit: int
    monthly_benefit: int
    duration_months: int
    situational_condition: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoadmapPhaseResponse(BaseModel):
    label: str
    phase_start: date
    phase_end: date
    total_benefit: int
    policies: list[PolicyIntervalResponse]

    @computed_field
    @property
    def policy_count(self) -> int:
        return len(self.policies)


class TransitionResponse(BaseModel):
    from_policy: str
    to_policy: str


class RoadmapResponse(BaseModel):
    phases: list[RoadmapPhaseResponse]
    transitions: list[TransitionResponse]
    total_benefit: int
    total_months: int

    @computed_field
    @property
    def phase_count(self) -> int:
        return len(self.phases)

    @classmethod
    def from_roadmap(cls, roadmap) -> RoadmapResponse:
        phases = [
            RoadmapPhaseResponse(
                label=ph.label,
                phase_start=ph.phase_start,
                phase_end=ph.phase_end,
                total_benefit=ph.total_benefit,
                policies=[
                    PolicyIntervalResponse(
                        policy_id=iv.policy_id,
                        title=iv.title,
                        category=iv.category,
                        benefit_start=iv.benefit_start,
                        benefit_end=iv.benefit_end,
                        total_benefit=iv.total_benefit,
                        monthly_benefit=iv.monthly_benefit,
                        duration_months=iv.duration_months,
                        situational_condition=iv.situational_condition, 
                    )
                    for iv in ph.policies
                ],
            )
            for ph in roadmap.phases
        ]
        transitions = [
            TransitionResponse(from_policy=f, to_policy=t)
            for f, t in roadmap.transitions
        ]
        return cls(
            phases=phases,
            transitions=transitions,
            total_benefit=roadmap.total_benefit,
            total_months=roadmap.total_months,
        )
    
class RoadmapRequest(BaseModel):
    profile: UserProfileRequest
    selected_policy_ids: list[UUID] = []    
