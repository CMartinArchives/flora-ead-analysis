#!/usr/bin/env python3
"""Analyse structurelle et validation d'exports EAD produits par Flora.

Le script distingue deux contrôles complémentaires :

1. l'analyse structurelle, qui compte les composants ``<c>`` et repère les
   identifiants dupliqués ;
2. la validation du document contre la DTD EAD 2002 fournie avec le dépôt.

Il ne modifie jamais les fichiers analysés. Les résultats peuvent être affichés
dans le terminal ou écrits en JSON pour être conservés avec l'expérimentation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree


def normaliser_texte(element: etree._Element | None) -> str | None:
    """Réunit le texte descendant d'un élément en normalisant les espaces."""
    if element is None:
        return None
    texte = " ".join("".join(element.itertext()).split())
    return texte or None


def chemin_composant(composant: etree._Element) -> list[str]:
    """Retourne le chemin des identifiants ``<c>`` menant au composant."""
    ancetres = [
        element.get("id") or "(sans identifiant)"
        for element in composant.iterancestors("c")
    ]
    return list(reversed(ancetres)) + [
        composant.get("id") or "(sans identifiant)"
    ]


def classer_erreur(message: str) -> str:
    """Regroupe les messages détaillés de la DTD en catégories lisibles."""
    message_minuscule = message.lower()
    if "already defined" in message_minuscule or "id " in message_minuscule and "defined" in message_minuscule:
        return "identifiant duplique"
    if "no declaration for element" in message_minuscule:
        return "element non declare"
    if "content does not follow the dtd" in message_minuscule:
        return "modele de contenu non conforme"
    if "no declaration for attribute" in message_minuscule:
        return "attribut non declare"
    return "autre erreur de validation"


def charger_xml(chemin: Path) -> etree._ElementTree:
    """Charge un XML sans résoudre le système externe indiqué par son DOCTYPE."""
    parseur = etree.XMLParser(
        load_dtd=False,
        no_network=True,
        resolve_entities=False,
        recover=False,
    )
    return etree.parse(str(chemin), parseur)


def analyser_fichier(chemin_xml: Path, dtd: etree.DTD | None) -> dict[str, Any]:
    """Analyse un export et renvoie un résultat sérialisable en JSON."""
    resultat: dict[str, Any] = {"fichier": chemin_xml.name}

    try:
        document = charger_xml(chemin_xml)
    except (OSError, etree.XMLSyntaxError) as erreur:
        resultat.update(
            {
                "xml_bien_forme": False,
                "erreur_xml": str(erreur),
                "validation_dtd": None,
            }
        )
        return resultat

    racine = document.getroot()
    composants = document.xpath("//c")
    identifiants = [
        composant.get("id") for composant in composants if composant.get("id")
    ]
    occurrences = Counter(identifiants)
    doublons = {
        identifiant: nombre
        for identifiant, nombre in sorted(occurrences.items())
        if nombre > 1
    }

    # Le titre du versement est exporté par Flora dans <unititle> (sic) ou,
    # après correction, dans l'élément EAD 2002 <unittitle>.
    titre = racine.find("./archdesc/did/unittitle")
    if titre is None:
        titre = racine.find("./archdesc/did/unititle")

    resultat.update(
        {
            "xml_bien_forme": True,
            "eadid": normaliser_texte(racine.find("./eadheader/eadid")),
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

    if dtd is None:
        resultat["validation_dtd"] = None
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
    categories = Counter(erreur["categorie"] for erreur in erreurs)
    resultat.update(
        {
            "validation_dtd": valide,
            "nombre_erreurs_validation": len(erreurs),
            "categories_erreurs": dict(sorted(categories.items())),
            "erreurs_validation": erreurs,
        }
    )
    return resultat


def afficher_resume(resultat: dict[str, Any]) -> None:
    """Affiche un résumé humainement lisible d'un résultat."""
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
        print(f"Validation DTD : {'valide' if validation else 'invalide'}")
        print(
            f"Erreurs de validation : {resultat['nombre_erreurs_validation']} "
            f"{resultat['categories_erreurs']}"
        )


def construire_cli() -> argparse.ArgumentParser:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        "xml",
        nargs="+",
        type=Path,
        help="un ou plusieurs exports XML à analyser",
    )
    analyseur.add_argument(
        "--dtd",
        type=Path,
        help="DTD EAD 2002 utilisée pour la validation",
    )
    analyseur.add_argument(
        "--json",
        dest="sortie_json",
        type=Path,
        help="écrit également les résultats détaillés dans ce fichier JSON",
    )
    return analyseur


def main() -> int:
    arguments = construire_cli().parse_args()

    dtd = None
    if arguments.dtd:
        try:
            dtd = etree.DTD(str(arguments.dtd))
        except (OSError, etree.DTDParseError) as erreur:
            print(f"Impossible de charger la DTD : {erreur}", file=sys.stderr)
            return 2

    resultats = [analyser_fichier(chemin, dtd) for chemin in arguments.xml]
    for resultat in resultats:
        afficher_resume(resultat)

    if arguments.sortie_json:
        arguments.sortie_json.parent.mkdir(parents=True, exist_ok=True)
        arguments.sortie_json.write_text(
            json.dumps(resultats, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nRapport JSON écrit dans {arguments.sortie_json}")

    # Un code de sortie non nul facilite l'emploi du script dans une chaîne de
    # tests : 1 signale un XML mal formé ou un document invalide contre la DTD.
    echec = any(
        not resultat.get("xml_bien_forme")
        or resultat.get("validation_dtd") is False
        for resultat in resultats
    )
    return 1 if echec else 0


if __name__ == "__main__":
    raise SystemExit(main())
