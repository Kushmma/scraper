"""
NepCompare — Flask Application
Main application entry point with route handlers.
"""

import logging
import os
import sys

from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from config import Config
from database import init_db

# ── Logging Setup ──────────────────────────────────────────────────────
os.makedirs(Config.LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(Config.LOG_DIR, "app.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    init_db(app)

    # Register API blueprint
    from api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # Initialize scheduler
    if Config.SCHEDULER_ENABLED:
        from scheduler import init_scheduler
        init_scheduler(app)
        logger.info("Scheduler enabled and started")

    # ── Page Routes ────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/search")
    def search():
        query = request.args.get("q", "")
        return render_template("search.html", query=query)

    @app.route("/product/<int:product_id>")
    def product_detail(product_id: int):
        return render_template("product.html", product_id=product_id)

    @app.route("/compare")
    def compare():
        query = request.args.get("q", "")
        return render_template("compare.html", query=query)

    @app.route("/admin")
    def admin():
        return render_template("admin.html")

    @app.route("/admin/login", methods=["POST"])
    def admin_login():
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        return redirect(url_for("admin"))

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin", None)
        return redirect(url_for("index"))

    # ── Error Handlers ─────────────────────────────────────────────

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return render_template("base.html", error="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return render_template("base.html", error="Server error"), 500

    logger.info("NepCompare application initialized")
    return app


# ── Run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )
