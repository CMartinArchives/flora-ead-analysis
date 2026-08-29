#!/usr/bin/env python3
"""Correction expérimentale de l'export minimal à plat de Flora.

Ce script reproduit le retraitement décrit dans le mémoire. Il corrige des
anomalies régulières du seul cas minimal : nom de ``<unittitle>``, enveloppes
héritées ``<admininfo>`` et ``<add>``, contenus textuels non structurés et
``<did>`` de composants dépourvus d'élément d'identification.

Il ne reconstruit pas les hiérarchies et n'est pas
un convertisseur général des exports Flora. 
Le fichier source n'est jamais modifié : un nouveau fichier est toujours produit.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lxml import etree


ELEMENTS_ENVELOPPES = {"admininfo", "add"}
ELEMENTS_TEXTE_STRUCTURE = {"otherfindaid", "accessrestrict", "acqinfo"}


def texte_significatif(texte: str | None) -> bool:
    return bool(texte and texte.strip())


def ajouter_texte_dans_paragraphe(element: etree._Element) -> None:
    """Place le texte direct et les enfants en ligne dans un élément ``<p>``.

    EAD 2002 n'autorise pas le texte libre ni ``persname``/``corpname``
    directement dans les éléments concernés. Un paragraphe constitue ici
    l'enveloppe textuelle minimale attendue par la DTD.
    """
    contenu_existant = list(element)
    texte_initial = element.text

    # Certains exports mélangent un paragraphe déjà valide et du texte placé
    # dans sa ``tail`` (cas de <accessrestrict>). Il faut alors conserver le
    # paragraphe existant et transformer seulement le texte résiduel, sans
    # créer l'imbrication interdite <p><p>...</p></p>.
    if contenu_existant and all(enfant.tag == "p" for enfant in contenu_existant):
        element.text = None
        if texte_significatif(texte_initial):
            paragraphe_initial = etree.Element("p")
            paragraphe_initial.text = texte_initial
            element.insert(0, paragraphe_initial)
        for enfant in list(element):
            texte_apres = enfant.tail
            enfant.tail = None
            if texte_significatif(texte_apres):
                paragraphe_apres = etree.Element("p")
                paragraphe_apres.text = texte_apres
                element.insert(element.index(enfant) + 1, paragraphe_apres)
        return

    # Si l'élément possède déjà uniquement des paragraphes et aucun texte
    # direct significatif, aucune transformation n'est nécessaire.
    if (
        not texte_significatif(texte_initial)
        and contenu_existant
        and all(enfant.tag == "p" for enfant in contenu_existant)
        and not any(texte_significatif(enfant.tail) for enfant in contenu_existant)
    ):
        return

    paragraphe = etree.Element("p")
    paragraphe.text = texte_initial
    element.text = None

    for enfant in contenu_existant:
        element.remove(enfant)
        paragraphe.append(enfant)

    element.append(paragraphe)


def deplier_enveloppe(enveloppe: etree._Element) -> None:
    """Remplace une enveloppe non EAD 2002 par ses enfants, sans les perdre."""
    parent = enveloppe.getparent()
    if parent is None:
        return
    position = parent.index(enveloppe)
    for enfant in list(enveloppe):
        enveloppe.remove(enfant)
        parent.insert(position, enfant)
        position += 1
    parent.remove(enveloppe)


def completer_did_composants(document: etree._ElementTree) -> None:
    """Ajoute un ``<unitid>`` aux ``<did>`` ne contenant qu'un ``<head>``."""
    for composant in document.xpath("//c"):
        did = composant.find("did")
        if did is None:
            continue
        elements_identification = [enfant for enfant in did if enfant.tag != "head"]
        if not elements_identification:
            unitid = etree.Element("unitid")
            unitid.text = composant.get("id") or "Identifiant non renseigné"
            did.append(unitid)


def corriger(source: Path, destination: Path) -> None:
    parseur = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
    document = etree.parse(str(source), parseur)

    # Flora emploie <unititle> alors que la DTD EAD 2002 définit <unittitle>.
    for element in document.xpath("//unititle"):
        element.tag = "unittitle"

    # Les enfants sont conservés et replacés à l'endroit de l'enveloppe.
    for nom in ELEMENTS_ENVELOPPES:
        for enveloppe in list(document.xpath(f"//{nom}")):
            deplier_enveloppe(enveloppe)

    # Une fois les enveloppes supprimées, les éléments EAD sont restructurés.
    for nom in ELEMENTS_TEXTE_STRUCTURE:
        for element in document.xpath(f"//{nom}"):
            ajouter_texte_dans_paragraphe(element)

    completer_did_composants(document)

    destination.parent.mkdir(parents=True, exist_ok=True)
    document.write(
        str(destination),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
        doctype=(
            '<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd '
            '(Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">'
        ),
    )


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path, help="export minimal original")
    cli.add_argument("destination", type=Path, help="nouveau fichier corrigé")
    arguments = cli.parse_args()
    corriger(arguments.source, arguments.destination)
    print(f"Fichier corrigé écrit dans {arguments.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
