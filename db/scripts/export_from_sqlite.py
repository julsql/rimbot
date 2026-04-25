"""
Exporte les tables de PoemeDB.sqlite3 vers des CSV chargés au démarrage par
PostgreSQL (via 02_seed.sql et la commande `\copy`).

Usage:
    python db/scripts/export_from_sqlite.py <chemin/vers/PoemeDB.sqlite3> <repertoire/de/sortie>
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

TABLES = {
    "syllabes":    ["id", "dersyll", "courant", "api"],
    "mots":        ["id", "ortho", "cgram", "genre", "nombre",
                    "freqfilms", "verper", "cvcv", "iddersyll", "nbsyll", "haspir"],
    "phrases":     ["id", "phrase", "nbsyllabe"],
    "ponctuation": ["id", "ponct", "freq"],
}

SQLITE_TO_POSTGRES_NAMES = {
    "syllabes":    ("SYLLABES",    ["id", "dersyll", "courant", "API"]),
    "mots":        ("MOTS",        ["id", "ortho", "cgram", "genre", "nombre",
                                    "freqfilms", "verper", "cvcv", "iddersyll", "nbsyll", "haspir"]),
    "phrases":     ("PHRASES",     ["id", "phrase", "nbsyllabe"]),
    "ponctuation": ("PONCTUATION", ["id", "ponct", "freq"]),
}


def export(sqlite_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
        for pg_table, _ in TABLES.items():
            sqlite_table, sqlite_cols = SQLITE_TO_POSTGRES_NAMES[pg_table]
            cur = conn.execute(
                f'SELECT {", ".join(sqlite_cols)} FROM {sqlite_table}'
            )
            target = out_dir / f"{pg_table}.csv"
            with target.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(TABLES[pg_table])
                for row in cur:
                    writer.writerow([row[c] for c in sqlite_cols])
            print(f"exported {pg_table} -> {target}")
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    export(Path(sys.argv[1]), Path(sys.argv[2]))
