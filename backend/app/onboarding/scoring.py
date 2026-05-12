"""Scoring algorithm — ASRS + PVT + reading-speed → profile vector → preset.

All maths is intentionally tractable and documented inline so it can be
critiqued: every coefficient is either taken from a citable reference
(ASRS-v1.1, PVT cutoffs) or marked clearly as a design choice.

The output is a 4-dimensional profile (inattention, hyperactivity,
reading_speed_wpm, consistency) plus a confidence score that shrinks if
the user skipped a stage. The profile is then projected onto the four
anchor presets used by the rest of the app — `apaise`, `equilibre`,
`concentre`, `sprint` — using inverse-distance weighting in profile
space. The winning preset's label is returned alongside an interpolated
settings dict so the frontend can either snap to the anchor or apply
the interpolated values directly.
"""
from __future__ import annotations

import math
import statistics
from collections.abc import Iterable

from .models import (
    AsrsAnswer,
    AssessmentRequest,
    AssessmentResult,
    ProfileVector,
    PvtTrial,
    ReadingTrial,
    RecommendedPreset,
)

# ---------- Stage scoring helpers -------------------------------------


def _score_asrs(asrs: list[AsrsAnswer]) -> tuple[float, float, float]:
    """ASRS-v1.1 → (inattention_self, hyperactivity_self, weight).

    q1-q3 → inattention; q4-q6 → hyperactivity-impulsivity. Each Likert
    item is 0..4. We average within each group and scale to 0..100.

    The third return value is a 0..1 weight: 1.0 if all 6 items were
    answered, scaled down proportionally otherwise.
    """
    if not asrs:
        return 0.0, 0.0, 0.0

    by_qid: dict[str, int] = {a.qid: a.score for a in asrs}
    inattention_items = [by_qid.get(q) for q in ("q1", "q2", "q3")]
    hi_items = [by_qid.get(q) for q in ("q4", "q5", "q6")]

    def _mean_pct(items: list[int | None]) -> float:
        nums = [x for x in items if x is not None]
        if not nums:
            return 0.0
        return (sum(nums) / len(nums)) / 4.0 * 100.0

    weight = (len([x for x in inattention_items + hi_items if x is not None])) / 6.0
    return _mean_pct(inattention_items), _mean_pct(hi_items), weight


def _score_pvt(trials: list[PvtTrial]) -> tuple[float, float, float, float]:
    """PVT → (objective_inattention, objective_hyperactivity, consistency, weight).

    Robust PVT markers per Dinges & Powell (1985) and Lim & Dinges (2008):
    - **Mean RT** rises with inattention/fatigue.
    - **RT standard deviation** (intraindividual variability) is *the*
      most reliable behavioural marker of ADHD. Higher = worse.
    - **Lapse rate** (proportion of trials with RT > 500 ms) ≥ 0.10 is
      considered clinically meaningful in adult ADHD samples.
    - **False start rate** (response before stimulus) loads on
      impulsivity / hyperactivity.

    We clip and rescale each to 0..100. Weight is the proportion of
    valid trials (∈ {0, 1}) up to a max of 1.0 at ≥ 15 trials.
    """
    valid = [t for t in trials if not t.false_start and t.rt_ms > 100]
    if not valid:
        return 0.0, 0.0, 50.0, 0.0

    rts = [t.rt_ms for t in valid]
    mean_rt = statistics.mean(rts)
    sd_rt = statistics.pstdev(rts) if len(rts) > 1 else 0.0
    lapse_rate = sum(1 for t in valid if t.rt_ms > 500) / len(valid)
    false_start_rate = sum(1 for t in trials if t.false_start) / max(1, len(trials))

    # Inattention objective score:
    #   - Mean RT: 250 ms (excellent) → 0 ; 600 ms (poor) → 100
    #   - SD RT  : 30 ms (consistent) → 0 ; 200 ms (erratic) → 100
    #   - Lapse rate: 0 → 0 ; 0.30 → 100
    # Equal weights (1/3 each) after clipping.
    score_meanrt = _clip01((mean_rt - 250) / 350)
    score_sd = _clip01((sd_rt - 30) / 170)
    score_lapse = _clip01(lapse_rate / 0.30)
    obj_inattention = (score_meanrt + score_sd + score_lapse) / 3.0 * 100.0

    # Hyperactivity / impulsivity objective score: false-start rate.
    # 0 → 0 ; 0.20 → 100. (Healthy adult average ≈ 0.02-0.05.)
    obj_hyperactivity = _clip01(false_start_rate / 0.20) * 100.0

    # Consistency: inverse of SD RT, rescaled.
    consistency = (1 - _clip01((sd_rt - 30) / 170)) * 100.0

    weight = min(1.0, len(valid) / 15.0)
    return obj_inattention, obj_hyperactivity, consistency, weight


def _score_reading(trial: ReadingTrial | None) -> tuple[float, float]:
    """Reading-speed trial → (wpm, weight). 0..900 wpm; weight ∈ {0, 1}."""
    if trial is None or trial.elapsed_ms <= 0 or trial.word_count <= 0:
        return 220.0, 0.0  # neutral default
    wpm = (trial.word_count / (trial.elapsed_ms / 1000.0)) * 60.0
    return float(max(40.0, min(900.0, wpm))), 1.0


# ---------- Profile composition ---------------------------------------


def _compose_profile(
    asrs_inatt: float, asrs_hi: float, asrs_w: float,
    pvt_inatt: float, pvt_hi: float, pvt_cons: float, pvt_w: float,
    wpm: float, reading_w: float,
) -> ProfileVector:
    """Blend self-report + behavioural scores into a single profile.

    Self-report is weighted 0.4 / behavioural 0.6 — the user's own
    perception matters, but the goal is to be **objective**, so the
    behavioural signal dominates when both are present. If either is
    missing, the other is used at full weight.

    Confidence shrinks if any stage was skipped:
      - all 3 stages → 1.0
      - 2 stages     → 0.7
      - 1 stage      → 0.4
      - 0 stages     → 0.1
    """
    # Combined inattention/hyperactivity with fall-through if one stage missing.
    inatt = _blend(asrs_inatt, asrs_w, pvt_inatt, pvt_w, self_weight=0.4, beh_weight=0.6)
    hi = _blend(asrs_hi, asrs_w, pvt_hi, pvt_w, self_weight=0.4, beh_weight=0.6)
    cons = pvt_cons if pvt_w > 0 else 60.0
    n_stages = sum(1 for w in (asrs_w, pvt_w, reading_w) if w > 0)
    confidence = {0: 0.1, 1: 0.4, 2: 0.7, 3: 1.0}[n_stages]
    return ProfileVector(
        inattention=inatt,
        hyperactivity=hi,
        reading_speed_wpm=wpm,
        consistency=cons,
        confidence=confidence,
    )


def _blend(
    self_score: float, self_w: float,
    beh_score: float, beh_w: float,
    self_weight: float = 0.4, beh_weight: float = 0.6,
) -> float:
    """Weighted blend with graceful fall-through when one source is missing."""
    if self_w == 0 and beh_w == 0:
        return 0.0
    if self_w == 0:
        return beh_score
    if beh_w == 0:
        return self_score
    return self_score * self_weight + beh_score * beh_weight


# ---------- Profile → preset mapping ----------------------------------

#: Anchor profiles in the same 4-dimensional space. Each represents the
#: kind of user the matching preset is optimised for. Chosen so the
#: four corners are spread out enough that distances are meaningful.
ANCHORS: dict[str, dict[str, float]] = {
    "apaise":    {"inattention": 30, "hyperactivity": 20, "wpm": 160, "consistency": 85},
    "equilibre": {"inattention": 45, "hyperactivity": 45, "wpm": 220, "consistency": 80},
    "concentre": {"inattention": 80, "hyperactivity": 35, "wpm": 200, "consistency": 45},
    "sprint":    {"inattention": 30, "hyperactivity": 75, "wpm": 320, "consistency": 70},
}

#: Settings at each anchor. Frontend `PRESETS` mirrors this exactly so
#: snapping back-to-front is symmetric.
ANCHOR_SETTINGS: dict[str, dict[str, float | int | bool | str]] = {
    "apaise": {
        "theme": "paper",
        "bionicEnabled": True,
        "fixationRatio": 0.35,
        "minWordLength": 4,
        "fontSize": 19,
        "lineHeight": 1.85,
        "saccadeAdaptive": True,
        "eyeAnchorEnabled": False,
        "phraseChunkingEnabled": False,
        "posColoringEnabled": False,
        "guidedPulseEnabled": False,
        "rsvpEnabled": False,
        "rsvpWpm": 160,
    },
    "equilibre": {
        "theme": "paper",
        "bionicEnabled": True,
        "fixationRatio": 0.45,
        "minWordLength": 4,
        "fontSize": 18,
        "lineHeight": 1.75,
        "saccadeAdaptive": True,
        "eyeAnchorEnabled": True,
        "phraseChunkingEnabled": False,
        "posColoringEnabled": False,
        "guidedPulseEnabled": True,
        "rsvpEnabled": False,
        "rsvpWpm": 220,
    },
    "concentre": {
        "theme": "paper",
        "bionicEnabled": True,
        "fixationRatio": 0.5,
        "minWordLength": 3,
        "fontSize": 19,
        "lineHeight": 1.9,
        "saccadeAdaptive": True,
        "eyeAnchorEnabled": True,
        "phraseChunkingEnabled": True,
        "posColoringEnabled": True,
        "guidedPulseEnabled": True,
        "rsvpEnabled": False,
        "rsvpWpm": 180,
    },
    "sprint": {
        "theme": "paper",
        "bionicEnabled": True,
        "fixationRatio": 0.5,
        "minWordLength": 3,
        "fontSize": 22,
        "lineHeight": 1.7,
        "saccadeAdaptive": False,
        "eyeAnchorEnabled": False,
        "phraseChunkingEnabled": False,
        "posColoringEnabled": False,
        "guidedPulseEnabled": False,
        "rsvpEnabled": True,
        "rsvpWpm": 350,
    },
}


#: Distance-metric weights per dimension. Inattention and hyperactivity
#: are the primary clinical axes and get double weight. Consistency is
#: a soft modifier that nudges between presets at the margins.
_DIM_WEIGHTS = {"inattention": 2.0, "hyperactivity": 2.0, "wpm": 1.0, "consistency": 0.5}


def _anchor_weights(profile: ProfileVector) -> dict[str, float]:
    """Inverse-distance weighting of the four anchors in normalized space.

    Distance uses per-dimension weights (`_DIM_WEIGHTS`) so the primary
    symptom axes (inattention / hyperactivity) dominate over the
    secondary 'reading speed' and 'consistency' axes — a person whose
    ASRS reports symptoms but happens to have stable RTs should still
    be routed to a high-guidance preset, not pulled toward `apaise` by
    consistency alone.
    """
    p = {
        "inattention": profile.inattention / 100.0,
        "hyperactivity": profile.hyperactivity / 100.0,
        "wpm": profile.reading_speed_wpm / 400.0,
        "consistency": profile.consistency / 100.0,
    }
    weights: dict[str, float] = {}
    for name, a in ANCHORS.items():
        ap = {
            "inattention": a["inattention"] / 100.0,
            "hyperactivity": a["hyperactivity"] / 100.0,
            "wpm": a["wpm"] / 400.0,
            "consistency": a["consistency"] / 100.0,
        }
        d = math.sqrt(sum(_DIM_WEIGHTS[k] * (p[k] - ap[k]) ** 2 for k in _DIM_WEIGHTS))
        weights[name] = 1.0 / (0.05 + d)  # 0.05 floor avoids div-by-zero
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def _interpolate_settings(
    weights: dict[str, float], winner: str,
) -> dict[str, float | int | bool | str]:
    """Numeric anchor settings interpolate; bool/str snap to the winner.

    Booleans (e.g. `rsvpEnabled`, `phraseChunkingEnabled`) and strings
    (e.g. `theme`) need crisp behaviour — a partially-on RSVP doesn't
    make sense — so they snap to the picked profile's anchor value.
    Numeric values (`fixationRatio`, `fontSize`, `rsvpWpm`,
    `lineHeight`) blend smoothly across anchors.
    """
    out: dict[str, float | int | bool | str] = {}
    keys = list(ANCHOR_SETTINGS["apaise"].keys())
    for k in keys:
        anchor_values = {a: ANCHOR_SETTINGS[a][k] for a in ANCHORS}
        winner_value = anchor_values[winner]
        if isinstance(winner_value, bool):
            out[k] = winner_value
        elif isinstance(winner_value, str):
            out[k] = winner_value
        else:
            blended = sum(weights[a] * float(anchor_values[a]) for a in ANCHORS)
            if isinstance(winner_value, int) and not isinstance(winner_value, bool):
                out[k] = int(round(blended))
            else:
                out[k] = round(blended, 3)
    return out


def _pick_profile(weights: dict[str, float]) -> str:
    return max(weights.items(), key=lambda kv: kv[1])[0]


def _rationale(profile: ProfileVector, label: str) -> str:
    bits: list[str] = []
    if profile.inattention >= 60:
        bits.append("signaux d'attention difficile à soutenir")
    if profile.hyperactivity >= 60:
        bits.append("préférence pour un rythme rapide")
    if profile.reading_speed_wpm >= 280:
        bits.append("lecture rapide mesurée")
    if profile.consistency >= 70:
        bits.append("temps de réaction stable")
    if not bits:
        bits.append("profil équilibré")

    why = {
        "apaise": "longueur des fixations augmentée pour réduire la fatigue",
        "equilibre": "ratio bionique modéré et chunking phrase léger",
        "concentre": "guidage saccade fort, ancrage visuel, chunking phrase",
        "sprint": "RSVP rapide pour maintenir l'engagement",
    }[label]
    return f"Détecté : {', '.join(bits)}. Réglage suggéré : {why}."


# ---------- Public API ------------------------------------------------


def score_assessment(req: AssessmentRequest) -> AssessmentResult:
    """End-to-end scoring of one assessment submission."""
    asrs_i, asrs_h, asrs_w = _score_asrs(req.asrs)
    pvt_i, pvt_h, pvt_c, pvt_w = _score_pvt(req.pvt)
    wpm, reading_w = _score_reading(req.reading)

    profile = _compose_profile(
        asrs_i, asrs_h, asrs_w,
        pvt_i, pvt_h, pvt_c, pvt_w,
        wpm, reading_w,
    )
    weights = _anchor_weights(profile)
    label = _pick_profile(weights)
    settings = _interpolate_settings(weights, label)

    return AssessmentResult(
        profile=profile,
        preset=RecommendedPreset(
            profile=label,  # type: ignore[arg-type]
            rationale=_rationale(profile, label),
            settings=settings,
            profile_weights=weights,
        ),
    )


# ---------- Utility ---------------------------------------------------


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _safe_mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return statistics.mean(xs) if xs else 0.0
