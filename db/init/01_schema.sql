-- Schéma PostgreSQL pour la base Poème
-- Inspiré de la base SQLite originale (PoemeDB.sqlite3)

CREATE TABLE IF NOT EXISTS syllabes (
    id        INTEGER PRIMARY KEY,
    dersyll   TEXT,
    courant   TEXT,
    api       TEXT
);

CREATE TABLE IF NOT EXISTS mots (
    id         INTEGER PRIMARY KEY,
    ortho      TEXT,
    cgram      TEXT,
    genre      TEXT,
    nombre     TEXT,
    freqfilms  REAL,
    verper     TEXT,
    cvcv       TEXT,
    iddersyll  INTEGER REFERENCES syllabes(id),
    nbsyll     INTEGER,
    haspir     INTEGER
);

CREATE TABLE IF NOT EXISTS phrases (
    id         INTEGER PRIMARY KEY,
    phrase     TEXT,
    nbsyllabe  INTEGER
);

CREATE TABLE IF NOT EXISTS ponctuation (
    id     INTEGER PRIMARY KEY,
    ponct  TEXT,
    freq   REAL
);

CREATE INDEX IF NOT EXISTS idx_mots_ortho     ON mots(ortho);
CREATE INDEX IF NOT EXISTS idx_mots_iddersyll ON mots(iddersyll);
CREATE INDEX IF NOT EXISTS idx_mots_nbsyll    ON mots(nbsyll);
CREATE INDEX IF NOT EXISTS idx_mots_cgram     ON mots(cgram);
CREATE INDEX IF NOT EXISTS idx_phrases_nbsyll ON phrases(nbsyllabe);
CREATE INDEX IF NOT EXISTS idx_syll_dersyll   ON syllabes(dersyll);
