FROM postgres:18-alpine

# Les scripts placés dans /docker-entrypoint-initdb.d sont exécutés en ordre
# alphabétique au premier démarrage du conteneur.
COPY init/01_schema.sql /docker-entrypoint-initdb.d/01_schema.sql
COPY init/02_seed.sql   /docker-entrypoint-initdb.d/02_seed.sql

# Les CSV sont copiés à un emplacement référencé dans 02_seed.sql via \copy.
COPY init/seed /seed
