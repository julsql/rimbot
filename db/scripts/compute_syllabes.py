"""
Calcule le nombre de syllabes pour chaque ligne de phrases.csv en sommant
les syllabes des mots qui composent la phrase, lues depuis mots.csv.

Usage:
    python db/scripts/compute_syllabes.py [--check]

Sans option, le script remplace en place le champ `nbsyllabe` de phrases.csv.
Avec --check, il affiche uniquement les écarts entre la valeur stockée et
la valeur calculée (utile pour vérifier sans rien écrire).

Règles de tokenisation:
- Les guillemets et la ponctuation finale sont retirés.
- Les tirets ne sont PAS coupés (là-bas, peut-être, vois-tu sont d'abord
  cherchés tels quels, et seulement coupés en fallback si l'entrée composée
  est absente du dictionnaire).
- Les apostrophes utiles dans un mot sont conservées (Aujourd'hui).
- Les particules d'élision (l, d, n, s, j, t, c, m, qu, jusqu, lorsqu,
  puisqu, presqu) écrites isolément (convention sans apostrophe du projet)
  sont comptées 0 syllabe car phonétiquement elles s'agrègent au mot suivant.

Les mots inconnus sont signalés sur stderr et comptés 0 syllabe.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "init" / "seed"
MOTS_CSV = ROOT / "mots.csv"
PHRASES_CSV = ROOT / "phrases.csv"

ELISION_TOKENS = {"l", "d", "n", "s", "j", "t", "c", "m",
                  "qu", "jusqu", "lorsqu", "puisqu", "presqu", "quoiqu"}

PUNCT_STRIP = " \t\r\n.,;:!?\"«»()[]…"

# Compléments au dictionnaire mots.csv pour les noms propres (poètes,
# chanteurs, lieux) et autres mots couramment absents. Sans ces entrées
# les phrases littéraires qui mentionnent ces termes seraient sous-comptées.
EXTRA_DICT = {
    # Poètes français
    "hugo": 2, "verlaine": 2, "rimbaud": 2, "mallarmé": 3,
    "baudelaire": 3, "apollinaire": 4,
    # Chanteurs / chansonniers français
    "brassens": 2, "brel": 1, "aznavour": 3, "bécaud": 2,
    "ferré": 2, "trenet": 2, "montand": 2, "greco": 2,
    "barbara": 3, "reggiani": 3, "renaud": 2, "gainsbourg": 2,
    "higelin": 3, "souchon": 2, "cabrel": 2, "goldman": 2,
    "bashung": 2, "jeanne": 1, "piaf": 1,
    # Lieux et monuments
    "italie": 3, "rome": 1, "naples": 1, "vésuve": 2,
    "pompéi": 2, "capri": 2, "tyrrhène": 2, "sorrente": 2,
    "vivaldi": 3, "casanova": 4, "mirabeau": 3, "vecchio": 2,
    "arno": 2, "palio": 2, "pise": 1, "rialto": 3,
    "pieta": 2, "sixtine": 2, "vatican": 3, "montmartre": 2,
    "louvre": 1, "eiffel": 2, "bretagne": 2, "sévigné": 3,
    "compostelle": 3, "trevi": 2, "colisée": 3, "espagne": 2,
    "michel-ange": 3, "saint-sulpice": 3, "botticelli": 4,
    # Marques / divers
    "clairefontaine": 4, "kingfisher": 3,
}


def load_dict(path: Path) -> dict[str, int]:
    """Retourne {ortho_lower: nbsyll}. Si plusieurs entrées coexistent,
    on garde le max (cas rare où une orthographe a plusieurs prononciations).
    Fusionne ensuite avec EXTRA_DICT (noms propres et mots manquants)."""
    table: dict[str, int] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ortho = row["ortho"].strip().lower()
            try:
                n = int(row["nbsyll"])
            except (TypeError, ValueError):
                continue
            if ortho in table:
                table[ortho] = max(table[ortho], n)
            else:
                table[ortho] = n
    for ortho, n in EXTRA_DICT.items():
        table.setdefault(ortho, n)
    return table


def normalize(token: str) -> str:
    return token.strip(PUNCT_STRIP).lower()


def tokenize(phrase: str) -> list[str]:
    raw = phrase.replace("’", "'")  # apostrophe typographique → simple
    return [normalize(tok) for tok in raw.split() if normalize(tok)]


def lookup(token: str, dico: dict[str, int],
           unknown: dict[str, int],
           phrase_id: str = "", phrase: str = "") -> int:
    if not token:
        return 0
    if token in ELISION_TOKENS:
        return 0
    if token in dico:
        return dico[token]
    # Fallback: mot composé absent du dictionnaire — on tente la décomposition.
    if "-" in token:
        parts = [p for p in token.split("-") if p]
        if all(p in dico or p in ELISION_TOKENS for p in parts):
            return sum(dico.get(p, 0) for p in parts)
    # Mot inconnu: on signale l'occurrence avec son contexte pour faciliter
    # une correction manuelle (orthographe, ou ajout dans mots.csv).
    where = f"id {phrase_id}: {phrase!r}" if phrase_id else "(hors contexte)"
    print(f"  mot inconnu {token!r} dans {where}", file=sys.stderr)
    unknown[token] += 1
    return 0


def syllables_of(phrase: str, dico: dict[str, int],
                 unknown: dict[str, int],
                 phrase_id: str = "") -> int:
    return sum(lookup(tok, dico, unknown, phrase_id, phrase)
               for tok in tokenize(phrase))


def main(argv: list[str]) -> int:
    check_only = "--check" in argv

    dico = load_dict(MOTS_CSV)
    print(f"dictionnaire: {len(dico)} formes uniques", file=sys.stderr)

    unknown: dict[str, int] = defaultdict(int)
    rows: list[list[str]] = []
    diffs: list[tuple[str, str, int, int]] = []

    with PHRASES_CSV.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for row in reader:
            if len(row) < 3:
                rows.append(row)
                continue
            phrase_id, phrase, stored = row[0], row[1], row[2]
            computed = syllables_of(phrase, dico, unknown, phrase_id)
            try:
                stored_int = int(stored)
            except ValueError:
                stored_int = -1
            if stored_int != computed:
                diffs.append((phrase_id, phrase, stored_int, computed))
            row[2] = str(computed)
            rows.append(row)

    if unknown:
        total = sum(unknown.values())
        print(f"\nrésumé: {len(unknown)} mots distincts inconnus "
              f"({total} occurrences au total):", file=sys.stderr)
        for word, count in sorted(unknown.items(),
                                  key=lambda x: (-x[1], x[0])):
            print(f"  {word!r}: {count}x", file=sys.stderr)

    if check_only:
        print(f"\n{len(diffs)} écarts entre stocké et calculé:")
        for pid, phrase, stored, computed in diffs:
            print(f"  id {pid}: stocké={stored}, calculé={computed} -- {phrase}")
        return 0

    with PHRASES_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"\n{len(rows)} phrases mises à jour. {len(diffs)} valeurs modifiées.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
