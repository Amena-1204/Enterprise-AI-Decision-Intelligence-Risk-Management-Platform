import time
from flask import Flask, g, jsonify, request
from flask_cors import CORS

from backend.app.config import get_config
from backend.app.utils.logger import app_logger, setup_logger


def create_app(config=None) -> Flask:
    app = Flask(__name__)

    # Load config
    cfg = config or get_config()
    app.config.from_object(cfg)
    app.config["JWT_SECRET_KEY"] = cfg.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = cfg.JWT_ACCESS_TOKEN_EXPIRES

    # Logging
    setup_logger("enterprise_ai", cfg.LOG_LEVEL)

    # CORS
    CORS(app, origins=cfg.CORS_ORIGINS.split(","))

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

    for bp in [auth_bp, customer_bp, prediction_bp, sales_bp, fraud_bp, churn_bp, report_bp, ai_bp]:
        app.register_blueprint(bp)

    # Request logging
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

    @app.errorhandler(500)
    def internal_error(e):
        app_logger.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    # Health check
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "enterprise-ai-platform"}), 200

    app_logger.info("Flask application created (env=%s)", app.config.get("ENV", "development"))
    return app
