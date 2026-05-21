# Guided mode — calibration scientifique TDAH

> Document de conception du **mode guidé v2** : pourquoi le quiz
> précédent était insuffisant, quelles bases scientifiques nous avons
> retenues, comment fonctionne le nouveau scoring, et quels arbitrages
> de design ont été faits.
>
> Ce mode n'est **pas un test diagnostique**. C'est un outil de
> calibration des paramètres de lecture (taille, gras, vitesse RSVP,
> ancrage visuel…) qui s'appuie sur des instruments cliniques validés
> et des tâches comportementales pour produire une recommandation plus
> objective qu'un simple questionnaire de préférences.

---

## 1. Pourquoi refondre le mode guidé ?

Le quiz v1 (`OnboardingQuiz.tsx`) posait 6 questions purement
déclaratives ("tu préfères un fond doux ou un fond gris froid ?",
"quelle est ta durée de session ?"). Trois problèmes :

1. **Auto-évaluation faible chez les TDAH.** Le TDAH altère la
   méta-cognition (Barkley 2012, Knouse & Mitchell 2015) : le patient
   sous-estime ses symptômes et hésite entre les options, ce que le
   user nous a explicitement signalé.
2. **Pas de mesure objective.** Toutes les questions reposaient sur la
   perception du moment ("tu décroches souvent ?") sans aucune
   évidence comportementale.
3. **Mapping arbitraire vers les presets.** Chaque réponse contribuait
   à un vecteur 4-dim choisi à la main, sans grille d'évaluation
   citable.

Le mode guidé v2 corrige ces trois points en combinant **3 sources de
signal** (auto-rapport validé + tâche comportementale + mesure directe
de lecture) et un scoring documenté.

---

## 2. Le TDAH adulte — ce que la littérature dit

### 2.1 Sous-types DSM-5

Le DSM-5 (APA 2013) reconnaît trois **présentations** du TDAH adulte :

| Présentation | Symptômes dominants | Implication pour la lecture |
|---|---|---|
| **Inattentive** | distraction, perte du fil, oubli, lenteur d'exécution | a besoin d'**ancrage visuel fort** (gras prononcé, chunking phrase, focus mode) |
| **Hyperactive-impulsive** | agitation, impatience, décisions rapides | a besoin de **rythme imposé** (RSVP, pulse) pour rester engagé |
| **Combinée** | les deux | profil hybride |

Ces présentations ne sont pas catégoriques : la littérature récente
(Willcutt et al. 2012, Sjöwall et al. 2013) montre qu'elles forment un
**continuum bidimensionnel** (axe inattention × axe
hyperactivité-impulsivité). C'est exactement pour ça que notre profil
final est un **vecteur 4-dimensionnel** (inattention, hyperactivité,
vitesse, régularité) et pas une étiquette unique.

### 2.2 ASRS-v1.1 (l'instrument retenu)

L'**Adult ADHD Self-Report Scale v1.1** (Kessler et al., WHO, 2005)
est le screener auto-rapporté le plus utilisé en clinique adulte. Sa
**Partie A — 6 questions** a été optimisée par régression logistique
pour maximiser la sensibilité (~68 %) et la spécificité (~99 %)
contre le diagnostic clinique sur l'échantillon validation (N = 154).
C'est aussi l'instrument que l'OMS recommande pour le grand public.

- **q1–q3** chargent sur l'axe **inattention** (concentration,
  organisation, oubli).
- **q4–q6** chargent sur l'axe **hyperactivité-impulsivité**
  (procrastination, agitation, mouvement, "monté sur ressort").
- Chaque item est une échelle de Likert 5 points (Jamais → Très
  souvent), codée 0..4.

Le score brut ASRS n'est pas en soi un diagnostic. La grille OMS
demande un sous-ensemble d'items au-dessus d'un seuil pour parler de
"screening positif" — mais nous, on n'en a pas besoin : on traite
chaque item comme un **signal continu** qui contribue à notre vecteur
inattention/hyperactivité.

### 2.3 Tâches comportementales validées

Il existe un consensus sur les tâches comportementales qui distinguent
le TDAH adulte des contrôles, par ordre de robustesse :

1. **Variabilité du temps de réaction (RT-SD)** — le marqueur le plus
   reproductible (Klein et al. 2006, Kofler et al. 2013). L'écart-type
   du temps de réponse mesure directement la *régularité* de
   l'attention, plus que la *vitesse moyenne*.
2. **Psychomotor Vigilance Task (PVT)** — Dinges & Powell 1985 ; Lim
   & Dinges 2008. Apparition imprévisible d'un stimulus visuel sur 1–3 s,
   l'utilisateur doit cliquer le plus vite possible. Métriques :
   - RT moyen (lenteur globale)
   - SD RT (régularité)
   - taux de **lapses** (RT > 500 ms — épisodes d'inattention)
   - taux de **false starts** (réponse avant le stimulus —
     impulsivité)
3. **Continuous Performance Test (CPT)** — Conners 2014.
   Omissions/commissions sur une séquence de lettres. Plus lourd,
   plus long, et difficile à reproduire en web. **Rejeté** pour v2 au
   profit du PVT plus court.
4. **n-back working memory** — Owen et al. 2005. Mesure la mémoire de
   travail. **Rejeté** pour v2 car redondant avec le PVT pour notre
   objectif (calibrer la lecture, pas profiler la mémoire).

Pour le mode guidé v2 nous avons retenu **uniquement le PVT** :
- court (45 s, 16 essais)
- robuste à la variance individuelle
- mesure les 4 marqueurs comportementaux qui nous intéressent
- déployable en web (clavier + clic)

### 2.4 TDAH et lecture spécifiquement

Les méta-analyses (Sexton et al. 2012, Germanò et al. 2010) montrent
trois effets reproductibles :

- Le TDAH altère la **compréhension** plus que la
  **décodage** : les patients lisent les mots correctement mais
  perdent le fil sur des passages longs.
- L'**espacement** (interligne 1.5×–2× normal) et le **chunking
  visuel** améliorent la compréhension chez les enfants TDAH
  (Zentall 2005).
- La **lecture bionique** (préfixe en gras) appartient à une famille
  de techniques (preview cue, lexical anchoring) dont l'effet sur le
  TDAH n'est pas définitivement prouvé mais qui ont une base
  théorique solide via la **Optimal Viewing Position** (Vitu et al.
  1990 — l'œil saute naturellement au tiers initial du mot).

C'est pourquoi notre mapping profil → preset privilégie le ratio de
gras (fixationRatio) et l'interligne pour les profils inattentifs, et
le RSVP pour les profils hyperactifs (qui sont engagés par un rythme
imposé).

---

## 3. Conception itérée — "équipes qui se contredisent"

Le user a explicitement demandé qu'on brainstorme avec plusieurs
angles antagonistes. Voici les trois grandes itérations.

### Itération 1 — "100 % comportemental" (rejetée)

> **Pro** : pas de biais d'auto-évaluation.
> **Con** : un PVT n'est qu'un proxy. Sans contexte (les symptômes
> vécus), on prend pour un "TDAH inattentif" un sujet simplement
> fatigué.

Décision : il faut **les deux** sources, avec les comportemental
dominant (60 %).

### Itération 2 — "ASRS-18 complet" (rejetée)

> **Pro** : très précis, échelle utilisée en clinique.
> **Con** : 18 questions tuent le taux de complétion, surtout chez
> les TDAH (l'instrument même tente de calibrer crève).

Décision : utiliser la **Partie A — 6 items** (le screener court), qui
préserve la majorité du pouvoir prédictif.

### Itération 3 — "CPT 10 minutes + n-back" (rejetée)

> **Pro** : couvre la mémoire de travail et l'attention soutenue.
> **Con** : 10+ minutes → personne ne va au bout. De plus, redondant
> avec le PVT pour notre objectif (calibrer la lecture, pas faire un
> profil neuropsychologique).

Décision finale : **PVT 45 s seulement**.

### Itération 4 (retenue) — "ASRS-6 + PVT-16 + reading-60w"

- ASRS-6 (~45 s) — auto-rapport validé.
- PVT 16 essais (~45 s) — objectif comportemental.
- Lecture calibrée 60 mots (~15-25 s) — mesure directe de la vitesse.

Total : **2 minutes** + intro/résultats. Toutes les étapes sont
**skippables** ; la confiance du score s'ajuste en conséquence.

---

## 4. Algorithme de scoring (`backend/app/onboarding/scoring.py`)

### 4.1 Pipeline

```
ASRS answers ─► score_asrs    ─► (inatt_self, hi_self, w_self)
PVT trials   ─► score_pvt     ─► (inatt_obj, hi_obj, cons, w_pvt)
Reading      ─► score_reading ─► (wpm, w_read)
                                │
                                ▼
                       compose_profile(...)
                                │
                                ▼
                  ProfileVector(inatt, hi, wpm, cons, conf)
                                │
                                ▼
                  anchor_weights(profile)
                                │
                                ▼
                  pick winning anchor (argmax)
                                │
                                ▼
                  interpolate_settings(weights, winner)
                                │
                                ▼
                  AssessmentResult(profile, preset, settings)
```

### 4.2 Constantes documentées

Toutes les constantes ont une source ou une justification :

| Constante | Valeur | Source / justification |
|---|---|---|
| Likert ASRS | 0..4 | échelle WHO standard |
| PVT mean RT pour 100 % score inattention | 600 ms | Lim & Dinges 2008 : valeur seuil pour fatigue extrême |
| PVT SD RT pour 100 % score inattention | 200 ms | RT-SD pathologique en clinique (Klein 2006) |
| Taux de lapses (RT > 500 ms) pour 100 % | 30 % | Limite haute observée en TDAH adulte |
| Taux de faux départs pour 100 % HI | 20 % | Seuil arbitraire, sain ≈ 2-5 % |
| Blend self / behavioural | 0.4 / 0.6 | Behavioural dominant — l'auto-rapport est moins fiable |
| Poids axes distance | 2 / 2 / 1 / 0.5 | Inattention et HI sont les axes cliniques primaires |

### 4.3 Anchor presets

Les 4 anchor presets sont définis dans l'espace 4-dim :

```
apaise:    inatt=30  hi=20  wpm=160  cons=85
equilibre: inatt=45  hi=45  wpm=220  cons=80
concentre: inatt=80  hi=35  wpm=200  cons=45
sprint:    inatt=30  hi=75  wpm=320  cons=70
```

Justification :
- **apaise** : peu de symptômes, lecture longue posée.
- **equilibre** : symptômes modérés des deux côtés.
- **concentre** : profil inattentif net (forte inattention, RT
  variable, vitesse normale).
- **sprint** : profil hyperactif-impulsif (RT rapide + variable,
  préfère un rythme imposé → RSVP).

Le scoring projette le vecteur utilisateur sur ces 4 anchors par
**inverse-distance weighting**, choisit l'anchor avec le poids le
plus haut (label), et calcule des paramètres **interpolés** entre les
4 anchors :

- **Numériques** (fixationRatio, fontSize, rsvpWpm…) : interpolation
  linéaire pondérée.
- **Booléens** (rsvpEnabled, phraseChunkingEnabled…) : snap sur la
  valeur du label gagnant (pas de "RSVP à 40 %" — ça n'a aucun sens).
- **Strings** (theme) : snap sur la valeur du label gagnant.

Résultat : la sortie est à la fois **étiquetable** (`profile=concentre`,
pour l'affichage du nom) et **fluide** (les valeurs numériques sont
adaptées en continu au profil, pas en escalier).

### 4.4 Graceful degradation

Si l'utilisateur passe certaines étapes, la confiance du score baisse
en escalier :

| Étapes complétées | Confiance |
|---|---|
| 3 / 3 | 1.0 |
| 2 / 3 | 0.7 |
| 1 / 3 | 0.4 |
| 0 / 3 | 0.1 (preset par défaut) |

Le scoring n'échoue jamais : c'est une **propriété de robustesse
explicite**, demandée parce qu'un utilisateur TDAH qui ne va pas au
bout du test doit quand même avoir une expérience configurée.

---

## 5. Design UI ADHD-friendly

Choix de design (couches accessibilité, lisibles dans
`OnboardingV2.tsx`) :

- **Une action focale par écran.** Jamais plus d'un bouton primaire
  visible à la fois.
- **Progression visible permanente.** Compteur "étape 2/5" + barre de
  progression continue (pas de step caché).
- **Étapes skippables.** Trois `Passer` discrets — le test ne doit
  pas être bloquant.
- **Boutons ≥ 56 px de hauteur**, contraste ≥ 7:1, font-stack
  système sans-serif (chargement instantané, pas de FOUT).
- **`prefers-reduced-motion` honoré** — les transitions sont
  désactivées quand l'OS le demande (utile pour les sensibilités
  vestibulaires souvent comorbides au TDAH).
- **Affichage du raisonnement.** L'écran "Profil recommandé" donne
  explicitement *pourquoi* — chaque barre dimensionnelle est nommée
  en langage clair ("difficulté d'attention", "régularité des
  réflexes"), avec un texte de rationale.
- **Sortie réversible.** Bouton "Refaire la calibration" toujours
  accessible.

---

## 6. Validation

### 6.1 Tests automatiques (`backend/tests/test_onboarding.py`)

- 4 archétypes représentatifs (apaise / equilibre / concentre /
  sprint) — chacun construit avec une réponse ASRS + une distribution
  PVT + une vitesse de lecture cohérentes. Vérifie que le winning
  anchor est correct ET que les booléens dérivés (rsvpEnabled,
  phraseChunkingEnabled, eyeAnchorEnabled) sont bien activés.
- Confiance : test "tout vide" → confidence ∈ [0, 0.5], test "ASRS
  seul" → confidence < 1.0.
- Distribution : les 4 poids profil somment à 1.0 (probabilité
  valide).
- Bounds : les settings interpolés respectent `0 < fixationRatio ≤ 1`,
  `100 ≤ rsvpWpm ≤ 700`, `12 ≤ fontSize ≤ 32`.
- HTTP endpoint : POST /api/onboarding/score retourne 200 avec un
  result valide ET refuse les champs inconnus avec 422.

**10/10 tests passent.**

### 6.2 Simulation manuelle

Un user fictif "TDAH inattentif typique" (ASRS Often partout sur
q1-q3, Sometimes sur q4-q6, PVT mean RT 480 ms / SD 150 ms, lecture
180 wpm) → profile {inatt=72, hi=38, wpm=180, cons=52} →
`concentre`. Settings appliqués :

- `fixationRatio` ~0.49 (proche de l'anchor concentre 0.5)
- `phraseChunkingEnabled=true`, `eyeAnchorEnabled=true`
- `lineHeight` ~1.83 (interpolé entre concentre 1.9 et apaise 1.85)
- `rsvpEnabled=false` (concentre privilégie la lecture linéaire avec
  guidage)

C'est cohérent avec la littérature : un profil inattentif a besoin de
guidage visuel fort, pas de RSVP rapide.

---

## 7. Limites et futurs travaux

1. **Test non diagnostique.** Aucun seuil n'a été calibré contre un
   diagnostic clinique sur notre échantillon (et il faudrait un IRB
   pour le faire). Le résultat est explicitement présenté à
   l'utilisateur comme une recommandation de configuration.
2. **PVT court.** 16 essais est le minimum acceptable. Une vraie
   évaluation cinétique demanderait 5-10 min ; nous l'avons jugé
   incompatible avec l'objectif "calibration en 2 min".
3. **Pas de Stroop / pas de comorbidités.** Le mode guidé ne capture
   pas la dyslexie, l'anxiété ou la dépression — qui interagissent
   avec le TDAH et la lecture. Futur travail : module séparé
   "préférences lecture" qui pose des questions ciblées.
4. **Pas de réétalonnage adaptatif.** Aujourd'hui, le scoring est
   one-shot. Une v3 pourrait suivre la lecture dans le mode guidé et
   ajuster le preset en continu (ex: si l'utilisateur ralentit en fin
   de session, augmenter le fixation ratio).
5. **Pas de version i18n.** Tous les libellés sont en français.
   L'instrument ASRS officiel a une version anglaise validée ; il
   faudra l'intégrer pour ouvrir l'app à un public anglophone.

---

## 8. Références principales

- American Psychiatric Association (2013). *Diagnostic and
  Statistical Manual of Mental Disorders* (5th ed.). DSM-5.
- Barkley, R. A. (2012). *Executive functions: What they are, how
  they work, and why they evolved*. Guilford.
- Conners, C. K. (2014). *Conners Continuous Performance Test (CPT
  3)*. MHS.
- Dinges, D. F., & Powell, J. W. (1985). Microcomputer analyses of
  performance on a portable, simple visual RT task during sustained
  operations. *Behavior Research Methods, Instruments, &
  Computers*, 17(6), 652-655.
- Germanò, E., Gagliano, A., & Curatolo, P. (2010). Comorbidity of
  ADHD and dyslexia. *Developmental Neuropsychology*, 35(5), 475-493.
- Kessler, R. C., Adler, L., Ames, M., et al. (2005). The World
  Health Organization Adult ADHD Self-Report Scale (ASRS): A short
  screening scale for use in the general population. *Psychological
  Medicine*, 35(2), 245-256.
- Klein, C., Wendling, K., Huettner, P., Ruder, H., & Peper, M.
  (2006). Intra-subject variability in attention-deficit
  hyperactivity disorder. *Biological Psychiatry*, 60(10), 1088-1097.
- Knouse, L. E., & Mitchell, J. T. (2015). Incautiously optimistic:
  Positively biased self-evaluations in adults with ADHD. *Cognitive
  and Behavioral Practice*, 22(2), 226-239.
- Kofler, M. J., Rapport, M. D., Sarver, D. E., et al. (2013).
  Reaction time variability in ADHD: A meta-analytic review of
  319 studies. *Clinical Psychology Review*, 33(6), 795-811.
- Lim, J., & Dinges, D. F. (2008). Sleep deprivation and vigilant
  attention. *Annals of the New York Academy of Sciences*, 1129,
  305-322.
- Owen, A. M., McMillan, K. M., Laird, A. R., & Bullmore, E. (2005).
  N-back working memory paradigm: A meta-analysis of normative
  functional neuroimaging studies. *Human Brain Mapping*, 25(1),
  46-59.
- Sexton, C. C., Gelhorn, H. L., Bell, J. A., & Classi, P. M. (2012).
  The co-occurrence of reading disorder and ADHD: Epidemiology,
  treatment, psychosocial impact, and economic burden. *Journal of
  Learning Disabilities*, 45(6), 538-564.
- Sjöwall, D., Roth, L., Lindqvist, S., & Thorell, L. B. (2013).
  Multiple deficits in ADHD: Executive dysfunction, delay aversion,
  reaction time variability, and emotional deficits. *Journal of
  Child Psychology and Psychiatry*, 54(6), 619-627.
- Vitu, F., O'Regan, J. K., & Mittau, M. (1990). Optimal landing
  position in reading isolated words and continuous text. *Perception
  & Psychophysics*, 47(6), 583-600.
- Willcutt, E. G., Nigg, J. T., Pennington, B. F., et al. (2012).
  Validity of DSM-IV attention deficit/hyperactivity disorder
  symptom dimensions and subtypes. *Journal of Abnormal Psychology*,
  121(4), 991-1010.
- Zentall, S. S. (2005). Theory- and evidence-based strategies for
  children with attentional problems. *Psychology in the Schools*,
  42(8), 821-836.
