"""Génère des poèmes français à partir d'une forme, d'un nombre de syllabes
et de rimes facultatives.

Algorithme (simplifié) :
1. `prev()` valide la forme utilisateur et la traduit en (forme expansée,
   liste des nbsyll par vers, rimes imposées éventuelles).
2. Pour chaque vers, `analyse()` :
   a. tire une phrase aléatoire en base ayant le bon nb de syllabes ;
   b. **pré-sélectionne le mot final** (le seul qui détermine la rime),
      en imposant la dersyll attendue ; si impossible, on retire une
      autre phrase ;
   c. substitue les mots du milieu — les échecs de substitution
      conservent le mot d'origine (la rime, elle, est garantie) ;
   d. assemble le vers et renvoie sa dernière syllabe pour propager
      la contrainte aux vers suivants.

Cette structure garantit que la rime est *toujours* respectée quand elle
est demandée — l'ancien algo (Django) la perdait silencieusement quand
le dernier mot était un article, un pronom, un mot inconnu, etc.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from psycopg import Connection

log = logging.getLogger(__name__)

SYMBOLES = ",;:…./\\&'§@#!()-_$*¥€%£?"

# Nombre de phrases différentes essayées avant d'abandonner un vers.
# Avec ~34 phrases par nb de syllabes, 30 tentatives donnent une probabilité
# de succès très élevée même pour les rimes rares.
MAX_PHRASE_ATTEMPTS = 30


class _PhraseUnusable(Exception):
    """Erreur "douce" : la phrase choisie ne convient pas pour cette rime,
    on doit en prendre une autre."""


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


@dataclass
class WordCatalog:
    """Cache des données peu changeantes côté générateur."""

    mots_possibles: set[str] = field(default_factory=set)
    syll_possibles: dict[str, str] = field(default_factory=dict)
    aide_phon: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, conn: Connection) -> "WordCatalog":
        catalog = cls()
        with conn.cursor() as cur:
            cur.execute("SELECT ortho FROM mots")
            catalog.mots_possibles = {row[0] for row in cur.fetchall() if row[0]}

            cur.execute(
                """
                SELECT s.dersyll, s.courant, s.api, COUNT(*) AS nboccurence
                FROM syllabes s JOIN mots m ON m.iddersyll = s.id
                GROUP BY s.id, s.dersyll, s.courant, s.api
                HAVING COUNT(m.iddersyll) >= 10
                ORDER BY LOWER(s.dersyll) ASC
                """
            )
            for dersyll, courant, api, nb in cur.fetchall():
                catalog.syll_possibles[dersyll] = dersyll
                catalog.syll_possibles[api] = dersyll
                catalog.aide_phon.append({
                    "courant": dersyll,
                    "dersyll": courant,
                    "API": api,
                    "nboccurence": int(nb),
                })
        return catalog


# ---------------------------------------------------------------------------
# Helpers SQL
# ---------------------------------------------------------------------------


def _random_ponctuation(conn: Connection) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ponct FROM ponctuation
            WHERE freq > random()
            ORDER BY random() LIMIT 1
            """
        )
        row = cur.fetchone()
    if row is None:
        return "."
    return row[0]


def _random_phrase(conn: Connection, nbsyll: int) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT phrase FROM phrases WHERE nbsyllabe = %s ORDER BY random() LIMIT 1",
            (nbsyll,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def _word_info(conn: Connection, mot: str) -> tuple | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cgram, genre, nombre, nbsyll, verper, haspir, cvcv
            FROM mots WHERE ortho = %s
            ORDER BY freqfilms DESC NULLS LAST LIMIT 1
            """,
            (mot,),
        )
        return cur.fetchone()


def _pick_word(
    conn: Connection,
    *,
    cgram: str,
    genre: str,
    nombre: str,
    nbsyll: int,
    verper: str,
    haspir: int,
    constraint_dersyll: str | None,
    require_min_occurrences: bool,
    require_long: bool,
    require_cvcv_prefix: str | None,
) -> tuple[str, str] | None:
    sql = [
        "SELECT m.ortho, s.dersyll FROM mots m JOIN syllabes s ON s.id = m.iddersyll",
        "WHERE m.cgram = %s AND m.genre = %s AND m.nombre = %s AND m.nbsyll = %s",
        "  AND m.verper LIKE %s AND m.haspir = %s",
    ]
    params: list = [cgram, genre, nombre, nbsyll, verper, haspir]

    if constraint_dersyll is not None:
        # Comparaison insensible à la casse : la base contient des doublons
        # de syllabes phonétiquement identiques avec des graphies différentes
        # ("ne", "Ne", "NE"…). On veut tous les considérer comme une seule
        # rime.
        sql.append("AND LOWER(s.dersyll) = LOWER(%s)")
        params.append(constraint_dersyll)
    elif require_min_occurrences:
        sql.append(
            "AND m.iddersyll IN ("
            "  SELECT iddersyll FROM mots GROUP BY iddersyll HAVING COUNT(*) >= 10"
            ")"
        )

    if require_long:
        sql.append("AND length(m.ortho) > 3")

    if require_cvcv_prefix is not None:
        sql.append("AND m.cvcv LIKE %s")
        params.append(f"{require_cvcv_prefix}%")

    sql.append("ORDER BY random() LIMIT 1")
    with conn.cursor() as cur:
        cur.execute("\n".join(sql), params)
        row = cur.fetchone()
    return (row[0], row[1]) if row else None


def _normalize_verper(mot: str, verper: str) -> str:
    """Réduit la chaîne verper à une seule personne quand le mot le permet."""
    if not verper:
        return verper
    if mot.endswith("s") and "2s" in verper:
        return "%2s%"
    if not mot.endswith("s") and ("1s" in verper or "3s" in verper):
        return "%1s%" if "1s" in verper else "%3s%"
    return f"%{verper.split('-')[0]}%"


# ---------------------------------------------------------------------------
# Génération vers par vers
# ---------------------------------------------------------------------------


def _last_meaningful_word_index(phraselist: list[str]) -> int:
    """Indice du dernier élément de la phrase qui n'est pas un symbole pur."""
    for i in range(len(phraselist) - 1, -1, -1):
        if phraselist[i].lower() in SYMBOLES:
            continue
        return i
    return -1


def _strip_trailing_symbols(mot: str) -> str:
    while mot and mot[-1] in SYMBOLES:
        mot = mot[:-1]
    return mot


def _capitalize_like(template: str, word: str) -> str:
    if template[:1].isupper() and word:
        return word[:1].upper() + word[1:]
    return word


def _pick_rhyme_word(
    conn: Connection,
    last_raw: str,
    constraint_dersyll: str,
) -> tuple[str, str]:
    """Choisit le mot final qui *garantira* la rime.

    Lève _PhraseUnusable si aucun candidat ne convient — l'appelant doit
    alors essayer une autre phrase.

    Stratégie :
        - le mot d'origine doit être substituable (ni article, ni pronom,
          ni courte préposition, ni inconnu en base) ;
        - on cherche un mot de même cgram/genre/nombre/nbsyll dont la
          dersyll égale la contrainte (si elle existe) ;
        - on relâche progressivement les contraintes esthétiques (cvcv,
          verper) avant d'abandonner.
    """
    mot = _strip_trailing_symbols(last_raw.lower()).replace(",", "")
    if not mot:
        raise _PhraseUnusable("dernier mot vide")

    info = _word_info(conn, mot)
    if info is None:
        raise _PhraseUnusable(f"dernier mot inconnu en base : {mot!r}")

    cgram, genre, nombre, mot_nbsyll, verper, haspir, cvcv = info

    if cgram[:3] in ("ART", "PRO") or cgram == "ADJ:pos":
        raise _PhraseUnusable(f"dernier mot non substituable : cgram={cgram}")
    if cgram[:3] in ("PRE", "CON") and len(mot) < 4:
        raise _PhraseUnusable(f"dernier mot fonctionnel court : {mot!r}")

    require_long = cgram[:3] in ("PRE", "CON")
    require_cvcv_prefix: str | None = None
    if cgram[:3] in ("NOM", "ADJ", "VER") and cvcv:
        verper = _normalize_verper(mot, verper)
        require_cvcv_prefix = cvcv[0]

    require_min_occ = not bool(constraint_dersyll)
    constraint = constraint_dersyll or None

    # On relâche cvcv puis verper si la rime stricte ne donne rien — la rime
    # elle-même reste imposée (constraint_dersyll), donc le résultat reste
    # toujours correct phonétiquement.
    relaxations = [
        (require_cvcv_prefix, verper),
        (None,                verper),
        (None,                "%"),
    ]
    last_err = "no match"
    for cvcv_pref, vp in relaxations:
        choice = _pick_word(
            conn,
            cgram=cgram,
            genre=genre,
            nombre=nombre,
            nbsyll=mot_nbsyll,
            verper=vp,
            haspir=haspir,
            constraint_dersyll=constraint,
            require_min_occurrences=require_min_occ,
            require_long=require_long,
            require_cvcv_prefix=cvcv_pref,
        )
        if choice is not None:
            return choice
        last_err = "no rhyme candidate"

    raise _PhraseUnusable(
        f"aucun mot rimant en {constraint_dersyll!r} pour "
        f"{cgram} {genre} {nombre} {mot_nbsyll}syll ({last_err})"
    )


def _substitute_middle_word(
    conn: Connection, catalog: WordCatalog, raw: str
) -> str:
    """Renvoie un mot remplaçant le mot du milieu de la phrase.

    Pour les mots du milieu, l'échec n'est pas critique : on garde alors le
    mot d'origine plutôt que de tout abandonner. Cela préserve le vers et,
    surtout, la rime."""
    mot = raw.lower()
    if mot in SYMBOLES:
        return mot + " "

    punct_inside = " "
    if mot[-1] in SYMBOLES and mot[:-1] in catalog.mots_possibles:
        punct_inside = mot[-1] + " "
        mot = mot[:-1]

    info = _word_info(conn, mot.replace(",", ""))
    if info is None:
        return raw + punct_inside

    cgram, genre, nombre, mot_nbsyll, verper, haspir, cvcv = info

    if len(mot) == 1 and cvcv and cvcv[0] == "C":
        return raw + "'"
    if cgram[:3] in ("ART", "PRO") or cgram == "ADJ:pos":
        return raw + " "
    if cgram[:3] in ("PRE", "CON") and len(mot) < 4:
        return raw + " "

    require_long = cgram[:3] in ("PRE", "CON")
    require_cvcv_prefix: str | None = None
    if cgram[:3] in ("NOM", "ADJ", "VER") and cvcv:
        verper = _normalize_verper(mot, verper)
        require_cvcv_prefix = cvcv[0]

    choice = _pick_word(
        conn,
        cgram=cgram,
        genre=genre,
        nombre=nombre,
        nbsyll=mot_nbsyll,
        verper=verper,
        haspir=haspir,
        constraint_dersyll=None,
        require_min_occurrences=False,
        require_long=require_long,
        require_cvcv_prefix=require_cvcv_prefix,
    )

    if choice is None:
        # On préserve la mécanique du vers : conserver le mot d'origine
        # plutôt que de propager l'échec.
        return raw + punct_inside

    new_word, _ = choice
    return _capitalize_like(raw, new_word) + punct_inside


def _build_verse(
    conn: Connection,
    catalog: WordCatalog,
    phrase: str,
    constraint_dersyll: str,
) -> tuple[str, str]:
    """Construit un vers à partir d'une phrase candidate.

    Lève _PhraseUnusable si la phrase ne permet pas la rime demandée.
    Renvoie (texte_du_vers, dersyll_du_dernier_mot_substitué)."""
    phraselist = phrase.split(" ")
    last_idx = _last_meaningful_word_index(phraselist)
    if last_idx < 0:
        raise _PhraseUnusable("phrase vide")

    # On commence par valider et choisir le mot rimé. Si ça échoue, inutile
    # d'aller plus loin avec cette phrase.
    last_word, last_dersyll = _pick_rhyme_word(
        conn, phraselist[last_idx], constraint_dersyll
    )

    parts: list[str] = []
    for i, raw in enumerate(phraselist):
        if i < last_idx:
            parts.append(_substitute_middle_word(conn, catalog, raw))
        elif i == last_idx:
            parts.append(_capitalize_like(raw, last_word))
        else:
            # Tokens après le dernier mot pertinent (ex. ponctuation isolée).
            mot = raw.lower()
            if mot in SYMBOLES:
                parts.append(mot + " ")

    verse = "".join(parts).strip(" ") + _random_ponctuation(conn) + "\n"
    return verse, last_dersyll


def analyse(
    conn: Connection,
    catalog: WordCatalog,
    nbsyll: int,
    dersyll: str = "",
    *,
    max_phrase_attempts: int = MAX_PHRASE_ATTEMPTS,
) -> tuple[str, str]:
    """Renvoie (vers, dersyll_du_vers).

    Si une rime est imposée (`dersyll != ''`), elle est *garantie* dans le
    résultat. On essaye jusqu'à `max_phrase_attempts` phrases différentes
    avant de renoncer.
    """
    if nbsyll < 2:
        return _analyse_one_syllable(conn, dersyll)

    nbsyll = min(nbsyll, 12)
    last_error: str | None = None

    for _ in range(max_phrase_attempts):
        phrase = _random_phrase(conn, nbsyll)
        if phrase is None:
            raise RuntimeError(f"Aucune phrase de {nbsyll} syllabes en base")
        try:
            return _build_verse(conn, catalog, phrase, dersyll)
        except _PhraseUnusable as exc:
            last_error = str(exc)
            continue

    raise RuntimeError(
        f"Impossible de produire un vers de {nbsyll} syllabes "
        f"avec rime {dersyll!r} après {max_phrase_attempts} tentatives"
        f" (dernière erreur : {last_error})"
    )


def _analyse_one_syllable(conn: Connection, dersyll: str) -> tuple[str, str]:
    sql_base = (
        "SELECT m.ortho, s.dersyll FROM mots m JOIN syllabes s ON s.id = m.iddersyll "
        "WHERE m.nbsyll = 1 AND length(m.ortho) > 3"
    )
    if dersyll == "":
        sql = (
            sql_base
            + " AND m.iddersyll IN (SELECT iddersyll FROM mots GROUP BY iddersyll HAVING COUNT(*) >= 10)"
            + " ORDER BY random() LIMIT 1"
        )
        params: tuple = ()
    else:
        sql = sql_base + " AND LOWER(s.dersyll) = LOWER(%s) ORDER BY random() LIMIT 1"
        params = (dersyll,)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    if row is None:
        raise RuntimeError("Pas de mot mono-syllabique disponible")
    nouveau, dersyll = row
    nouveau = nouveau[:1].upper() + nouveau[1:] + _random_ponctuation(conn) + "\n"
    return nouveau, dersyll


# ---------------------------------------------------------------------------
# Génération du poème entier
# ---------------------------------------------------------------------------


def poeme_texte(
    conn: Connection,
    catalog: WordCatalog,
    rimes: str,
    nbsyll: list[int],
) -> str:
    """Construit le texte complet du poème à partir d'une forme expansée."""
    dictsyll: dict[str, str] = {}
    poeme = ""
    paragraphs = rimes.split(" ")
    i = 0
    for paragraphe in paragraphs:
        for verssyll in paragraphe.split("_")[:-1]:
            if "." in verssyll:
                # Rime explicitement imposée par l'utilisateur.
                phrase, _ = analyse(conn, catalog, nbsyll[i], verssyll.strip("."))
            elif verssyll in dictsyll:
                # Rime déjà choisie pour cette lettre par un vers précédent.
                phrase, _ = analyse(conn, catalog, nbsyll[i], dictsyll[verssyll])
            else:
                # Première occurrence de cette lettre : libre choix, on
                # mémorise la dersyll pour les vers suivants.
                phrase, last = analyse(conn, catalog, nbsyll[i])
                dictsyll[verssyll] = last
            poeme += phrase
            i += 1
        poeme += "\n"
    return poeme.strip("\n")[:-1].strip(" ") + "."


def prev(
    catalog: WordCatalog,
    forme: str,
    sylltaille: str,
    rime: str,
) -> tuple[str | None, str, str]:
    """Construit l'aperçu (forme + nb syllabes par vers + rime imposée)."""
    err1 = ""
    err2 = ""

    if not forme:
        return None, "Vous n'avez donné aucune forme", ""

    syllname: dict[str, str] = {}
    forme_compact = forme.replace(" ", "")

    if sylltaille:
        nbsyll: list[str] = [""] * len(forme_compact)
        for unit in sylltaille.split(","):
            parts = unit.replace(" ", "").split("=")
            try:
                idx = int(parts[0])
                count = int(parts[1])
            except (ValueError, IndexError):
                return (
                    None,
                    f"{unit} est mal écrit",
                    "Veuillez respecter la mise en forme :\n 1 = 12, 2 = 6 ...",
                )
            try:
                if count > 12:
                    err1 = "Attention, nombre de syllabes max dépassés\n(max = 12)"
                    nbsyll[idx - 1] = "_ " * 11
                elif count < 1:
                    err1 = "Attention, nombre de syllabes min = 1"
                    nbsyll[idx - 1] = " "
                elif count == 1:
                    nbsyll[idx - 1] = " "
                else:
                    nbsyll[idx - 1] = "_ " * (count - 1)
            except IndexError:
                return None, "Vous avez dépassé le nombre de vers donnés dans la forme", ""

        if nbsyll[0] == "":
            nbsyll[0] = "_ " * 11
        elif nbsyll[0] == " ":
            nbsyll[0] = ""
        for a in range(1, len(nbsyll)):
            if nbsyll[a] == "":
                nbsyll[a] = "_ " * nbsyll[a - 1].count("_")
    else:
        nbsyll = ["_ " * 11] * len(forme_compact)

    texte = ""
    if rime:
        for unit in rime.split(","):
            a = unit.replace(" ", "").split("=")
            if len(a) != 2 or a[0] not in forme:
                err1 = "Les rimes sont mal écrites"
                err2 = (
                    "Veuillez respecter la mise en forme : A=t@t, B=se … "
                    "(avec les bons symboles correspondants à ceux donnés dans forme)"
                )
                continue
            if a[1] in catalog.syll_possibles:
                syllname[a[0]] = catalog.syll_possibles[a[1]]
            else:
                err1 = "Les rimes sont mal écrites"
                err2 = f"{a[1]} n'existe pas"

        j = 0
        for ch in forme:
            if ch == " ":
                texte += "\n"
            else:
                texte += str(nbsyll[j]) + (syllname[ch] + "." if ch in syllname else ch) + "\n"
                j += 1
    else:
        j = 0
        for ch in forme:
            if ch == " ":
                texte += "\n"
            else:
                texte += str(nbsyll[j]) + ch + "\n"
                j += 1

    return texte, err1, err2


def expand_form(texte: str) -> tuple[str, list[int]]:
    """Reconstruit (forme expansée, nbsyll[]) depuis le texte de prev()."""
    forme = ""
    nbsyll: list[int] = []
    for line in texte.split("\n"):
        if line == "":
            forme += " "
        else:
            nbsyll.append(line.count("_") + 1)
            forme += line.split(" ")[-1] + "_"
    return forme, nbsyll


def generate(
    conn: Connection,
    catalog: WordCatalog,
    forme_in: str = "ABBA",
    sylla_in: str = "1=12",
    phone_in: str = "",
) -> tuple[list[str] | None, str, str]:
    """Pipeline complet : forme utilisateur -> poème final (lignes)."""
    phone_in = phone_in.replace(" ", "").strip(",")
    sylla_in = sylla_in.replace(" ", "").strip(",")
    texte, err1, err2 = prev(catalog, forme_in, sylla_in, phone_in)
    if texte is None:
        return None, err1, err2

    forme, nbsyll = expand_form(texte)
    try:
        return poeme_texte(conn, catalog, forme, nbsyll).split("\n"), err1, err2
    except Exception:
        log.exception(
            "Échec de génération pour forme=%r sylla=%r phone=%r",
            forme_in, sylla_in, phone_in,
        )
        return None, "Erreur, Veuillez recommencer.", err2
