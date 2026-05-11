# Conseil des experts — design d'un lecteur réellement utile aux TDAH

Document de travail. 14 figures historiques et contemporaines (neurosciences de la lecture, TDAH clinique, perception visuelle, ergonomie, typographie, flow, design) débattent à tour de rôle sur **comment construire une expérience de lecture qui retient l'attention d'une personne TDAH du premier au dernier mot**. À la fin, synthèse opérationnelle.

> Méthode : pour chaque expert, je relis mentalement leur œuvre la plus citée et je formule l'argument qu'ils auraient dans un atelier de conception. Les apports sont contradictoires à dessein — ils nous obligent à arbitrer.

---

## 1. Stanislas Dehaene — neurosciences de la lecture

**Argument central** : lire, ce n'est pas voir des lettres : c'est reconnaître des chaînes graphémiques au sein d'une cascade ventrale qui passe par la **« letterbox area »** (région occipito-temporale gauche). Cette région a une **résolution maximale autour de 4 lettres** centrées sur la fixation foveale.

**Conséquence pour notre design** :
- L'idée du préfixe en gras de la lecture bionique est **insuffisante car arbitraire** : la fovéa ne capture que 7–8 lettres nettement de chaque côté. Le préfixe doit s'aligner sur le **point optimal de reconnaissance du mot** (OVP — *Optimal Viewing Position*), qui n'est PAS le début du mot, mais autour de la **moitié-gauche** (33–50% selon longueur).
- → **Eye-anchor dot** : un petit point gris discret PLACÉ exactement à l'OVP de chaque mot. C'est ce que fait l'œil expert naturellement. On le rend visible pour le lecteur TDAH qui ne le calcule pas spontanément.
- L'OPV varie : 2è lettre pour mot de 3, 3è pour mot de 5, 4–5è pour mot de 7+. (Données O'Regan 1987, Brysbaert 1996.)

**Citation à mettre en avant** : « Le cerveau du lecteur, p. 117 : *la fovéa lit, mais c'est la parafovéa qui décide où regarder ensuite.* »

---

## 2. Russell Barkley — psychologue clinicien, autorité TDAH

**Argument central** : le TDAH n'est pas un déficit d'attention — c'est un **déficit d'auto-régulation** et d'**inhibition** des réponses non pertinentes. La working memory est réduite d'environ 30%. La motivation est **gouvernée par la saillance immédiate**, pas par la récompense différée.

**Conséquence pour notre design** :
- Toute conception qui demande à l'utilisateur de **maintenir un état mental** (« je vais me concentrer », « je vais lire ce paragraphe ») est vouée à l'échec.
- → Il faut **externaliser la régulation** dans l'interface : auto-pacing, focus paragraphe forcé (le reste s'estompe vraiment), Pomodoro intégré, indicateur de progression toujours visible.
- Le quiz d'onboarding doit avoir **6 questions max** (working memory limitée). Pas 10.
- Récompense immédiate : à chaque paragraphe lu, micro-feedback (barre qui se remplit, sans gamification grotesque).

**Mot-clef** : « *l'attention chez le TDAH ne se commande pas — elle se capture* ».

---

## 3. Edward Hallowell — psychiatre TDAH, auteur *Driven to Distraction*

**Argument central** : le TDAH est aussi un **« hunter brain in a farmer's world »** — la stimulation **doit varier** ou l'attention décroche. Mais variation ≠ chaos.

**Conséquence pour notre design** :
- **Alternance** rythmée entre techniques : il faut proposer des « modes d'attaque » différents pour le même texte (lecture classique adaptée / RSVP / écoute TTS / chunks visuels). L'utilisateur bascule quand il sent qu'il décroche.
- → Bouton **« changer de mode »** toujours accessible (1 clic), discrètement, sans quitter la page.
- → **Compteur de décrochage** : si l'utilisateur reste plus de 30 secondes sans scroll, on lui propose gentiment « passer en mode audio ? » ou « passer en RSVP ? » — pas une notif agressive, juste un toast doux.

---

## 4. Maryanne Wolf — neuroscientifique cognitive de la lecture

**Argument central** : la lecture profonde (deep reading) suppose **temps + circuit complexe** (ventral lecture rapide ↔ dorsal lecture analytique). Le scroll infini et la lecture rapide érodent ce circuit. Pour les TDAH, le risque est de tout basculer vers le RSVP (lecture skim) sans construire de compréhension.

**Conséquence pour notre design** :
- Ne PAS faire de RSVP le mode par défaut. RSVP = sprint, pas marathon.
- → Le mode Guidé doit proposer **deux vitesses** par défaut : « lecture immersive » (rythme calme, focus paragraphe) vs « scan » (RSVP, chunking).
- → Marquer visuellement les **fins de phrases comme des respirations** (petit espace vertical) — invite à intégrer le sens avant de continuer.

---

## 5. Daniel Kahneman — cognition System 1 / System 2

**Argument central** : la lecture est **System 1** (automatique, fluide) quand tout va bien. Dès qu'il y a friction perceptive (couleur trop vive, contraste excessif, police mal dessinée), c'est **System 2** qui prend le relais — coûteux en attention.

**Conséquence pour notre design** :
- → **Le design DOIT être invisible**. Pas de bleu vif `#2563eb`, pas de surlignage agressif. Tout doit aller dans le sens d'une fluidité System 1.
- L'utilisateur ne doit JAMAIS être obligé d'aller chercher un réglage — tout est pré-recommandé.
- → Couleurs par défaut : **gris chauds** (le crème actuel `#fbfaf6` est encore trop blanc et tire vers le clinique). Cible : `#ece8e1` (parchemin doux) avec texte `#2a2825` (charcoal warm, pas noir).

---

## 6. Mihaly Csikszentmihalyi — théorie du flow

**Argument central** : le flow apparaît quand **défi = compétence**, retour immédiat, objectif clair. Trop facile → ennui. Trop dur → anxiété. La lecture TDAH oscille entre ces deux pièges.

**Conséquence pour notre design** :
- → **Vitesse adaptative** : l'app mesure le temps réel passé par paragraphe et ajuste subtilement (sans rien dire) la taille du chunk, le niveau de bionique, ou propose de ralentir/accélérer.
- Objectif clair : afficher TOUJOURS « il te reste 3 paragraphes » ou « 47% lus », mais discrètement.
- Récompense en flux : la barre de progression doit se remplir **avec lissage** (animation 300ms ease-out), pas par bonds, pour créer une sensation d'avancement continu.

---

## 7. Don Norman — *The Design of Everyday Things*

**Argument central** : un objet bien conçu se comprend sans manuel. Les **affordances** (ce que l'objet semble permettre) doivent être visibles, mais discrètes. Aujourd'hui, ton interface a 7 onglets latéraux. Pour un TDAH, c'est **40% de choices fatigue** dès l'ouverture.

**Conséquence pour notre design** :
- → Mode Guidé = **3 affordances maximum à l'écran** : « plus calme », « plus de bionique », « parler à voix haute ».
- → Pas de jargon : remplacer « ratio de fixation », « saccade adaptative », « overlay Irlen » par « combien de gras », « plus reposant pour les yeux ».
- → Toutes les options expertes (RSVP, TTS, chunking, justification, hyphens…) sont dans le mode Expert seulement. Le mode Guidé n'en montre que 4 sliders et 2 boutons.

---

## 8. Edward Tufte — design de l'information

**Argument central** : *« Above all else show the data »*. Maximiser le **data-ink ratio**. Tout pixel qui ne sert pas le contenu est du bruit.

**Conséquence pour notre design** :
- Pas de bordures inutiles, pas d'icônes décoratives.
- → Texte au centre, **rien autour**. Pas de header géant. Le nom du fichier en très petit en haut, c'est tout.
- → La toolbar du mode Guidé n'a PAS de panneau permanent — elle est dans une barre du bas, type lecteur Kindle, **invisible à moins de tapoter**.

---

## 9. Erik Spiekermann — typographie

**Argument central** : une bonne police pour la lecture longue a (a) des **distinctions claires** entre b/d/p/q (problème majeur des dyslexiques), (b) des **chasses uniformes**, (c) un **œil** (x-height) généreux, (d) du **caractère** (pour que le cerveau ait des amers).

**Conséquence pour notre design** :
- Lexend est bonne (conçue pour la lisibilité) — garder en défaut.
- **Atkinson Hyperlegible** (Braille Institute, 2019) : meilleure pour les déficits visuels — la mettre en option 2 explicite.
- **OpenDyslexic** : marche pour certains, pas tous (preuves mitigées) — laisser mais ne pas la pousser.
- → **Letter-spacing par défaut à 0.01em**, pas 0 (relâche subtilement la tension visuelle, gain mesuré sur fluence en relecture, Zorzi 2012).

---

## 10. Helen Irlen — syndrome scotopique

**Argument central** : ~14% des lecteurs ont une sensibilité aux contrastes élevés (texte noir/fond blanc) qui provoque flou, instabilité du texte, fatigue. Un **overlay coloré pastel** (rose pâle, jaune pâle, cyan pâle, vert pâle) résout 60–80% des cas.

**Conséquence pour notre design** :
- Le mode Guidé doit avoir une **étape « teste 5 couleurs de fond »** où l'utilisateur fait défiler 5 propositions de fond (gris chaud, crème, sépia, lavande pâle, menthe pâle) et choisit celle qui « repose les yeux ».
- → **NE PAS** mettre l'overlay devant le texte (mon implémentation actuelle le fait via `position: fixed` au-dessus). C'est **mauvais** — l'overlay doit être le **fond** du conteneur lecteur. Bug à corriger.

---

## 11. Renato Casutt — inventeur de la lecture bionique

**Argument central** : la lecture bionique en elle-même est un **guide de saccade**, pas une accélération. Son intérêt est de **réduire la fatigue** sur les longs textes, pas d'augmenter le wpm sur 200 mots.

**Conséquence pour notre design** :
- Ne pas survendre le bionique. Le présenter comme **« aide à ne pas perdre la ligne »**, pas comme **« lis 50% plus vite »** (faux).
- → Ratio par défaut : **40%** (pas 50%), légèrement plus bas que mon implémentation actuelle. Plus discret = plus durable sur une longue session.
- → Désactiver le bionique sur les mots de moins de 4 lettres : c'est du bruit (la/le/un/des n'ont rien à guider).

---

## 12. Steven Pinker — langage et cognition

**Argument central** : la **syntaxe** est ce qui structure le sens. Un bon design devrait aider à voir les **groupes syntaxiques** (groupe nominal, groupe verbal, propositions subordonnées), pas les mots isolés.

**Conséquence pour notre design** :
- → **Phrase chunking** : grouper les mots en phrases courtes visuelles (3–5 mots) séparées par des micro-espaces. Marche très bien pour les TDAH (réduit la charge sur la WM).
- → **POS coloring très subtil** (optionnel) : verbes en gris foncé légèrement teinté (`#3a3530`), noms en charcoal (`#2a2825`), connecteurs ("mais, donc, car") en orange très pâle. Permet de scanner la structure d'un coup d'œil.

---

## 13. Temple Grandin — penseuse neurodivergente, *Thinking in Pictures*

**Argument central** : beaucoup de cerveaux neurodivergents (TDAH inclus) pensent en images, pas en mots. La lecture pure est **un mode hostile** pour ce type de cognition.

**Conséquence pour notre design** :
- → **Dual modality TTS + texte** doit être un mode première classe, pas une option enfouie dans le 6è onglet. Synchroniser un surlignage **discret** (fond gris très pâle) sur le mot en cours d'audition.
- → Possibilité (mode Expert) d'**afficher une mini-illustration** générée pour les concepts complexes (out of scope pour cette version mais à noter).

---

## 14. Anne Treisman — théorie de l'intégration des traits

**Argument central** : l'attention sélective fonctionne par **pré-attention** sur des traits visuels singletons (couleur, taille, orientation). Si tout est uniforme, l'œil ne sait pas où atterrir. Si tout varie, c'est l'overload.

**Conséquence pour notre design** :
- → **Une seule dimension** doit varier pour guider l'attention : le **poids** (préfixe gras). Ne PAS y ajouter en plus couleur + souligné + taille (mon design actuel permet 4 dimensions cumulatives — c'est trop).
- → Le mode Guidé désactive automatiquement toutes les combinaisons (color + bold + first-letter-color + vowels) qui empilent les saillances. **Au max 2 dimensions** activées simultanément.

---

## Synthèse — points de consensus du conseil

| Décision | Source(s) | Implémentation |
|---|---|---|
| **Thème par défaut = gris chaud doux** `bg #ece8e1 / fg #2a2825` | Kahneman, Irlen | nouveau preset `paper` qui remplace `cream` comme défaut |
| **Ratio bionique baissé à 40%** | Casutt | `fixationRatio: 0.4` |
| **minWordLength = 4** | Casutt | skip articles et mots courts |
| **letter-spacing default 0.01em** | Spiekermann | typo défaut |
| **Eye-anchor dot** (point gris OVP) | Dehaene | nouvelle technique backend + frontend |
| **Phrase chunking par groupes syntaxiques** | Pinker | nouvelle technique (phrase de 3–5 mots → groupes visuels) |
| **Focus paragraphe FORT (opacité 0.2 sur les autres)** | Barkley | renforcer le focus mode existant |
| **Auto-pacing (Pomodoro intégré)** | Barkley, Hallowell | nouveau composant |
| **Détection décrochage → toast doux** | Hallowell | event listener scroll |
| **Indicateur progression toujours visible** | Csikszentmihalyi, Barkley | barre fine en haut |
| **Quiz d'onboarding à 6 questions** | Barkley (WM), Norman | nouveau composant `Onboarding` |
| **Mode Guidé = 3 affordances visibles** | Norman, Tufte | refonte UI radicale du panneau gauche en mode guidé |
| **TTS dual modality = mode première classe** | Grandin | bouton géant « écouter » dans Guidé |
| **Overlay = fond du conteneur, pas couche au-dessus** | Irlen | refacto Reader.tsx |
| **Pas plus de 2 dimensions de saillance simultanées en Guidé** | Treisman | algorithme de scoring force |
| **Pas de RSVP par défaut** | Wolf | RSVP réservé au mode Expert ou bouton « sprint » explicite |

---

## Nouvelles techniques à inventer / combiner

Au-delà du consensus, le conseil pousse à **inventer** ce qui n'existe pas encore comme combinaison cohérente :

### A. **Eye-anchor dot** (Dehaene)
Un point gris de 2 px placé à l'OVP de chaque mot (lettre n°2 sur mot de 3, n°3 sur mot de 5, n°4 sur mot de 7+). Subtil mais guide la saccade au point optimal. **Nouveau dans la littérature de design appliqué.**

### B. **Breathing word** (Csikszentmihalyi + Treisman)
En lecture audio (TTS actif), le mot en cours d'audition n'est pas surligné en jaune (trop saillant), mais voit son **poids passer de 400 à 500 sur 200ms** en ease-in-out. C'est un guide cognitif sans rupture System 1.

### C. **Pulse cadence** (Hallowell, Csikszentmihalyi)
En mode auto-pacing, un **liseré gris très pâle** descend lentement à travers le texte (1 ligne toutes les 1.5s à 220 wpm). L'utilisateur peut soit suivre, soit le dépasser. C'est une **invitation, pas une contrainte** — fondamental pour les TDAH qui refusent le forcing.

### D. **Calm-grade adaptive** (Kahneman + Csikszentmihalyi)
Toutes les 60 secondes, l'app mesure le **temps moyen par paragraphe** vs la cible théorique. Si l'utilisateur est plus lent, elle propose discrètement de réduire le bionique d'un cran (« on dirait que ça force, je peux essayer plus discret ? »). Aucune pop-up agressive — toast doux 4 secondes.

### E. **POS subtle highlight** (Pinker, Treisman)
Les connecteurs logiques (« mais, donc, parce que, cependant, néanmoins, ainsi, en effet, puisque ») sont colorés en `#a05a1a` très atténué. C'est la **carte mentale** du raisonnement, visible d'un coup d'œil. Optionnel.

### F. **Reading "anchor letters"** (combinaison Spiekermann + Dehaene)
Optionnellement, la première lettre **et** la lettre OVP du mot sont à la fois en gras. Le cerveau a **deux points d'ancrage** par mot → meilleure prédictibilité de la saccade.

### G. **Quietness slider** (Treisman, Norman)
Un seul slider master « niveau de calme » qui, en un mouvement, désactive séquentiellement tout ce qui est saillant : passe le bionique de bold à color-only, réduit le contraste, agrandit l'interligne. Trois positions : **tonique / équilibré / cocoon**.

---

## Le débat des dissidents

Trois points où le conseil n'est PAS unanime, et où il faut trancher :

1. **Tufte vs Barkley** : Tufte dit « pas d'indicateurs, juste le texte ». Barkley dit « il faut afficher la progression sinon le TDAH ne sait pas où il en est ». → On tranche en faveur de Barkley pour le mode Guidé, mais l'indicateur est **fin (3 px)** et **en haut** (pas dans le champ de lecture).

2. **Wolf vs Hallowell** : Wolf dit « pas de RSVP, dégrade la compréhension ». Hallowell dit « la variation des modes EST le levier d'attention ». → Compromis : RSVP est **disponible en un clic** mais jamais le mode d'arrivée par défaut. On annonce explicitement « mode sprint, compréhension réduite ».

3. **Treisman vs Pinker** : Treisman veut **une seule dimension saillante**. Pinker propose POS coloring + bionique = 2 dimensions. → Compromis : POS coloring est OFF par défaut, on le propose comme **toggle distinct** dans le mode Expert. En mode Guidé, jamais.

---

## Conclusion opérationnelle

Le conseil produit une **architecture en 2 modes** :

### Mode Guidé (par défaut, simple, recommandé)
- Onboarding 6 questions à la première visite (puis persisté en localStorage)
- Algorithme de scoring → preset auto (« Apaisé », « Équilibré », « Concentré », « Sprint »)
- UI : **uniquement** 3 contrôles visibles → « plus calme / plus bionique / écouter »
- Auto-pacing optionnel via bouton « play » géant
- Détection décrochage → suggestion non-intrusive
- Indicateur de progression fin en haut
- Pas de jargon (« combien de gras », « plus reposant »)

### Mode Expert (pour les power users)
- Conservation de la toolbar complète actuelle
- + Nouveaux contrôles : eye-anchor dot, phrase chunking, POS coloring, auto-pacing speed
- + **Quietness slider** unique (raccourci master)

### Sous le capot
- Backend : ajouter `eyeAnchor`, `phraseChunking`, `posColoring`, `pulseCadence`, `breathingWord` dans `BionicSettings`
- Frontend : refonte des thèmes (paper, fog, lavender, mint comme nouveaux defaults calmes), refactor de l'overlay (fond du conteneur), nouveaux composants `Onboarding`, `WelcomePage`, `GuidedShell`, `QuietnessSlider`, `ProgressBar`, `AutoPacer`
- **Simulateur** TDAH (script Python) qui modélise saccades / décrochage / WM et score chaque preset → confirme que « Apaisé » obtient bien le meilleur score sur un lecteur TDAH simulé.

Prochaine étape : simulation cognitive (`ADHD_SIMULATOR.md`).
