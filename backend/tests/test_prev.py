"""Tests unitaires de la couche pure (sans BDD) du générateur."""
from __future__ import annotations

import pytest

from app.services.poem_generator import (
    WordCatalog,
    _capitalize_like,
    _last_meaningful_word_index,
    _normalize_verper,
    _strip_trailing_symbols,
    expand_form,
    prev,
)


@pytest.fixture
def catalog() -> WordCatalog:
    return WordCatalog(
        mots_possibles={"chat", "chien"},
        syll_possibles={"t@t": "t@t", "se": "se", "ã": "ã"},
        aide_phon=[],
    )


class TestNormalizeVerper:
    def test_2s_quand_mot_finit_par_s(self):
        assert _normalize_verper("manges", "1s-2s-3s") == "%2s%"

    def test_1s_prioritaire_si_present(self):
        assert _normalize_verper("mange", "1s-3s") == "%1s%"

    def test_3s_si_pas_de_1s(self):
        assert _normalize_verper("mange", "3s") == "%3s%"

    def test_autre_personne_garde_premier_segment(self):
        assert _normalize_verper("mangeons", "1p-2p") == "%1p%"

    def test_chaine_vide(self):
        assert _normalize_verper("mot", "") == ""


class TestPrev:
    def test_forme_vide_renvoie_erreur(self, catalog):
        result, err1, err2 = prev(catalog, "", "", "")
        assert result is None
        assert "aucune forme" in err1.lower()

    def test_forme_simple_sans_options(self, catalog):
        result, err1, err2 = prev(catalog, "ABBA", "", "")
        assert result is not None
        assert err1 == "" and err2 == ""
        # Une ligne par lettre, 12 syllabes par défaut (= 11 underscores)
        lignes = [l for l in result.split("\n") if l]
        assert len(lignes) == 4
        assert all(l.count("_") == 11 for l in lignes)

    def test_syllabes_explicites_par_vers(self, catalog):
        result, _, _ = prev(catalog, "ABAB", "1=8,2=8,3=8,4=8", "")
        lignes = [l for l in result.split("\n") if l]
        assert all(l.count("_") == 7 for l in lignes)

    def test_propagation_du_compte_syllabes(self, catalog):
        # Si seul le 1er vers est précisé, les suivants héritent.
        result, _, _ = prev(catalog, "ABBA", "1=10", "")
        lignes = [l for l in result.split("\n") if l]
        assert all(l.count("_") == 9 for l in lignes)

    def test_syllabes_mal_formatees(self, catalog):
        result, err1, err2 = prev(catalog, "ABBA", "blabla", "")
        assert result is None
        assert "mal écrit" in err1

    def test_syllabes_sup_a_12_clamp(self, catalog):
        result, err1, _ = prev(catalog, "A", "1=20", "")
        assert result is not None
        assert "max" in err1

    def test_syllabes_inf_a_1(self, catalog):
        result, err1, _ = prev(catalog, "A", "1=0", "")
        assert result is not None
        assert "min" in err1.lower()

    def test_rime_appliquee_sur_lettre(self, catalog):
        result, err1, err2 = prev(catalog, "ABBA", "1=12", "A=t@t")
        assert result is not None
        # La syllabe imposée doit apparaître dans la sortie
        assert "t@t." in result
        assert err1 == ""

    def test_rime_inexistante(self, catalog):
        result, err1, err2 = prev(catalog, "ABBA", "1=12", "A=zzzz")
        assert result is not None
        assert "mal écrites" in err1
        assert "n'existe pas" in err2


class TestExpandForm:
    def test_round_trip_simple(self):
        forme, nbsyll = expand_form("_ _ _ A\n_ _ _ B\n_ _ _ B\n_ _ _ A\n")
        # La forme contient les lettres séparées par _ ; un espace de
        # paragraphe peut être ajouté en fin (cf. expand_form).
        assert forme.startswith("A_B_B_A_")
        assert nbsyll == [4, 4, 4, 4]

    def test_paragraphes_separes_par_ligne_vide(self):
        forme, nbsyll = expand_form("_ A\n_ B\n\n_ C\n")
        assert " " in forme  # un séparateur de paragraphe
        assert nbsyll == [2, 2, 2]


class TestLastMeaningfulWordIndex:
    def test_phrase_simple(self):
        assert _last_meaningful_word_index(["Le", "chat"]) == 1

    def test_phrase_avec_ponctuation_finale(self):
        # Token isolé "." à la fin n'est pas un mot.
        assert _last_meaningful_word_index(["Le", "chat", ","]) == 1

    def test_phrase_vide(self):
        assert _last_meaningful_word_index([]) == -1

    def test_seulement_des_symboles(self):
        assert _last_meaningful_word_index([",", "."]) == -1


class TestStripTrailingSymbols:
    def test_pas_de_symbole(self):
        assert _strip_trailing_symbols("chat") == "chat"

    def test_un_symbole(self):
        assert _strip_trailing_symbols("chat,") == "chat"

    def test_plusieurs_symboles(self):
        assert _strip_trailing_symbols("chat...") == "chat"

    def test_que_des_symboles(self):
        assert _strip_trailing_symbols(",.;") == ""


class TestCapitalizeLike:
    def test_minuscule_garde_minuscule(self):
        assert _capitalize_like("chat", "chien") == "chien"

    def test_majuscule_capitalise(self):
        assert _capitalize_like("Chat", "chien") == "Chien"

    def test_garde_le_reste_du_mot(self):
        assert _capitalize_like("Aujourd'hui", "etoile") == "Etoile"

    def test_mot_vide(self):
        assert _capitalize_like("Chat", "") == ""
