# Analyse des exports EAD de Flora

Ce dépôt accompagne le mémoire consacré à l'architecture documentaire des
Archives historiques de la Faculté de médecine de l'Université de Montpellier.
Il documente les contrôles réalisés en 2026 sur l'export XML-EAD du module
Archives de Flora dans l'instance de préproduction alors disponible.

Les résultats ne constituent pas une évaluation générale de toutes les versions
de Flora. Ils décrivent uniquement les fichiers produits par la configuration
testée au moment de l'expérimentation.

## Contenu du dépôt

```text
.
├── analyser_exports.py          comptage des composants, détection des identifiants dupliqués et validation contre la DTD EAD 2002
├── corriger_export_minimal.py   correction expérimentale des erreurs de validation du seul export minimal à plat
├── requirements.txt             dépendance Python nécessaire à l’analyse et à la validation des fichiers XML (`lxml`)
├── tests/
│   └── test_analyse.py          vérification automatisée des résultats attendus
├── dtd/
│   └── ead.dtd                  DTD EAD 2002 employée pendant les tests
├── exports/
│   ├── 01_export_minimal_a_plat.xml
│   ├── 02_export_a_plat_versement_enrichi.xml
│   ├── 03_export_a_plat_article_enrichi.xml
│   ├── 04_export_hierarchique_deux_niveaux.xml
│   ├── 05_export_hierarchique_trois_niveaux.xml
│   └── 06_export_hierarchique_deux_branches.xml
└── rapports/
    └── analyse.json             résultats détaillés produits automatiquement par le script d’analyse
```

Les valeurs nominatives saisies pour les essais ont été remplacées dans les
copies publiables. Cette anonymisation ne modifie ni les éléments XML, ni leur
ordre, ni les relations hiérarchiques, ni les identifiants archivistiques sur
lesquels porte l'analyse.

## Fichiers d’essai analysés

Les essais à plat décrivent des articles placés au même niveau dans l’instrument, sans relation parent–enfant entre eux. Les essais dits « enrichis » ajoutent aux identifiants et intitulés minimaux des informations descriptives ou de gestion afin de vérifier leur transposition dans les éléments EAD correspondants.

| Fichier | Configuration testée | Résultat structurel |
|---|---|---|
| `01_export_minimal_a_plat.xml` | Un versement contenant trois articles frères, décrits uniquement par les informations minimales nécessaires à leur identification | 3 composants `<c>` et 3 identifiants uniques |
| `02_export_a_plat_versement_enrichi.xml` | La même structure sans relation parent–enfant, avec une description détaillée au niveau du versement et des articles volontairement peu renseignés | 3 composants `<c>` et aucun identifiant dupliqué |
| `03_export_a_plat_article_enrichi.xml` | La même structure à plat, avec une description détaillée du versement et l’ajout de champs descriptifs et de gestion au niveau d’un article | 3 composants `<c>` et aucun identifiant dupliqué |
| `04_export_hierarchique_deux_niveaux.xml` | Une arborescence à deux niveaux composée d’un article parent et de deux dossiers enfants | 5 composants `<c>` pour 3 unités : `TEST-2` et `TEST-3` sont chacun exportés deux fois |
| `05_export_hierarchique_trois_niveaux.xml` | Une branche à trois niveaux composée d’un article, d’un dossier enfant et d’un sous-dossier rattaché à ce dernier | 6 composants `<c>` pour 3 unités : `TEST2-2` est exporté deux fois et `TEST2-3` trois fois |
| `06_export_hierarchique_deux_branches.xml` | Deux branches indépendantes comprenant chacune un article parent et un dossier enfant | 6 composants `<c>` pour 4 unités : les dossiers `TEST3-2` et `TEST3-4` sont chacun exportés deux fois |

Un dernier essai portait sur l’export simultané de plusieurs versements. Flora ayant produit une archive ZIP vide de 22 octets, ce test n’a fourni aucun document XML susceptible d’être analysé.

## Installation

Python 3.10 ou une version ultérieure est recommandé.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Reproduire l'analyse

```bash
python3 analyser_exports.py \
  --dtd dtd/ead.dtd \
  --json rapports/analyse.json \
  exports/*.xml
```

Le script vérifie que chaque fichier est un XML bien formé, compte les
composants `<c>`, compare le nombre d'occurrences d'identifiants à leur nombre
de valeurs uniques, restitue le chemin hiérarchique de chaque composant et
valide le document contre la DTD EAD 2002. Le rapport JSON conserve les messages
détaillés de validation et une catégorisation synthétique des erreurs.

Le programme renvoie le code de sortie `1` dès qu'un document est mal formé ou
invalide contre la DTD. Ce résultat est attendu pour les exports originaux
étudiés ; il permet notamment d'employer le contrôle dans une intégration
continue sans confondre exécution réussie du script et validité des documents.

## Preuve de concept de correction

Le second script reproduit le retraitement expérimental appliqué au seul export
minimal :

```bash
python3 corriger_export_minimal.py \
  exports/01_export_minimal_a_plat.xml \
  rapports/01_export_minimal_a_plat_corrige.xml

python3 analyser_exports.py \
  --dtd dtd/ead.dtd \
  rapports/01_export_minimal_a_plat_corrige.xml
```

Il remplace `<unititle>` par `<unittitle>`, retire les enveloppes
`<admininfo>` et `<add>` en conservant leurs enfants, restructure le contenu de
`<acqinfo>`, `<accessrestrict>` et `<otherfindaid>`, puis complète les blocs
`<did>` qui ne contiennent qu'un `<head>`. Cette transformation démontre que
plusieurs anomalies du cas minimal suivent des règles automatisables.

Elle ne constitue toutefois pas une chaîne de conversion pérenne : elle ne
traite ni tous les champs des exports enrichis, ni la reconstruction des
arborescences dupliquées. Les fichiers hiérarchiques doivent donc rester des
objets d'analyse et non être « corrigés » automatiquement par suppression des
occurrences répétées, car leur seule position dans l'export ne suffit pas à
garantir la reconstruction de l'intention descriptive initiale.

## Exécuter les tests automatisés

```bash
python3 -m unittest discover -s tests -v
```

Les tests vérifient les nombres de composants et d'identifiants uniques, les
duplications attendues dans les trois arborescences et la validité du fichier
minimal après application de la preuve de concept.

## Principaux constats reproductibles

* aucun export fourni ne valide en l'état contre la DTD EAD 2002 annoncée dans
  son `DOCTYPE` ;
* le cas minimal produit 29 erreurs de validation ;
* plusieurs champs sont bien associés à des éléments EAD spécialisés, mais
  certaines structures ou imbrications ne respectent pas leur modèle de
  contenu ;
* les essais à plat conservent des identifiants uniques ;
* dès qu'une relation parent--enfant est introduite, les unités enfants sont
  exportées à la fois comme composants autonomes et sous leur parent ;
* la répétition augmente avec la profondeur dans l'essai `TEST2`.

## Périmètre méthodologique

La validation contre une DTD vérifie une conformité syntaxique et structurelle.
Elle ne suffit pas à établir la qualité archivistique ou l'interopérabilité
effective d'un instrument. L'analyse associe donc validation, comptage des
identifiants et examen des relations hiérarchiques.
