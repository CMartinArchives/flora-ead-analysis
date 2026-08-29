# Analyse des exports EAD de Flora

Ce dépôt accompagne le mémoire consacré à l’architecture documentaire des Archives historiques de la Faculté de médecine de l’Université de Montpellier. Il rassemble les fichiers et les scripts utilisés en 2026 pour analyser l’export XML-EAD du module Archives de Flora, dans la version de préproduction disponible pendant le stage.

Le script `analyser_exports.py` peut être utilisé pour examiner d’autres fichiers en EAD 2002, à condition de lui fournir la DTD correspondante. Les contrôles structurels et les catégories d’erreurs qu’il emploie ont toutefois été définis à partir des exports Flora étudiés. Le script `corriger_export_minimal.py` est, quant à lui, strictement limité au fichier minimal fourni dans ce dépôt et ne constitue pas un outil général de correction des fichiers EAD.

Les résultats présentés ne valent pas pour toutes les versions ou configurations de Flora. Ils concernent uniquement l’instance et les fichiers testés au moment de l’expérimentation, à l’été 2026.

## Contenu du dépôt

```text
.
├── analyser_exports.py          analyse de la structure des exports et validation contre la DTD EAD 2002
├── corriger_export_minimal.py   correction expérimentale du seul export minimal à plat
├── requirements.txt             bibliothèque Python nécessaire au fonctionnement des scripts (lxml)
├── dtd/
│   └── ead.dtd                  DTD EAD 2002 utilisée pour valider les exports
├── exports/
│   ├── 01_export_minimal_a_plat.xml
│   ├── 02_export_a_plat_versement_enrichi.xml
│   ├── 03_export_a_plat_article_enrichi.xml
│   ├── 04_export_hierarchique_deux_niveaux.xml
│   ├── 05_export_hierarchique_trois_niveaux.xml
│   └── 06_export_hierarchique_deux_branches.xml
└── rapports/
    ├── analyse.json
    └── 01_export_minimal_a_plat_corrige.xml
```

Le dossier `rapports/` contient les fichiers produits par les deux scripts. `analyse.json`, généré par `analyser_exports.py`, rassemble les résultats de l’analyse des six exports. `01_export_minimal_a_plat_corrige.xml`, généré par `corriger_export_minimal.py`, correspond à la version corrigée du premier export et sert à vérifier que les corrections expérimentales permettent de le rendre conforme à la DTD EAD 2002.

Les noms de personnes utilisés pour les essais ont été remplacés. Cette anonymisation ne modifie ni les balises XML, ni leur ordre, ni les relations hiérarchiques, ni les identifiants archivistiques étudiés.

## Méthode et assistance à la rédaction des scripts

Les scripts utilisent des fonctions courantes de Python et de la bibliothèque `lxml` pour lire et parcourir des fichiers XML, rechercher des éléments, compter des identifiants, modifier une arborescence et valider un document contre une DTD. Leur rédaction s’appuie principalement sur la [documentation de Python](https://docs.python.org/3/) ainsi que sur le [tutoriel](https://lxml.de/tutorial.html) et la [documentation relative à la validation](https://lxml.de/validation.html) de `lxml`.

Les scénarios d’essai, les champs saisis dans Flora, les anomalies recherchées et l’interprétation archivistique des résultats ont été définis dans le cadre du stage. ChatGPT (modèle GPT-5) a été utilisé comme aide à la rédaction et à la vérification du code, en particulier pour les opérations les plus techniques : parcours des relations parent–enfant, repérage des identifiants répétés, classement des messages produits par la DTD, déplacement d’éléments XML sans perte de contenu, production du rapport JSON et gestion des arguments de la ligne de commande. Les scripts ont ensuite été adaptés aux exports étudiés et leurs résultats contrôlés sur les fichiers publiés dans ce dépôt.

## Fichiers d’essai analysés

Dans les essais « à plat », les articles sont placés au même niveau dans l’instrument : aucun article n’est rattaché à un autre comme enfant. Les essais « enrichis » ajoutent aux informations minimales — principalement la cote et l’intitulé — différents champs descriptifs ou de gestion afin d’observer leur restitution dans l’export EAD.

| Fichier | Configuration testée | Résultat structurel |
|---|---|---|
| `01_export_minimal_a_plat.xml` | Un versement contenant trois articles placés au même niveau et décrits par un nombre minimal d’informations | 3 composants `<c>` et 3 identifiants uniques |
| `02_export_a_plat_versement_enrichi.xml` | La même structure à plat, avec une description plus complète du versement et des articles peu renseignés | 3 composants `<c>` et aucun identifiant répété |
| `03_export_a_plat_article_enrichi.xml` | La même structure à plat, avec une description plus complète du versement et l’ajout de champs descriptifs et de gestion à un article | 3 composants `<c>` et aucun identifiant répété |
| `04_export_hierarchique_deux_niveaux.xml` | Une structure à deux niveaux comprenant un article parent et deux dossiers qui lui sont rattachés | 5 composants `<c>` pour 3 unités : `TEST-2` et `TEST-3` sont chacun exportés deux fois |
| `05_export_hierarchique_trois_niveaux.xml` | Une structure à trois niveaux comprenant un article, un dossier rattaché à cet article et un sous-dossier rattaché au dossier | 6 composants `<c>` pour 3 unités : `TEST2-2` est exporté deux fois et `TEST2-3` trois fois |
| `06_export_hierarchique_deux_branches.xml` | Deux branches distinctes comprenant chacune un article parent et un dossier enfant | 6 composants `<c>` pour 4 unités : `TEST3-2` et `TEST3-4` sont chacun exportés deux fois |

Un dernier essai portait sur l’export simultané de plusieurs versements. Flora ayant produit une archive ZIP vide de 22 octets, aucun fichier XML n’a pu être analysé pour ce test.

## Installation

Python 3.10 ou une version plus récente est recommandé.

Les commandes suivantes créent un environnement Python séparé, l’activent et installent la bibliothèque `lxml`, utilisée pour lire et valider les fichiers XML :

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Lancer l’analyse

```bash
python3 analyser_exports.py \
  --dtd dtd/ead.dtd \
  --json rapports/analyse.json \
  exports/*.xml
```

Pour chaque export, le script :

- vérifie que le fichier respecte les règles générales d’écriture du XML ;
- compte les composants archivistiques `<c>` ;
- relève leurs identifiants et signale ceux qui apparaissent plusieurs fois ;
- restitue la place de chaque composant dans l’arborescence ;
- vérifie la conformité du fichier avec la DTD EAD 2002 ;
- enregistre les résultats détaillés dans `rapports/analyse.json`.

Le script renvoie le code de sortie `1` lorsqu’au moins un export n’est pas conforme à la DTD. Ce résultat est normal ici, puisque l’analyse vise précisément à relever les erreurs présentes dans les fichiers produits par Flora. Il ne signifie donc pas que le script a échoué.

## Correction expérimentale de l’export minimal

Le second script reproduit la correction expérimentale appliquée au seul export minimal à plat :

```bash
python3 corriger_export_minimal.py \
  exports/01_export_minimal_a_plat.xml \
  rapports/01_export_minimal_a_plat_corrige.xml

python3 analyser_exports.py \
  --dtd dtd/ead.dtd \
  rapports/01_export_minimal_a_plat_corrige.xml
```

Le script effectue plusieurs corrections précises :

- il remplace la balise erronée `<unititle>` par `<unittitle>` ;
- il retire les balises `<admininfo>` et `<add>`, qui n’appartiennent pas à la DTD EAD 2002, tout en conservant les informations qu’elles contiennent ;
- il replace le contenu de `<acqinfo>`, `<accessrestrict>` et `<otherfindaid>` dans les sous-éléments attendus par la DTD ;
- il complète les blocs `<did>` qui ne contiennent qu’un titre de rubrique `<head>`.

Après ces transformations, l’export minimal est conforme à la DTD EAD 2002. Ce résultat montre que certaines erreurs peuvent être corrigées automatiquement lorsqu’elles suivent une règle stable.

Ce script reste cependant un essai limité. Il ne traite pas l’ensemble des champs présents dans les exports enrichis et ne reconstruit pas les arborescences dans lesquelles des unités sont répétées. Supprimer automatiquement les doublons ne suffirait pas : il faudrait également déterminer la place correcte de chaque unité dans la hiérarchie. Les exports hiérarchiques sont donc conservés comme fichiers d’analyse et ne sont pas corrigés par ce script.

## Principaux résultats

- Aucun des six exports originaux n’est conforme en l’état à la DTD EAD 2002 indiquée dans son `DOCTYPE`.

- L’export minimal produit 29 erreurs de validation.

- Plusieurs informations sont bien placées dans des balises EAD adaptées, mais certaines balises employées, leur contenu ou leur ordre ne respectent pas la DTD.

- Les trois exports à plat conservent un identifiant unique pour chaque article.

- Dès qu’une relation parent–enfant est créée dans Flora, les unités enfants sont exportées une première fois seules, puis une nouvelle fois à l’intérieur de leur parent.

- Dans l’essai à trois niveaux, le nombre de répétitions augmente avec la profondeur : le dossier apparaît deux fois et le sous-dossier trois fois.

## Limites de l’analyse

La validation contre la DTD permet de vérifier si les balises, leur ordre et leur organisation respectent les règles de l’EAD 2002. Elle ne permet pas, à elle seule, de juger la qualité archivistique d’un instrument ni de garantir qu’il sera correctement repris par Calames ou FranceArchives.

L’analyse combine donc trois contrôles complémentaires : la validation contre la DTD, le repérage des identifiants répétés et l’examen de la hiérarchie produite dans chaque export.
