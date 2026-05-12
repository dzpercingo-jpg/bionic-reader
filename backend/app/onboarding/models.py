"""Pydantic models for the onboarding assessment.

The full request body sent by the frontend after the user completes
all stages of the assessment. All fields are validated at the API
boundary and any missing block degrades gracefully (we still score
with reduced confidence rather than refusing the request).

References:
- ASRS-v1.1 6-item screener (Kessler et al., WHO, 2005)
- PVT — Psychomotor Vigilance Task (Dinges & Powell, 1985)
- DSM-5 ADHD presentations (American Psychiatric Association, 2013)
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------- Stage 1: ASRS-v1.1 self-report ---------------------------

#: ASRS Likert (Kessler et al., 2005) maps Never/Rarely/Sometimes/Often/Very Often → 0..4
AsrsScore = Literal[0, 1, 2, 3, 4]

#: Six ASRS-v1.1 question IDs (Part A — the validated screener).
#: q1–q3 load on inattention; q4–q6 load on hyperactivity-impulsivity.
AsrsQid = Literal["q1", "q2", "q3", "q4", "q5", "q6"]


class AsrsAnswer(BaseModel):
    """One answer in the ASRS-v1.1 6-item screener."""

    qid: AsrsQid
    score: AsrsScore


# ---------- Stage 2: Psychomotor Vigilance Task -----------------------


class PvtTrial(BaseModel):
    """One trial of the Psychomotor Vigilance Task.

    `rt_ms` is the response time in milliseconds. `false_start=True`
    means the user responded before the stimulus appeared (impulsivity
    marker). `lapse=True` is derived (rt_ms > 500ms) but kept explicit
    so the frontend can transmit its own classification consistently.
    """

    rt_ms: float = Field(..., ge=0, le=5000)
    false_start: bool = False
    lapse: bool = False


# ---------- Stage 3: reading-speed calibration ------------------------


class ReadingTrial(BaseModel):
    """A single reading-speed trial: time to read N words once."""

    word_count: int = Field(..., ge=20, le=400)
    elapsed_ms: float = Field(..., ge=2000, le=600_000)
    comprehension_correct: int = Field(0, ge=0, le=10)
    comprehension_total: int = Field(0, ge=0, le=10)


# ---------- Aggregated request ----------------------------------------


class AssessmentRequest(BaseModel):
    """Full payload sent at the end of the assessment."""

    model_config = ConfigDict(extra="forbid")

    asrs: list[AsrsAnswer] = Field(default_factory=list)
    pvt: list[PvtTrial] = Field(default_factory=list)
    reading: ReadingTrial | None = None
    # Optional user-provided metadata for transparency. Not used by the
    # scorer; the frontend echoes age/locale here for analytics.
    locale: str | None = None


# ---------- Output models ---------------------------------------------


class ProfileVector(BaseModel):
    """Continuous, multidimensional cognitive profile.

    All four scores are normalised to 0–100. They're NOT a diagnosis —
    they're a calibration vector used to pick reading-aid parameters.
    """

    inattention: float = Field(..., ge=0, le=100)
    hyperactivity: float = Field(..., ge=0, le=100)
    reading_speed_wpm: float = Field(..., ge=0, le=900)
    consistency: float = Field(
        ..., ge=0, le=100,
        description="Higher = lower RT variability on PVT (more attentional consistency).",
    )
    # Confidence: shrinks if some stages were skipped.
    confidence: float = Field(..., ge=0, le=1)


class RecommendedPreset(BaseModel):
    """The bionic preset settings recommended for this user.

    `profile` is one of the 4 anchor presets used by the frontend
    store as a label; `settings` contains the (possibly interpolated)
    actual values to apply, so the frontend can pull either form.
    """

    profile: Literal["apaise", "equilibre", "concentre", "sprint"]
    rationale: str
    settings: dict[str, float | int | bool | str]
    profile_weights: dict[str, float]


class AssessmentResult(BaseModel):
    profile: ProfileVector
    preset: RecommendedPreset
