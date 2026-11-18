import decimal
import time
from datetime import date, datetime

from flask import Flask, g, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.app.config import get_config
from backend.app.utils.logger import app_logger, setup_logger

# ── Custom JSON provider — handles datetime, date, Decimal ───────────────────

class _SafeJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


# Module-level limiter (initialised inside create_app)
limiter: Limiter = None  # type: ignore


def create_app(config=None) -> Flask:
    global limiter

    app = Flask(__name__)
    app.json_provider_class = _SafeJSONProvider
    app.json = _SafeJSONProvider(app)

    # Load config
    cfg = config or get_config()
    app.config.from_object(cfg)
    app.config["JWT_SECRET_KEY"] = cfg.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = cfg.JWT_ACCESS_TOKEN_EXPIRES
    app.config["MAX_CONTENT_LENGTH"] = cfg.MAX_CONTENT_LENGTH

    # Logging
    setup_logger("enterprise_ai", cfg.LOG_LEVEL)

    # CORS
    CORS(app, origins=cfg.CORS_ORIGINS.split(","))

    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[cfg.RATELIMIT_DEFAULT],
        storage_uri=cfg.RATELIMIT_STORAGE_URL,
        headers_enabled=True,
    )

    # Database pool
    try:
        from backend.app.database.connection import init_pool
        init_pool(cfg)
    except Exception as e:
        app_logger.error("Database pool initialization failed: %s", e)

    # Register blueprints
    from backend.app.routes.auth_routes import auth_bp
    from backend.app.routes.customer_routes import customer_bp
    from backend.app.routes.prediction_routes import prediction_bp
    from backend.app.routes.sales_routes import sales_bp
    from backend.app.routes.fraud_routes import fraud_bp
    from backend.app.routes.churn_routes import churn_bp
    from backend.app.routes.report_routes import report_bp
    from backend.app.routes.ai_routes import ai_bp
    from backend.app.routes.segment_routes import segment_bp

    for bp in [auth_bp, customer_bp, prediction_bp, sales_bp,
               fraud_bp, churn_bp, report_bp, ai_bp, segment_bp]:
        app.register_blueprint(bp)

    # Request lifecycle hooks
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        duration = int((time.time() - g.get("start_time", time.time())) * 1000)
        app_logger.info(
            "%s %s %s %dms",
            request.method, request.path, response.status_code, duration,
        )
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "detail": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(413)
    def request_too_large(e):
        return jsonify({"error": "Request body too large (max 1 MB)"}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Too many requests. Please slow down."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        app_logger.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    # Health check (exempt from rate limiting)
    @app.route("/health")
    @limiter.exempt
    def health():
        return jsonify({"status": "ok", "service": "enterprise-ai-platform"}), 200

    app_logger.info(
        "Flask application created (env=%s)", app.config.get("ENV", "development")
    )
    return app
