"""Evidence-based ADHD-aware onboarding.

This package replaces the previous purely-declarative 6-question quiz
with a hybrid objective + self-report assessment that maps a user's
multidimensional cognitive profile to a continuous bionic preset
recommendation. See `RESEARCH_GUIDED_MODE.md` for the design rationale,
the clinical literature it draws from, and the equations.
"""
from .models import (
    AsrsAnswer,
    AssessmentRequest,
    AssessmentResult,
    ProfileVector,
    PvtTrial,
    RecommendedPreset,
)
from .scoring import score_assessment

__all__ = [
    "AsrsAnswer",
    "AssessmentRequest",
    "AssessmentResult",
    "ProfileVector",
    "PvtTrial",
    "RecommendedPreset",
    "score_assessment",
]
