from __future__ import annotations

import logging

from flask import Flask
from flask_cors import CORS

from .config import Config
from .db import init_pool, close_pool
from .routes.health import bp as health_bp
from .routes.help import bp as help_bp
from .routes.poem import bp as poem_bp


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config or Config())

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    init_pool(app.config["DATABASE_URL"])
    app.teardown_appcontext(lambda exc: None)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(poem_bp,   url_prefix="/api/poem")
    app.register_blueprint(help_bp,   url_prefix="/api/help")

    @app.teardown_appcontext
    def _close(_):  # pragma: no cover - shutdown hook
        pass

    import atexit
    atexit.register(close_pool)

    return app
