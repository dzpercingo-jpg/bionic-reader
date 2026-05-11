# Decisions — refonte mode guidé v2

Ce document synthétise en 1 page les décisions de design issues du Conseil d'experts
(voir `COUNCIL.md`) et validées par le simulateur de lecteur TDAH
(voir `ADHD_SIMULATOR.md`).

## Pourquoi cette refonte ?

Feedback utilisateur : *« je ne ressens pas vraiment que c'est bien »* + sensation
que l'interface est trop chargée et que la couleur de fond est trop blanche.

Le simulateur a confirmé objectivement le problème : sur la configuration v1
(`devin_v1`), un lecteur TDAH simulé atteint **un score de friction de 100/100**
— c'est-à-dire qu'il abandonne le texte avant la fin. La cumulation possible de
saillances visuelles (color_vowels + color_first_letter + use_color_instead_of_bold
+ overlay flottant) explosait la charge cognitive.

## Trois axes de décision

### 1. Mode guidé par défaut, mode expert en option

| Mode      | Visible | Utilisateurs cibles                          |
|-----------|---------|----------------------------------------------|
| Guidé     | défaut  | Premier usage, TDAH non-expert               |
| Expert    | toggle  | Power-users, designers, recherche perso      |

Le mode guidé limite l'écran à **3 affordances** : *plus calme* / *plus de bionique*
/ *écouter*. Aucun slider, aucun panneau. La sélection de réglages passe par un
**onboarding** : 6 questions, ~30 s, scoring vectoriel → preset auto-appliqué.

### 2. Quatre profils cohérents

Chaque profil est un **bundle complet** de paramètres (jamais de combinaison
incohérente possible) :

| Profil      | Friction (simulateur, médiane) | Cas d'usage                                |
|-------------|-------------------------------|--------------------------------------------|
| Apaisé      | 18,9                          | Lecture longue, livre, soir                |
| Équilibré   | 42,8                          | Usage quotidien général                    |
| Concentré   | 16,7                          | Texte dense, étude, prise de note          |
| Sprint      | 24,9                          | Scan rapide, headlines, RSVP               |

Comparaison : configuration v1 → **100,0**. Nouveaux profils → divisés par 4 à 6.

### 3. Nouvelles techniques (issues du Conseil)

Six techniques inédites combinées, chacune avec un fondement théorique :

1. **Point OVP** (Dehaene, O'Regan 1987) — point gris de 1 px sous chaque mot,
   à la *Optimal Viewing Position*. Guide la saccade sans saillance forte.
2. **Phrase chunking** (Pinker) — groupe les mots par 4 avec une micro-respiration
   visuelle. Expose la structure de la phrase à coût zéro.
3. **POS coloring** (Pinker, Treisman) — colore les connecteurs logiques
   (*mais, donc, parce que, cependant*) en brun chaud, jamais en jaune ou rouge.
4. **Pulse cadence** (Hallowell) — ligne horizontale qui descend lentement.
   Auto-régule la vitesse de lecture sans demander de clic.
5. **Quietness slider** (Norman) — un seul contrôle global qui cascade :
   *tonique → équilibré → cocoon*. Réduit la charge décisionnelle.
6. **Respiration de mot** (Csikszentmihalyi) — au lieu d'un surlignage jaune sur le
   mot lu par le TTS, un simple pulse de poids (font-weight 500 → 600). Beaucoup
   moins distrayant.

### 4. Couleurs plus douces (palette parchment)

| Thème       | Fond         | Texte        | Contraste  | Cas                         |
|-------------|--------------|--------------|------------|-----------------------------|
| paper *     | `#ece8e1`    | `#2a2825`    | 10,8 : 1   | Défaut (parchment chaud)    |
| fog         | `#dde1e3`    | `#262a2d`    | 11,4 : 1   | Concentré (gris froid)      |
| lavender    | `#e8e3ec`    | `#2d2a33`    | 10,2 : 1   | Calme (lavande)             |
| mint        | `#dfe7e1`    | `#1f2924`    | 11,0 : 1   | Calme (menthe)              |

Le blanc franc (`#fafaf9`) est conservé en option mais n'est plus le défaut.

Tous les contrastes respectent **WCAG AAA** (> 7:1 pour le corps).

### 5. Contraintes d'invariants

- **Maximum 2 saillances cumulées simultanément** (Treisman). Le mode guidé
  bloque les combinaisons toxiques (couleur voyelles + couleur première lettre +
  couleur connecteurs + overlay).
- **L'overlay n'est plus une couche flottante** : il teinte la couleur de fond
  *via* un blending. Plus de halo qui suit le scroll.
- **Le fichier source n'est jamais modifié** sur disque (SHA-256 vérifié dans
  les tests).
- **Mode expert préserve la version actuelle**, accessible en un clic.

## Mesures objectives

| Indicateur                        | v1     | v2 (mode guidé / preset *concentré*) |
|-----------------------------------|--------|---------------------------------------|
| Friction TDAH simulée             | 100,0  | 16,7                                  |
| Saillances cumulables             | ≥ 4    | ≤ 2                                   |
| Décisions à prendre avant lecture | 8 panneaux × ~3 toggles | 6 questions de quiz                |
| Affordances visibles à l'écran    | 7 onglets + 20+ sliders | 3 boutons                           |
| Contraste fond/texte (défaut)     | 19,1   | 10,8 (toujours AAA, moins agressif)   |

## Ce qu'on ne change pas

- L'algorithme bionique de base (saccade adaptative, ratio configurable) ✓
- Le support des formats PDF / DOCX / EPUB / HTML / MD / RTF / TXT ✓
- L'export vers HTML autonome, DOCX (Word) et TXT ✓
- La conservation absolue du fichier source ✓
- Le mode RSVP, le TTS, le ruler, le focus paragraphe (déplacés dans le mode expert) ✓

## Étapes suivantes (post-merge)

1. Test utilisateur (toi) sur les 4 presets.
2. Ajustements éventuels du scoring du quiz selon retours.
3. Ajout d'un mode "lecture continue" qui mémorise la position dans le doc.
4. Calibrage perso : option pour fine-tuner un preset puis le sauvegarder.
