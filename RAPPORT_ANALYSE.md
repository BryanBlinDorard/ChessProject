# Rapport d'analyse — ChessProject

Analyse du 2026-09-06. Projet : jeu d'échecs Python / Pygame, IA NegaMax.
Basé sur la structure de la série "Chess Engine in Python" (Eddie Sharick), largement retravaillé.

---

## ✅ État : Étapes 0 et 1 réalisées (2026-09-06)

**Étape 0 — filet de sécurité**
- `requirements.txt` figé, `requirements-dev.txt` ajouté (pytest, ruff, mypy).
- `fen_utils.py` : chargeur FEN + `perft` (utilitaires de test).
- `test_perft.py` : perft sur 6 positions de référence (position initiale, Kiwipete,
  positions 3 à 6). Toutes exactes jusqu'à perft(3) en test rapide, **jusqu'à
  ~4 millions de nœuds** (perft(4)/perft(5)) en test lent (`RUN_SLOW_PERFT=1`).
- `test_rules_regression.py` : 15 tests verrouillant les bugs corrigés.
- `TESTS.md` : mode d'emploi. **27 tests, tous verts.**

**Étape 1 — règles justes.** Corrigés : B1, B2, B3, B4, B5, B7, B8, B9, B18.
La campagne perft a révélé et corrigé **3 bugs supplémentaires** non repérés à la
lecture :
- **B24** — `undoMove` faisait aliaser `current_castling_rights` sur une entrée du
  log, que le `updateCastleRights` suivant corrompait en place → droits de roque
  qui « bavaient » d'une position à l'autre après annulation. Copie défensive ajoutée.
- **B25** — quand un pion venait mettre le roi en échec par une poussée double, la
  prise en passant de ce pion (case d'arrivée ≠ case du pion) était rejetée par le
  filtre de sortie d'échec. Exception ajoutée.
- **B18** confirmé — une tour issue d'une promotion, capturée en a1/h1/a8/h8,
  supprimait à tort un droit de roque (rangée non testée).

Le générateur de coups est désormais **conforme** (perft exact partout).

## ✅ État : Étape 2 (partielle) réalisée (2026-09-06)

Nettoyage UI — corrigés :
- **B10** — `Z` ne fait plus un double `undoMove` qu'en mode contre l'IA, et
  seulement si le dernier coup était celui de l'IA (test `human_now`). En PvP/CvC,
  un seul undo.
- **B13** — `drawEndGameText` centre désormais sur le plateau (décalage
  `LEFT_PANEL_WIDTH`) et non sous le panneau gauche.
- **B14** — `R` recrée `GameState(flip_board=flip_board)` (orientation conservée)
  et remet les pendules à zéro.
- **B15** — le défilement de l'historique est borné en haut : `UIManager` calcule
  `max_scroll` à partir de la hauteur réelle du contenu et `handle_scroll` clampe
  dans `[0, max_scroll]`.
- **B16** — `UIManager.reset_timer()` resynchronise `last_time` au (re)démarrage de
  la partie, après les menus : le temps passé dans les menus n'est plus imputé aux
  Blancs. Appelé aussi sur `R` et sur chargement.
- **B20 / B21** — `p.mixer.init()` + chargement des sons et `logging.basicConfig`
  sortis du niveau module vers `_load_sounds()` / `_configure_logging()`, appelés
  depuis `main()`. Importer `ChessMain` (tests) n'ouvre plus l'audio ni ne crée
  `chess_debug.log`.
- **B23** — `MAX_FPS` passé de 15 à 30.

Restent ouverts pour l'étape 2 : suppression du `flip_board` global (→ attribut
d'un `Renderer`, B22), découpage de `main()` (200 lignes), remplacement de la
sauvegarde `pickle` par FEN + liste de coups (B17). Ces trois points sont des
refactors plus lourds, sans couverture de test UI — à faire ensuite.

Restent ouverts : bugs IA (B6, B11, B12) → étapes 3 et 4.

---

## 1. Vue d'ensemble

| Fichier | Rôle | État |
|---|---|---|
| `ChessEngine.py` | Règles, plateau, génération/validation des coups, évaluation nulle | Fonctionnel, quelques bugs de règles |
| `ChessAI.py` | NegaMax + alpha‑bêta + table de transposition + ordonnancement | Fonctionnel mais faible et lent conceptuellement |
| `ChessMain.py` | Pygame : entrées, rendu, menus, sons, sauvegarde, animation, chrono | Fonctionnel, dette UI |
| `test_chess.py` | 6 tests unittest | Passent tous (`python -m unittest test_chess`) |

Points forts : broches (pins) et échecs gérés proprement, roque / en passant / promotion présents, règle des 50 coups + matériel insuffisant + répétition, séparation moteur/IA/UI, IA en `multiprocessing` (UI non bloquée), menus, personnalisation, sons, sauvegarde pickle.

`requirements.txt` liste `numpy` mais il n'était pas installé dans l'environnement ; à figer (`numpy==2.x`).

---

## 2. Bugs (par priorité)

### 🔴 Critiques — fausses règles

**B1. `getValidMoves` utilise des broches périmées.**
`ChessEngine.py:301-302` appelle `getAllPossibleMoves()` **avant** `checkForPinsAndChecks()`. La génération des coups filtre donc les pièces clouées avec les broches de la position **précédente** (et du mauvais camp). Reproduit : une pièce clouée se voit proposer des coups illégaux au premier calcul de la position (et c'est ce calcul qui est mis en cache et utilisé en jeu réel).
→ Corriger : calculer `in_check, pins, checks` d'abord, puis générer les coups.

**B2. Le pat (stalemate) n'est pas détecté.**
`ChessEngine.py:328-341` : `stalemate` n'est mis à `True` que par les règles de nulle (50 coups / matériel / répétition). Le cas « aucun coup légal et roi pas en échec » ne met jamais `stalemate = True`. Reproduit : position de pat classique → `moves=[]`, `stalemate=False`, `checkmate=False`, partie bloquée sans fin de partie.
→ Ajouter : `elif not moves and not self.in_check: self.stalemate = True`.

**B3. `insufficient_material` trop laxiste.**
`ChessEngine.py:162-174` : renvoie `True` dès qu'il y a ≤ 1 pièce hors roi. Donc **Roi + Dame vs Roi** ou **Roi + Tour vs Roi** sont déclarés nulle → impossible de mater avec une dame. C'est aussi ce qui masquait B2 dans certains tests.
→ Ne renvoyer `True` que pour : R vs R ; R+(B ou N) vs R ; R+B vs R+B de même couleur de case. Compter les pièces par type/couleur.

**B4. Cases attaquées par les pions ignorées si la case est vide.**
`getPawnMoves` (`:405-413`) n'ajoute une capture diagonale que si une pièce ennemie est présente. Or `squareUnderAttack` (`:351-362`) s'appuie sur `getAllPossibleMoves`. Conséquence : `getCastleMoves`/`getKingside/QueensideCastleMoves` (`:541-563`) peuvent autoriser un roque qui traverse une case **contrôlée par un pion** (case vide). Les déplacements de roi ne sont pas touchés (ils passent par `checkForPinsAndChecks`, correct).
→ Fournir une vraie fonction « case attaquée » (attaques des pions incluses, cases vides comprises), ou générer les coups de pion diagonaux vers cases vides marqués « attaque seulement ».

**B5. `getKingsideCastleMoves` / `getQueensideCastleMoves` : `IndexError` possible.**
`:555-563` accèdent à `board[row][col±2]` / `col-3` sans borne. En jeu normal les droits de roque protègent, mais toute position chargée / éditée avec le roi hors de sa case et des droits à `True` fait planter le moteur (`IndexError: list index out of range`, reproduit).
→ Vérifier que le roi est bien sur `(7,4)`/`(0,4)` et borner les indices, ou fiabiliser `updateCastleRights`.

### 🟠 Importants

**B6. Table de transposition sans borne (exact/lower/upper).**
`ChessAI.py:27-48` stocke `max_score` comme valeur **exacte** même quand la boucle a été coupée par `alpha >= beta` (c'est alors une borne inférieure). Des scores tronqués sont ensuite relus comme exacts → l'IA peut jouer un coup objectivement mauvais. De plus un hit TT à la racine renvoie `(score, None)` → `best_move = None`.
→ Stocker un flag `EXACT / LOWERBOUND / UPPERBOUND` + la profondeur, et ne couper sur un hit que si la borne est compatible avec `[alpha, beta]`. Toujours stocker le meilleur coup pour le réutiliser en tête d'ordonnancement.

**B7. Hash de position incomplet (répétition + TT).**
`get_board_hash_str` (`:157-160`) et `get_board_hash` (`ChessAI.py:141-146`) ne hachent que `board + white_to_move`. Ni les droits de roque, ni la case d'en passant. Deux positions réellement différentes (au sens FIDE de la triple répétition) sont comptées identiques → nulles réclamées à tort, et collisions dans la TT.
→ Inclure droits de roque + en passant dans la clé. Idéalement : hachage de Zobrist incrémental.
Détail : `str(hash(...))` n'apporte rien, garder l'`int`.

**B8. `moveID` n'encode pas la pièce de promotion.**
`Move.__eq__` (`:646,655-656`) : promotion en Dame et en Cavalier ont le même `moveID` → considérées égales. L'UI force toujours Dame côté moteur pour le popup (`ChessMain.py:583-585` passe `btn.text` mais `makeMove` revalide via `move not in getValidMoves()` avec un `Move` sans info de promotion — ça marche par chance). L'IA ne considère jamais la sous‑promotion.
→ Ajouter `promotion_piece` au `Move`, l'inclure dans `__eq__`/`__hash__`, générer les 4 promotions dans `getPawnMoves`.

**B9. `Move` définit `__eq__` sans `__hash__`.**
Les objets `Move` deviennent non hachables (impossible de faire `set(moves)`). Pas utilisé aujourd'hui mais piège pour l'optimisation de l'ordonnancement / killer moves.

**B10. Undo double inconditionnel.**
`ChessMain.py:645-651` : la touche `Z` fait deux `undoMove()` pour « sauter » le coup de l'IA. En mode **Joueur vs Joueur** cela annule aussi le coup adverse légitime. En début de partie (1 coup joué) le 2ᵉ undo est ignoré, OK, mais le comportement PvP est faux.
→ N'annuler deux fois qu'en mode contre l'IA, et seulement si le dernier coup est celui de l'IA.

**B11. `scoreBoard` appelle `getValidMoves()` à chaque feuille.**
`ChessAI.py:127` : la mobilité recalcule toute la génération légale (pins/checks compris) pour **chaque nœud feuille** du NegaMax. Très coûteux, et la mobilité n'est mesurée que pour le camp au trait (pas différentielle).
→ Mobilité différentielle approchée via `getAllPossibleMoves`, ou la retirer, ou ne l'évaluer qu'en cache.

**B12. `moveOrderingHeuristic` fait make/undo par coup.**
`ChessAI.py:62-64` applique puis annule chaque coup juste pour hacher la position et détecter une répétition, à chaque tri, à chaque profondeur. Coût ~×2 sur toute la recherche pour un signal marginal.
→ Ordonner via MVV‑LVA (valeur capturée − valeur capturante), promotions, puis coup de la TT ; garder la détection de répétition uniquement à la racine.

### 🟡 Mineurs / UI

- **B13.** `drawEndGameText` (`ChessMain.py:319-326`) centre sur `BOARD_WIDTH` sans ajouter `LEFT_PANEL_WIDTH` → texte de fin décalé sous le panneau gauche.
- **B14.** Touche `R` : `ChessEngine.GameState()` recréé sans `flip_board` (`:659`) → en jouant les Noirs, plateau toujours retourné mais roi/dame non permutés. Incohérent.
- **B15.** `handle_scroll` (`:143-146`) n'a pas de borne supérieure → on défile l'historique dans le vide.
- **B16.** Chronomètre : `last_time` initialisé à la création de `UIManager`, avant les menus → tout le temps passé dans les menus est imputé aux Blancs au premier tick.
- **B17.** `load_game` par `pickle` : rechargement d'un objet complet sans contrôle de version/schéma ; `pickle` est aussi un risque de sécurité si le fichier vient d'ailleurs. Préférer une sérialisation FEN + liste de coups.
- **B18.** `updateCastleRights` (`:263-274`) teste `move.end_col in (0,7)` pour une tour capturée sans vérifier `end_row` (rangée 0 ou 7).
- **B19.** `getChessNotation` a un `return "error"` mort après un `if/else` exhaustif ; pas d'annotation d'échec (`+`) ni de mat (`#`), pas de désambiguïsation (`Nbd2`).
- **B20.** `p.mixer.init()` et chargement des sons au niveau module → import de `ChessMain` par les tests initialise l'audio (effets de bord). À déplacer dans `main()`.
- **B21.** `ChessMain.py:6` `import sys, os, pickle, logging` groupés ; `logging.basicConfig` au niveau module écrit toujours `chess_debug.log` dans le cwd.
- **B22.** Le `flip_board` est une variable **globale** mutée un peu partout (`Animation`, `draw_board`, `draw_pieces`, `main`) → source de bugs d'orientation. À passer en paramètre / attribut d'un objet vue.
- **B23.** `MAX_FPS = 15` rend l'UI peu réactive (saisie souris, hover boutons). 30–60 conseillé.

---

## 3. Optimisations

### Correction / robustesse
1. Réordonner B1, ajouter B2, resserrer B3 : c'est le socle « règles justes ».
2. Clé de position complète (B7) → répétition FIDE correcte + TT fiable.
3. Suite de tests « perft » : compter les nœuds à profondeur 1‑4 depuis la position initiale et 4‑5 positions de référence (Kiwipete, etc.) et comparer aux valeurs connues. C'est le seul moyen fiable de valider la génération de coups.

### Performance moteur (gain ×5 à ×50 possible)
4. **Ne pas tout régénérer** : `getKingMoves` appelle `checkForPinsAndChecks` jusqu'à 8 fois ; `getCastleMoves` appelle `squareUnderAttack` (donc `getAllPossibleMoves`) 2 fois de plus. Calculer les cases attaquées **une seule fois** par position (bitboard ou tableau 8×8 `attacked[r][c]`).
5. **`makeMove`/`undoMove` sans `copy.deepcopy`** : `position_history_log` fait un `deepcopy` du dict à chaque coup (`:187`). Utiliser un hash unique + pile de hash, ou un compteur incrémental.
6. `makeMove(validate=True)` par défaut appelle `getValidMoves()` : coûteux quand on sait déjà que le coup vient de la liste valide. L'UI devrait passer `validate=False` pour un coup déjà vérifié.
7. **Représentation du plateau** : `List[List[str]]` avec des chaînes `"wp"` → beaucoup d'allocations et de comparaisons de chaînes. Passer à des entiers (ou bitboards) : gros gain sur l'évaluation et la génération.
8. IA : **quiescence search** (ne s'arrêter que sur position calme) pour supprimer l'effet d'horizon ; **iterative deepening piloté par le temps** (le process a 5 s mais l'IA rend en 0,2 s — profondeur ~3 gâchée) ; **move ordering** MVV‑LVA + killer + history + coup de la TT ; **null‑move pruning**.
9. `scoreBoard` : précalculer les tables `piece_position_scores` en dict d'accès O(1) sans `numpy` (l'indexation numpy scalaire est lente), ou vectoriser toute l'évaluation en une passe numpy.
10. `transposition_table` non borné → fuite mémoire sur longue partie. Ajouter une taille max / remplacement.

### Architecture / qualité
11. Extraire une classe `View`/`Renderer` (fin de `flip_board` global, de `ui_manager` global).
12. `ChessMain.main()` est une fonction de 200 lignes : séparer boucle d'événements, mise à jour, rendu.
13. Constantes dupliquées : `CHECKMATE`, `DIMENSION`, `Color` définis dans 3 fichiers. Un seul module `constants.py`.
14. Typage : `mypy --strict` passerait presque ; corriger les `# type: ignore` sur `enpassant_possible` (utiliser `Optional[Tuple[int,int]]`).
15. `logging` configurable (niveau, fichier) ; retirer les logs bruyants de la boucle.
16. `requirements.txt` : figer les versions ; ajouter `requirements-dev.txt` (pytest, mypy, ruff).
17. CI GitHub Actions : `unittest` + `perft` + `ruff` + `mypy` à chaque push.

---

## 4. Plan pour la suite

### Étape 0 — Filet de sécurité (0,5 j) — ✅ FAIT
- [x] Ajouter `pytest`, `ruff`, `mypy` en dev ; figer `requirements.txt`.
- [x] Écrire les tests **perft** (position initiale + Kiwipete + 4 autres).
- [x] Tests de non‑régression : mat du berger, pat classique, K+Q vs K matable, triple répétition réelle, roque à travers case attaquée par un pion, sous‑promotions, prise en passant exposant le roi.

### Étape 1 — Règles justes (1–2 j) — ✅ FAIT
- [x] B1 (ordre pins/checks), B2 (pat), B3 (matériel insuffisant), B4 (attaque de pion sur case vide), B5 (bornes roque).
- [x] B7 : clé de position = plateau + trait + droits de roque + en passant.
- [x] B8 : `Move.promotion_piece` + `__hash__` + génération des 4 promotions.
- [x] B18 / B24 / B25 (trouvés via perft).
- [x] Perft exact à profondeur 4–5 sur les 6 positions de référence.

### Étape 2 — Nettoyage UI (1–2 j) — 🟡 EN COURS
- [x] B10 (undo PvP), B13 (texte de fin), B14 (reset + flip), B15/B16 (scroll, chrono).
- [x] Sortir `mixer.init` + sons + `logging.basicConfig` dans `main()`.
- [x] `MAX_FPS` monté à 30.
- [ ] Supprimer `flip_board` global → attribut d'une classe `Renderer`.
- [ ] Découper `main()`.
- [ ] Remplacer la sauvegarde `pickle` par FEN + liste de coups (PGN léger).

### Étape 3 — Moteur performant (2–4 j)
- [ ] Table `attacked[r][c]` calculée une fois par position ; supprimer les appels répétés à `squareUnderAttack`.
- [ ] Supprimer `copy.deepcopy` de l'historique (pile de hash).
- [ ] Bench avant/après (nœuds/s depuis Kiwipete).

### Étape 4 — IA forte (3–5 j)
- [ ] TT avec bornes (B6) + coup de la TT en tête d'ordonnancement.
- [ ] Move ordering MVV‑LVA + killers + history (retirer make/undo de B12).
- [ ] Quiescence search.
- [ ] Iterative deepening piloté par une **limite de temps** (ex. 2 s) au lieu de `DEPTH` fixe.
- [ ] Évaluation : phase de partie (ouverture/milieu/finale), structure de pions, roi en sécurité réelle, paires de fous.
- [ ] Optionnel : null‑move pruning, aspiration windows.
- [ ] Cible : mat en 2/3 résolu de façon fiable, profondeur effective 5–7 en milieu de partie sous 2 s.

### Étape 5 — Confort (optionnel)
- [ ] Niveaux de difficulté (profondeur/temps/bruit d'évaluation).
- [ ] Import/export FEN et PGN.
- [ ] Horloge d'échecs réelle (blitz/rapide) avec drapeau.
- [ ] Annotation d'échec `+` / mat `#` / désambiguïsation dans la notation.
- [ ] Support UCI → jouer contre Stockfish ou brancher un vrai moteur.
- [ ] Passage éventuel à `python-chess` pour les règles (garder l'IA maison).

### Effort total estimé
Corrections règles + UI : ~1 semaine. Moteur + IA : ~1,5–2 semaines de plus.
Priorité absolue : **Étape 0 puis Étape 1** (une partie avec de fausses règles est plus grave qu'une IA faible).
