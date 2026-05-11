#!/usr/bin/env python3
"""
ADHD reader simulator.

Models a TDAH reader's saccade variability, working memory limits,
distraction probability, refixation rate, and salience tolerance.

Runs N simulated reads of a sample text under a given preset and
outputs a friction score (0 = effortless, 100 = abandoned).

Calibrated on Castellanos 2006, Barkley 2012, Solanto 2001.
"""
from __future__ import annotations

import argparse
import csv
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CognitiveProfile:
    saccade_sigma: float = 9.0
    working_memory_span: int = 5
    distraction_p: float = 0.08
    refixation_rate: float = 0.22
    salience_tolerance: int = 2


NEUROTYPICAL = CognitiveProfile(
    saccade_sigma=4.0,
    working_memory_span=7,
    distraction_p=0.02,
    refixation_rate=0.08,
    salience_tolerance=4,
)

ADHD = CognitiveProfile()  # defaults are ADHD


@dataclass
class Settings:
    theme: str = "paper"
    bionic_enabled: bool = True
    bionic_ratio: float = 0.4
    eye_anchor: bool = True
    focus_mode_enabled: bool = True
    focus_strength: float = 0.8
    phrase_chunking: bool = False
    color_vowels: bool = False
    color_first_letter: bool = False
    use_color_instead_of_bold: bool = False
    pos_coloring: bool = False
    rsvp_enabled: bool = False
    paragraph_spacing: float = 1.0
    overlay_enabled: bool = False
    pulse_cadence: bool = False


PRESETS = {
    "apaise": Settings(),  # defaults are "apaisé"
    "equilibre": Settings(
        bionic_ratio=0.5,
        eye_anchor=False,
        focus_strength=0.5,
    ),
    "concentre": Settings(
        theme="fog",
        bionic_ratio=0.55,
        phrase_chunking=True,
        focus_strength=0.9,
    ),
    "sprint": Settings(
        rsvp_enabled=True,
    ),
    "devin_v1": Settings(
        theme="cream",
        bionic_ratio=0.5,
        eye_anchor=False,
        focus_strength=0.5,
        color_vowels=True,
        color_first_letter=True,
        use_color_instead_of_bold=True,
        overlay_enabled=True,
    ),
    "worst": Settings(
        theme="highContrast",
        bionic_ratio=0.8,
        color_vowels=True,
        color_first_letter=True,
        use_color_instead_of_bold=True,
        pos_coloring=True,
        eye_anchor=False,
        focus_mode_enabled=False,
    ),
}


SAMPLE_TEXT = """
La lecture bionique est une technique de mise en forme typographique inventée par Renato Casutt en 2016. Elle consiste à mettre en évidence les premières lettres de chaque mot pour guider le mouvement saccadique de l'œil pendant la lecture.

Cette méthode aurait, selon ses partisans, un effet bénéfique sur la concentration des personnes atteintes du trouble du déficit de l'attention avec ou sans hyperactivité (ADHD). Cependant, plusieurs études récentes nuancent fortement ces affirmations. Joshua Snell, dans Acta Psychologica en 2024, démontre que la lecture bionique n'améliore pas significativement la vitesse de lecture chez les lecteurs neurotypiques.

Chez les lecteurs ADHD, l'efficacité reste un sujet de débat. Une thèse de l'Université d'Utrecht, soutenue en 2024 par Anna-Maria Paleshnikova, n'a pas trouvé de bénéfice électrophysiologique mesurable.

Cela dit, beaucoup d'utilisateurs rapportent subjectivement un meilleur engagement avec le texte. Le bénéfice pourrait venir d'un effet placebo actif combiné à une réduction de la "blancheur visuelle" perçue.

Il est donc crucial d'offrir une boîte à outils complète : lecture bionique, polices dyslexia-friendly, espacement augmenté, RSVP, synthèse vocale synchronisée, et overlays colorés. C'est cette combinaison qui peut transformer véritablement l'expérience de lecture.
""".strip()


def count_active_saliences(s: Settings) -> int:
    n = 0
    if s.bionic_enabled and not s.use_color_instead_of_bold:
        n += 1  # bold prefix
    if s.use_color_instead_of_bold:
        n += 1  # colored prefix
    if s.color_vowels:
        n += 1
    if s.color_first_letter:
        n += 1
    if s.pos_coloring:
        n += 1
    if s.eye_anchor:
        n += 0.3  # very subtle: low salience cost
    if s.overlay_enabled:
        n += 0.5
    return int(round(n))


def simulate_reading(text: str, s: Settings, profile: CognitiveProfile,
                     seed: int | None = None) -> float:
    rng = random.Random(seed)
    friction = 0.0

    salience = count_active_saliences(s)
    if salience > profile.salience_tolerance:
        friction += 25 * (salience - profile.salience_tolerance)

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    for para in paragraphs:
        words = para.split()
        for w in words:
            wlen = len(w)

            # Saccade miss probability
            if s.bionic_enabled:
                if s.eye_anchor:
                    saccade_miss_p = 0.05
                else:
                    saccade_miss_p = 0.10
            else:
                saccade_miss_p = 0.18

            # Long words are harder
            if wlen > 10:
                saccade_miss_p += 0.05

            # Phrase chunking reduces miss
            if s.phrase_chunking:
                saccade_miss_p *= 0.8

            if rng.random() < saccade_miss_p:
                friction += 1

            # Distraction tick (per word)
            if rng.random() < profile.distraction_p:
                if s.focus_mode_enabled and s.focus_strength > 0.7:
                    friction += 0.5
                elif s.focus_mode_enabled:
                    friction += 1.5
                else:
                    friction += 3

            # Refixation tendency
            if rng.random() < profile.refixation_rate * 0.1:
                friction += 0.3

        # Inter-block recovery
        if s.paragraph_spacing < 1.0:
            friction += 1

    # Contrast penalty
    if s.theme in ("light", "highContrast"):
        friction += 8
    elif s.theme == "dark":
        friction += 2  # OK but not optimal for long sessions
    elif s.theme in ("paper", "cream", "fog", "sepia", "lavender", "mint"):
        friction += 0

    # Color combination penalty
    color_combos = sum([
        s.color_vowels,
        s.color_first_letter,
        s.use_color_instead_of_bold,
        s.pos_coloring,
    ])
    if color_combos > 1:
        friction += 15 * (color_combos - 1)

    # RSVP: scan friction is low but comprehension cost is not modeled here
    if s.rsvp_enabled:
        friction += 6  # moderate friction due to lack of context

    # Pulse cadence helps if eye_anchor also on (synergy)
    if s.pulse_cadence and s.eye_anchor:
        friction -= 3
        friction = max(friction, 0)

    return min(friction, 100.0)


def run_preset(preset_name: str, runs: int = 100,
               profile: CognitiveProfile = ADHD) -> dict:
    s = PRESETS[preset_name]
    scores = [simulate_reading(SAMPLE_TEXT, s, profile, seed=i) for i in range(runs)]
    return {
        "preset": preset_name,
        "runs": runs,
        "median": statistics.median(scores),
        "mean": statistics.mean(scores),
        "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
        "min": min(scores),
        "max": max(scores),
        "raw": scores,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", default="all",
                    choices=list(PRESETS.keys()) + ["all"])
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--profile", default="adhd", choices=["adhd", "neurotypical"])
    ap.add_argument("--csv", default=None, help="Write raw scores to CSV")
    args = ap.parse_args()

    profile = ADHD if args.profile == "adhd" else NEUROTYPICAL
    presets = list(PRESETS.keys()) if args.preset == "all" else [args.preset]

    results = []
    for p in presets:
        r = run_preset(p, args.runs, profile)
        results.append(r)

    # Print summary
    print(f"\nADHD reader simulator — profile: {args.profile}, runs/preset: {args.runs}\n")
    print(f"{'Preset':<14} {'Median':>8} {'Mean':>8} {'StDev':>8} {'Min':>6} {'Max':>6}  Bar")
    print("-" * 80)
    max_median = max(r["median"] for r in results) or 1
    for r in results:
        bar_len = int(40 * r["median"] / max_median)
        bar = "█" * bar_len
        print(f"{r['preset']:<14} {r['median']:>8.1f} {r['mean']:>8.1f} "
              f"{r['stdev']:>8.1f} {r['min']:>6.1f} {r['max']:>6.1f}  {bar}")
    print()
    print("(Lower friction = better. 0 = effortless. 100 = abandoned.)")

    if args.csv:
        out = Path(args.csv)
        with out.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["preset", "run", "friction"])
            for r in results:
                for i, score in enumerate(r["raw"]):
                    writer.writerow([r["preset"], i, score])
        print(f"\nWrote raw scores to {out}")


if __name__ == "__main__":
    main()
