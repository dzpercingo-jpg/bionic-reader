"""Unit tests for the ADHD-aware onboarding scorer.

We test four representative archetypes — they exercise the corners of
the profile space and map cleanly onto the four anchor presets — plus
a degenerate empty input and a self-report-only input to verify the
confidence shrinks correctly.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.onboarding import (
    AsrsAnswer,
    AssessmentRequest,
    PvtTrial,
    score_assessment,
)
from app.onboarding.models import ReadingTrial

client = TestClient(app)


def _asrs(scores: list[int]) -> list[AsrsAnswer]:
    assert len(scores) == 6
    return [AsrsAnswer(qid=f"q{i+1}", score=s) for i, s in enumerate(scores)]  # type: ignore[arg-type]


def _pvt(mean_ms: float, sd_ms: float, n: int = 20, false_starts: int = 0) -> list[PvtTrial]:
    """Synthesise a PVT trial sequence with a target mean / SD."""
    import random
    rng = random.Random(123)
    trials: list[PvtTrial] = []
    for _ in range(n):
        rt = max(120.0, rng.gauss(mean_ms, sd_ms))
        trials.append(PvtTrial(rt_ms=rt, false_start=False, lapse=rt > 500))
    for _ in range(false_starts):
        trials.append(PvtTrial(rt_ms=0.0, false_start=True, lapse=False))
    return trials


# -- Archetypes -------------------------------------------------------


def test_apaise_profile_picks_apaise() -> None:
    """Low ADHD signal, slow reader → apaise."""
    req = AssessmentRequest(
        asrs=_asrs([1, 0, 1, 0, 0, 1]),
        pvt=_pvt(mean_ms=290, sd_ms=40, false_starts=0),
        reading=ReadingTrial(word_count=60, elapsed_ms=24_000),  # 150 wpm
    )
    res = score_assessment(req)
    assert res.preset.profile == "apaise"
    assert res.profile.inattention < 50
    assert res.profile.hyperactivity < 50
    assert res.profile.confidence == 1.0


def test_concentre_profile_picks_concentre() -> None:
    """High inattention (ASRS + PVT erratic), normal HI → concentre."""
    req = AssessmentRequest(
        asrs=_asrs([4, 4, 3, 1, 1, 2]),
        pvt=_pvt(mean_ms=520, sd_ms=180, n=20, false_starts=1),
        reading=ReadingTrial(word_count=60, elapsed_ms=22_000),  # 164 wpm
    )
    res = score_assessment(req)
    assert res.preset.profile == "concentre"
    assert res.profile.inattention >= 60
    # Heavy guidance settings activated.
    assert res.preset.settings["phraseChunkingEnabled"] is True
    assert res.preset.settings["eyeAnchorEnabled"] is True


def test_sprint_profile_picks_sprint() -> None:
    """High HI + impulsive (false starts) + fast reader → sprint."""
    req = AssessmentRequest(
        asrs=_asrs([1, 1, 1, 4, 4, 4]),
        pvt=_pvt(mean_ms=240, sd_ms=35, n=20, false_starts=5),
        reading=ReadingTrial(word_count=60, elapsed_ms=10_000),  # 360 wpm
    )
    res = score_assessment(req)
    assert res.preset.profile == "sprint"
    assert res.profile.hyperactivity >= 60
    assert res.preset.settings["rsvpEnabled"] is True


def test_equilibre_profile_picks_equilibre() -> None:
    """Moderate symptoms across BOTH inattention and hyperactivity, moderate
    PVT (mean 360 ms, SD 110 ms) → equilibre.

    Note: ASRS 'Sometimes' (score=2) on every item actually maps to the
    low-symptom 'apaise' zone, not equilibre — that user reports infrequent
    symptoms and their PVT is fine. Equilibre needs symptoms reported in
    the 'Often' band on at least some items.
    """
    req = AssessmentRequest(
        asrs=_asrs([3, 2, 3, 3, 2, 3]),
        pvt=_pvt(mean_ms=370, sd_ms=110, n=20, false_starts=2),
        reading=ReadingTrial(word_count=60, elapsed_ms=16_000),  # 225 wpm
    )
    res = score_assessment(req)
    assert res.preset.profile == "equilibre", (
        f"got {res.preset.profile} with profile {res.profile.model_dump()}"
    )


# -- Confidence + graceful degradation --------------------------------


def test_empty_assessment_returns_low_confidence_profile() -> None:
    req = AssessmentRequest()
    res = score_assessment(req)
    assert 0.0 <= res.profile.confidence <= 0.5
    assert res.preset.profile in {"apaise", "equilibre", "concentre", "sprint"}


def test_asrs_only_yields_reduced_confidence() -> None:
    req = AssessmentRequest(asrs=_asrs([3, 3, 3, 2, 2, 2]))
    res = score_assessment(req)
    assert res.profile.confidence < 1.0
    # ASRS-only must still pick a sensible non-zero profile.
    assert res.profile.inattention > 0


# -- Profile weights are a valid distribution ------------------------


def test_anchor_weights_sum_to_one() -> None:
    req = AssessmentRequest(
        asrs=_asrs([2, 2, 2, 2, 2, 2]),
        pvt=_pvt(mean_ms=350, sd_ms=100),
    )
    res = score_assessment(req)
    weights = res.preset.profile_weights
    assert pytest.approx(sum(weights.values()), abs=1e-6) == 1.0
    for v in weights.values():
        assert 0.0 <= v <= 1.0


# -- Interpolated settings respect bounds -----------------------------


def test_interpolated_settings_have_valid_bounds() -> None:
    req = AssessmentRequest(
        asrs=_asrs([4, 4, 4, 4, 4, 4]),
        pvt=_pvt(mean_ms=600, sd_ms=200, false_starts=5),
        reading=ReadingTrial(word_count=60, elapsed_ms=30_000),
    )
    res = score_assessment(req)
    s = res.preset.settings
    assert 0.0 < float(s["fixationRatio"]) <= 1.0
    assert 100 <= int(s["rsvpWpm"]) <= 700
    assert 12 <= int(s["fontSize"]) <= 32


# -- Live HTTP endpoint -----------------------------------------------


def test_onboarding_endpoint_returns_assessment_result() -> None:
    payload = {
        "asrs": [{"qid": f"q{i+1}", "score": 2} for i in range(6)],
        "pvt": [{"rt_ms": 320 + i * 5, "false_start": False, "lapse": False} for i in range(15)],
        "reading": {"word_count": 60, "elapsed_ms": 18_000},
    }
    resp = client.post("/api/onboarding/score", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["preset"]["profile"] in {"apaise", "equilibre", "concentre", "sprint"}
    assert 0.0 <= body["profile"]["confidence"] <= 1.0


def test_onboarding_endpoint_rejects_extra_fields() -> None:
    payload = {"asrs": [], "pvt": [], "reading": None, "unknown_field": 1}
    resp = client.post("/api/onboarding/score", json=payload)
    # extra=forbid → 422
    assert resp.status_code == 422
