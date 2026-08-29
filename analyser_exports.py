#!/usr/bin/env python3

"""Analyse la structure d'exports EAD et les valide contre une DTD.

La validation suit la méthode décrite dans la documentation de lxml.
L'analyse structurelle repose sur les fonctions courantes de lxml pour
parcourir l'arborescence d'un instrument EAD.

Les contrôles portant sur le nombre de composants, les identifiants répétés
et leurs chemins hiérarchiques ont été définis pour étudier les anomalies
observées dans les exports Flora.

Référence technique :
https://lxml.de/validation.html
"""

# IMPORTS

# Lit les fichiers et les options indiqués dans la ligne de commande.
import argparse

# Transforme les résultats de l'analyse en données JSON.
import json

# Permet d'afficher les erreurs séparément et de renvoyer un code de sortie.
import sys

# Compte les occurrences des identifiants et des catégories d'erreurs.
from collections import Counter

# Représente les chemins vers les fichiers XML, la DTD et le rapport JSON.
from pathlib import Path

# Lit les fichiers XML et permet de les valider contre une DTD.
from lxml import etree


# OUTILS COMMUNS

def normaliser_texte(element):
    """Récupère le texte d'un élément et supprime les espaces inutiles."""
    if element is None:
        return None

    texte = " ".join("".join(element.itertext()).split())
    return texte or None


def charger_xml(chemin):
    """Charge un XML sans utiliser automatiquement la DTD de son DOCTYPE."""
    parseur = etree.XMLParser(
        load_dtd=False,
        no_network=True,
        resolve_entities=False,
        recover=False,
    )

    return etree.parse(str(chemin), parseur)


# ANALYSE DE LA HIÉRARCHIE EAD

def chemin_composant(composant):
    """Reconstitue le chemin hiérarchique menant à un composant <c>."""
    ancetres = [
        element.get("id") or "(sans identifiant)"
        for element in composant.iterancestors("c")
    ]

    return list(reversed(ancetres)) + [
        composant.get("id") or "(sans identifiant)"
    ]


# VALIDATION CONTRE LA DTD

def classer_erreur(message):
    """Classe les erreurs de validation dans plusieurs catégories."""
    message = message.lower()

    if (
        "already defined" in message
        or ("id " in message and "defined" in message)
    ):
        return "identifiant duplique"

    if "no declaration for element" in message:
        return "element non declare"

    if "content does not follow the dtd" in message:
        return "modele de contenu non conforme"

    if "no declaration for attribute" in message:
        return "attribut non declare"

    return "autre erreur de validation"


# ANALYSE D'UN EXPORT

def analyser_fichier(chemin_xml, dtd):
    """Analyse un fichier XML et rassemble ses résultats."""
    resultat = {
        "fichier": chemin_xml.name
    }

    try:
        document = charger_xml(chemin_xml)

    except (OSError, etree.XMLSyntaxError) as erreur:
        resultat.update(
            {
                "xml_bien_forme": False,
                "erreur_xml": str(erreur),
                "validation_dtd": None,
                "nombre_erreurs_validation": 0,
                "categories_erreurs": {},
                "erreurs_validation": [],
            }
        )
        return resultat

    racine = document.getroot()

    # Recherche de tous les composants archivistiques <c>.
    composants = document.findall(".//c")

    # Relevé et comptage de leurs identifiants.
    identifiants = [
        composant.get("id")
        for composant in composants
        if composant.get("id")
    ]

    occurrences = Counter(identifiants)

    doublons = {
        identifiant: nombre
        for identifiant, nombre in sorted(occurrences.items())
        if nombre > 1
    }

    # Flora emploie <unititle> à la place de la balise EAD <unittitle>.
    # Les deux formes sont recherchées pour analyser aussi le fichier corrigé.
    titre = racine.find("./archdesc/did/unittitle")

    if titre is None:
        titre = racine.find("./archdesc/did/unititle")

    resultat.update(
        {
            "xml_bien_forme": True,
            "eadid": normaliser_texte(
                racine.find("./eadheader/eadid")
            ),
            "titre": normaliser_texte(titre),
            "nombre_composants": len(composants),
            "nombre_identifiants": len(identifiants),
            "nombre_identifiants_uniques": len(occurrences),
            "identifiants_dupliques": doublons,
            "composants": [
                {
                    "id": composant.get("id"),
                    "level": composant.get("level"),
                    "otherlevel": composant.get("otherlevel"),
                    "chemin": chemin_composant(composant),
                }
                for composant in composants
            ],
        }
    )

    # La validation n'est effectuée que si une DTD a été indiquée.
    if dtd is None:
        resultat["validation_dtd"] = None
        resultat["nombre_erreurs_validation"] = 0
        resultat["categories_erreurs"] = {}
        resultat["erreurs_validation"] = []
        return resultat

    valide = dtd.validate(document)

    erreurs = [
        {
            "ligne": erreur.line,
            "categorie": classer_erreur(erreur.message),
            "message": erreur.message,
        }
        for erreur in dtd.error_log
    ]

    categories = Counter(
        erreur["categorie"]
        for erreur in erreurs
    )

    resultat.update(
        {
            "validation_dtd": valide,
            "nombre_erreurs_validation": len(erreurs),
            "categories_erreurs": dict(
                sorted(categories.items())
            ),
            "erreurs_validation": erreurs,
        }
    )

    return resultat


# AFFICHAGE DES RÉSULTATS

def afficher_resume(resultat):
    """Affiche les principaux résultats dans le terminal."""
    print(f"\n{resultat['fichier']}")
    print("-" * len(resultat["fichier"]))

    if not resultat.get("xml_bien_forme"):
        print(f"XML mal formé : {resultat['erreur_xml']}")
        return

    print(f"Composants <c> : {resultat['nombre_composants']}")

    print(
        "Identifiants : "
        f"{resultat['nombre_identifiants']} occurrence(s), "
        f"{resultat['nombre_identifiants_uniques']} valeur(s) unique(s)"
    )

    doublons = resultat["identifiants_dupliques"]
    print(f"Identifiants dupliqués : {doublons or 'aucun'}")

    validation = resultat.get("validation_dtd")

    if validation is None:
        print("Validation DTD : non demandée")

    else:
        etat = "valide" if validation else "invalide"
        print(f"Validation DTD : {etat}")

        print(
            "Erreurs de validation : "
            f"{resultat['nombre_erreurs_validation']} "
            f"{resultat['categories_erreurs']}"
        )


# ARGUMENTS DE LA LIGNE DE COMMANDE

def construire_arguments():
    """Définit les arguments acceptés par le script."""
    analyseur = argparse.ArgumentParser(
        description=__doc__
    )

    analyseur.add_argument(
        "xml",
        nargs="+",
        type=Path,
        help="un ou plusieurs exports XML à analyser",
    )

    analyseur.add_argument(
        "--dtd",
        type=Path,
        help="DTD utilisée pour valider les fichiers",
    )

    analyseur.add_argument(
        "--json",
        dest="sortie_json",
        type=Path,
        help="fichier JSON dans lequel enregistrer les résultats",
    )

    return analyseur


# EXÉCUTION DU SCRIPT

def main():
    """Lance l'analyse des fichiers indiqués dans la commande."""
    arguments = construire_arguments().parse_args()

    dtd = None

    if arguments.dtd:
        try:
            dtd = etree.DTD(str(arguments.dtd))

        except (OSError, etree.DTDParseError) as erreur:
            print(
                f"Impossible de charger la DTD : {erreur}",
                file=sys.stderr,
            )
            return 2

    resultats = [
        analyser_fichier(chemin, dtd)
        for chemin in arguments.xml
    ]

    for resultat in resultats:
        afficher_resume(resultat)

    # Création facultative du rapport JSON.
    if arguments.sortie_json:
        arguments.sortie_json.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        arguments.sortie_json.write_text(
            json.dumps(
                resultats,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            f"\nRapport JSON écrit dans "
            f"{arguments.sortie_json}"
        )

    # Le code 1 signale un XML mal formé ou invalide contre la DTD.
    echec = any(
        not resultat.get("xml_bien_forme")
        or resultat.get("validation_dtd") is False
        for resultat in resultats
    )

    return 1 if echec else 0


if __name__ == "__main__":
    raise SystemExit(main())
