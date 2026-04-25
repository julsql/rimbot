-- Charge les CSV de seed dans les tables Poème.
-- Exécuté automatiquement par l'image officielle postgres lors du premier
-- démarrage (cf. /docker-entrypoint-initdb.d).
-- Les CSV sont copiés dans le conteneur sous /seed (cf. db/Dockerfile).
--
-- Important : la base SQLite originale stockait des chaînes VIDES dans
-- de nombreuses colonnes texte (genre, nombre, verper, dersyll, courant…).
-- Par défaut, `\copy ... FORMAT csv` interprète une cellule vide non-quotée
-- comme NULL. L'algorithme de génération compare ces colonnes via `=` :
-- en NULL elles ne matcheraient plus rien. On force donc empty-string via
-- FORCE_NOT_NULL.

\copy syllabes    (id, dersyll, courant, api)                                                                          FROM '/seed/syllabes.csv'    WITH (FORMAT csv, HEADER true, FORCE_NOT_NULL (dersyll, courant, api));
\copy mots        (id, ortho, cgram, genre, nombre, freqfilms, verper, cvcv, iddersyll, nbsyll, haspir)                FROM '/seed/mots.csv'        WITH (FORMAT csv, HEADER true, FORCE_NOT_NULL (ortho, cgram, genre, nombre, verper, cvcv));
\copy phrases     (id, phrase, nbsyllabe)                                                                              FROM '/seed/phrases.csv'     WITH (FORMAT csv, HEADER true, FORCE_NOT_NULL (phrase));
\copy ponctuation (id, ponct, freq)                                                                                    FROM '/seed/ponctuation.csv' WITH (FORMAT csv, HEADER true, FORCE_NOT_NULL (ponct));

ANALYZE syllabes;
ANALYZE mots;
ANALYZE phrases;
ANALYZE ponctuation;
