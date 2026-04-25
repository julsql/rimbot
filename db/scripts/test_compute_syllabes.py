"""Tests unitaires pour compute_syllabes.py.

Exécution:
    python3 -m unittest db/scripts/test_compute_syllabes.py
ou:
    pytest db/scripts/test_compute_syllabes.py
"""
from __future__ import annotations

import io
import sys
import unittest
from collections import defaultdict
from contextlib import redirect_stderr
from pathlib import Path

# Permet d'importer compute_syllabes.py depuis le même dossier sans installation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from compute_syllabes import (  # noqa: E402
    ELISION_TOKENS,
    lookup,
    normalize,
    syllables_of,
    tokenize,
)


class NormalizeTests(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(normalize("CHAT"), "chat")
        self.assertEqual(normalize("Aujourd'hui"), "aujourd'hui")

    def test_strips_punctuation(self):
        self.assertEqual(normalize("chat,"), "chat")
        self.assertEqual(normalize("chat!"), "chat")
        self.assertEqual(normalize("chat..."), "chat")
        self.assertEqual(normalize("...chat"), "chat")
        self.assertEqual(normalize(",chat;"), "chat")

    def test_strips_quotes(self):
        self.assertEqual(normalize('"chat"'), "chat")
        self.assertEqual(normalize("«chat»"), "chat")

    def test_keeps_internal_apostrophe(self):
        self.assertEqual(normalize("aujourd'hui"), "aujourd'hui")

    def test_keeps_hyphen(self):
        self.assertEqual(normalize("là-bas"), "là-bas")
        self.assertEqual(normalize("peut-être"), "peut-être")

    def test_only_punctuation_returns_empty(self):
        self.assertEqual(normalize("..."), "")
        self.assertEqual(normalize(",,"), "")
        self.assertEqual(normalize(""), "")
        self.assertEqual(normalize("   "), "")


class TokenizeTests(unittest.TestCase):
    def test_simple_phrase(self):
        self.assertEqual(tokenize("Le chat dort"), ["le", "chat", "dort"])

    def test_with_punctuation(self):
        self.assertEqual(
            tokenize("Le chat, dort doucement."),
            ["le", "chat", "dort", "doucement"],
        )

    def test_with_exclamation_and_question(self):
        self.assertEqual(
            tokenize("Hélas ! Le chat ?"),
            ["hélas", "le", "chat"],
        )

    def test_typographic_apostrophe_normalized(self):
        # ’ (U+2019) doit devenir ' pour rester dans le mot
        self.assertEqual(tokenize("Aujourd’hui"), ["aujourd'hui"])

    def test_apostrophe_convention_with_space(self):
        # Convention du seed: "L'" devient "L "
        self.assertEqual(tokenize("L hiver vient"), ["l", "hiver", "vient"])

    def test_empty_phrase(self):
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize("   "), [])
        self.assertEqual(tokenize("!?,"), [])


class LookupTests(unittest.TestCase):
    def setUp(self):
        # "l" volontairement présent: doit toujours rendre 0 (élision prime).
        self.dico = {
            "chat": 1, "hiver": 2, "vient": 1,
            "là-bas": 2, "vois": 1, "tu": 1, "l": 1,
        }
        self.unknown: dict[str, int] = defaultdict(int)

    def test_known_word(self):
        self.assertEqual(lookup("chat", self.dico, self.unknown), 1)
        self.assertEqual(lookup("hiver", self.dico, self.unknown), 2)

    def test_elision_returns_zero(self):
        for tok in ("l", "d", "j", "n", "s", "t", "c", "m", "qu"):
            self.assertEqual(lookup(tok, self.dico, self.unknown), 0,
                             msg=f"{tok!r} devrait être élidé")

    def test_elision_prime_sur_dictionnaire(self):
        # "l" est présent dans self.dico avec valeur 1, mais reste compté 0.
        self.assertEqual(lookup("l", self.dico, self.unknown), 0)

    def test_empty_token_returns_zero(self):
        self.assertEqual(lookup("", self.dico, self.unknown), 0)

    def test_unknown_word_marked(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            result = lookup("blabla", self.dico, self.unknown)
        self.assertEqual(result, 0)
        self.assertEqual(self.unknown["blabla"], 1)
        self.assertIn("blabla", buf.getvalue())
        self.assertIn("inconnu", buf.getvalue())

    def test_unknown_word_includes_phrase_context(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            lookup("blabla", self.dico, self.unknown,
                   phrase_id="42", phrase="Le blabla dort")
        out = buf.getvalue()
        self.assertIn("42", out)
        self.assertIn("Le blabla dort", out)

    def test_compound_with_hyphen_in_dict(self):
        self.assertEqual(lookup("là-bas", self.dico, self.unknown), 2)

    def test_compound_fallback_split(self):
        # "vois-tu" absent du dictionnaire mais ses parties y sont
        self.assertEqual(lookup("vois-tu", self.dico, self.unknown), 2)
        # rien n'a été marqué comme inconnu
        self.assertEqual(self.unknown.get("vois-tu", 0), 0)

    def test_compound_fully_unknown(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            result = lookup("xxx-yyy", self.dico, self.unknown)
        self.assertEqual(result, 0)
        self.assertEqual(self.unknown["xxx-yyy"], 1)

    def test_compound_with_one_unknown_part_falls_through(self):
        # "vois-yyy": "vois" connu, "yyy" non — on retombe sur le print global
        buf = io.StringIO()
        with redirect_stderr(buf):
            result = lookup("vois-yyy", self.dico, self.unknown)
        self.assertEqual(result, 0)
        self.assertEqual(self.unknown["vois-yyy"], 1)


class SyllablesOfTests(unittest.TestCase):
    def setUp(self):
        self.dico = {
            "le": 1, "la": 1, "les": 1, "des": 1, "un": 1, "une": 1,
            "chat": 1, "chatte": 1, "chats": 1, "chattes": 1,
            "hiver": 2, "vient": 1, "dort": 1, "aime": 1,
            "sache": 1, "que": 1, "je": 1, "tu": 1, "il": 1, "elle": 1,
            "aujourd'hui": 3, "sait": 1,
            "musique": 2, "avant": 2, "toute": 1, "chose": 1, "de": 1,
            "vois": 1, "hélas": 2,
        }
        self.unknown: dict[str, int] = defaultdict(int)

    def test_simple_phrase(self):
        self.assertEqual(syllables_of("Le chat", self.dico, self.unknown), 2)

    def test_phrase_with_elision_l(self):
        # "L hiver vient" → 0 + 2 + 1 = 3
        self.assertEqual(
            syllables_of("L hiver vient", self.dico, self.unknown), 3
        )

    def test_phrase_with_elision_j(self):
        # "Sache que j aime" → 1 + 1 + 0 + 1 = 3
        self.assertEqual(
            syllables_of("Sache que j aime", self.dico, self.unknown), 3
        )

    def test_phrase_with_apostrophe_word(self):
        # "Aujourd'hui elle sait" → 3 + 1 + 1 = 5
        self.assertEqual(
            syllables_of("Aujourd'hui elle sait", self.dico, self.unknown), 5
        )

    def test_phrase_with_punctuation(self):
        # La ponctuation est ignorée: "Hélas, le chat !" → 2+1+1 = 4
        self.assertEqual(
            syllables_of("Hélas, le chat !", self.dico, self.unknown), 4
        )

    def test_verlaine_first_line(self):
        # "De la musique avant toute chose" → 1+1+2+2+1+1 = 8
        # (compte standard: "toute" et "chose" valent 1 — le e muet n'est
        # pas compté, contrairement à la métrique poétique classique)
        self.assertEqual(
            syllables_of(
                "De la musique avant toute chose",
                self.dico, self.unknown,
            ),
            8,
        )

    def test_unknown_word_does_not_break_sum(self):
        # "Le xyzzy dort" → 1 + 0 (inconnu) + 1 = 2
        buf = io.StringIO()
        with redirect_stderr(buf):
            n = syllables_of("Le xyzzy dort", self.dico, self.unknown)
        self.assertEqual(n, 2)
        self.assertEqual(self.unknown["xyzzy"], 1)

    def test_propagates_phrase_context_to_unknown(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            syllables_of("Le xyzzy dort", self.dico, self.unknown,
                         phrase_id="999")
        out = buf.getvalue()
        self.assertIn("999", out)
        self.assertIn("Le xyzzy dort", out)


class ElisionTokensTests(unittest.TestCase):
    def test_classic_elision_letters_present(self):
        for tok in ("l", "d", "j", "n", "s", "t", "c", "m"):
            self.assertIn(tok, ELISION_TOKENS)

    def test_qu_compounds_present(self):
        for tok in ("qu", "jusqu", "lorsqu", "puisqu", "presqu", "quoiqu"):
            self.assertIn(tok, ELISION_TOKENS)

    def test_common_words_not_treated_as_elision(self):
        # Les déterminants/prépositions courts ne doivent PAS être élidés.
        for tok in ("le", "la", "les", "de", "du", "un", "une"):
            self.assertNotIn(tok, ELISION_TOKENS)


if __name__ == "__main__":
    unittest.main()
