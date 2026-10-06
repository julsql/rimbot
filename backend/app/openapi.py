"""Spécification OpenAPI de l'API, écrite à la main (une poignée de routes)."""
from __future__ import annotations

_ERREURS = {
    "err1": {"type": "string", "description": "Message d'erreur principal (vide si tout va bien)."},
    "err2": {"type": "string", "description": "Détail complémentaire de l'erreur."},
}

_CORPS_POEME = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {"$ref": "#/components/schemas/PoemRequest"},
        },
        "application/x-www-form-urlencoded": {
            "schema": {"$ref": "#/components/schemas/PoemRequest"},
        },
    },
}


def _reponse(description: str, schema: str) -> dict:
    return {
        "description": description,
        "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema}"}}},
    }


SPEC: dict = {
    "openapi": "3.0.3",
    "info": {
        "title": "Rimbot API",
        "version": "1.0.0",
        "description": "Générateur de poèmes français aléatoires.",
    },
    "servers": [{"url": "/api"}],
    "tags": [
        {"name": "poem", "description": "Aperçu et génération de poèmes."},
        {"name": "help", "description": "Aide à la saisie des contraintes."},
        {"name": "health", "description": "État du service."},
    ],
    "paths": {
        "/health": {
            "get": {
                "tags": ["health"],
                "summary": "Vérifie le pool DB.",
                "responses": {
                    "200": _reponse("Service opérationnel.", "Health"),
                    "503": _reponse("Base de données injoignable.", "Health"),
                },
            },
        },
        "/help/syllables": {
            "get": {
                "tags": ["help"],
                "summary": "Liste des syllabes utilisables comme rime.",
                "responses": {
                    "200": {
                        "description": "Syllabes finales connues, avec leur nombre de mots.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Syllable"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "/poem/preview": {
            "post": {
                "tags": ["poem"],
                "summary": "Aperçu de la forme et des contraintes saisies.",
                "requestBody": _CORPS_POEME,
                "responses": {
                    "200": _reponse("Aperçu de la forme.", "PreviewResponse"),
                    "400": _reponse("Forme ou contraintes invalides.", "PreviewResponse"),
                },
            },
        },
        "/poem/generate": {
            "post": {
                "tags": ["poem"],
                "summary": "Génère le poème complet.",
                "requestBody": _CORPS_POEME,
                "responses": {
                    "200": _reponse("Poème généré.", "PoemResponse"),
                    "400": _reponse("Forme ou contraintes invalides.", "PoemResponse"),
                },
            },
        },
    },
    "components": {
        "schemas": {
            "PoemRequest": {
                "type": "object",
                "required": ["forme"],
                "properties": {
                    "forme": {
                        "type": "string",
                        "description": "Schéma de rimes, une lettre par vers, un espace entre les strophes.",
                        "example": "ABBA CDDC EEF GGF",
                    },
                    "sylla": {
                        "type": "string",
                        "description": "Nombre de syllabes par vers.",
                        "example": "1=12",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Rimes imposées par lettre (voir /help/syllables).",
                        "example": "A=t@t,B=se",
                    },
                },
            },
            "PreviewResponse": {
                "type": "object",
                "properties": {
                    "preview": {"type": "string", "nullable": True},
                    **_ERREURS,
                },
            },
            "PoemResponse": {
                "type": "object",
                "properties": {
                    "poem": {"type": "array", "nullable": True, "items": {"type": "string"}},
                    **_ERREURS,
                },
            },
            "Syllable": {
                "type": "object",
                "properties": {
                    "courant": {"type": "string"},
                    "dersyll": {"type": "string"},
                    "API": {"type": "string", "description": "Notation phonétique."},
                    "nboccurence": {"type": "integer"},
                },
            },
            "Health": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok", "degraded"]},
                    "db": {"type": "string", "enum": ["ok", "unavailable"]},
                },
            },
        },
    },
}
