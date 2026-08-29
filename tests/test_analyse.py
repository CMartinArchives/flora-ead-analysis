"""Tests de non-régression sur les six exports documentés."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from lxml import etree

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from analyser_exports import analyser_fichier  # noqa: E402
from corriger_export_minimal import corriger  # noqa: E402


class AnalyseExportsFlora(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dtd = etree.DTD(str(RACINE / "dtd" / "ead.dtd"))

    def analyser(self, nom: str):
        return analyser_fichier(RACINE / "exports" / nom, self.dtd)

    def test_export_minimal(self) -> None:
        resultat = self.analyser("01_export_minimal_a_plat.xml")
        self.assertEqual(resultat["nombre_composants"], 3)
        self.assertEqual(resultat["nombre_identifiants_uniques"], 3)
        self.assertEqual(resultat["nombre_erreurs_validation"], 29)
        self.assertFalse(resultat["validation_dtd"])

    def test_hierarchie_test(self) -> None:
        resultat = self.analyser("04_export_hierarchique_deux_niveaux.xml")
        self.assertEqual(resultat["nombre_composants"], 5)
        self.assertEqual(
            resultat["identifiants_dupliques"],
            {"TEST-2": 2, "TEST-3": 2},
        )

    def test_hierarchie_test2(self) -> None:
        resultat = self.analyser("05_export_hierarchique_trois_niveaux.xml")
        self.assertEqual(resultat["nombre_composants"], 6)
        self.assertEqual(
            resultat["identifiants_dupliques"],
            {"TEST2-2": 2, "TEST2-3": 3},
        )

    def test_hierarchie_test3(self) -> None:
        resultat = self.analyser("06_export_hierarchique_deux_branches.xml")
        self.assertEqual(resultat["nombre_composants"], 6)
        self.assertEqual(
            resultat["identifiants_dupliques"],
            {"TEST3-2": 2, "TEST3-4": 2},
        )

    def test_correction_du_cas_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as dossier:
            destination = Path(dossier) / "corrige.xml"
            corriger(RACINE / "exports" / "01_export_minimal_a_plat.xml", destination)
            resultat = analyser_fichier(destination, self.dtd)
        self.assertTrue(resultat["validation_dtd"])
        self.assertEqual(resultat["nombre_erreurs_validation"], 0)


if __name__ == "__main__":
    unittest.main()
