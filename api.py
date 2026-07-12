"""
NepCompare — REST API
All API endpoints for products, search, comparison, history, and admin.
"""

import csv
import io
import logging
import time
from datetime import datetime, timezone
from threading import Thread

from flask import Blueprint, jsonify, request, Response

from database import db
from models import PriceHistory, Product, ScrapingLog
from config import Config

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


# ── Helper ─────────────────────────────────────────────────────────────

def _paginate_query(query, page: int, per_page: int):
    """Apply pagination to a SQLAlchemy query."""
    per_page = min(per_page, Config.MAX_PAGE_SIZE)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [item.to_dict() for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# ── Products ───────────────────────────────────────────────────────────

@api_bp.route("/products", methods=["GET"])
def get_products():
    """List products with filtering, sorting, and pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", Config.DEFAULT_PAGE_SIZE, type=int)

    q = Product.query

    # Filters
    store = request.args.get("store")
    if store:
        q = q.filter(Product.store == store)

    category = request.args.get("category")
    if category:
        q = q.filter(Product.category == category)

    min_price = request.args.get("min_price", type=float)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)

    max_price = request.args.get("max_price", type=float)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)

    min_rating = request.args.get("min_rating", type=float)
    if min_rating is not None:
        q = q.filter(Product.rating >= min_rating)

    min_discount = request.args.get("min_discount", type=float)
    if min_discount is not None:
        q = q.filter(Product.discount >= min_discount)

    availability = request.args.get("availability")
    if availability:
        q = q.filter(Product.availability == availability)

    # Sorting
    sort_by = request.args.get("sort_by", "updated")
    sort_map = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
        "discount": Product.discount.desc(),
        "updated": Product.last_updated.desc(),
        "name": Product.name.asc(),
    }
    q = q.order_by(sort_map.get(sort_by, Product.last_updated.desc()))

    return jsonify(_paginate_query(q, page, per_page))


@api_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """Get single product detail."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict())


@api_bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id: int):
    """Delete a product (admin)."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"})


# ── Search ─────────────────────────────────────────────────────────────

@api_bp.route("/search", methods=["GET"])
def search_products():
    """Search products by name (queries the database)."""
    query_str = request.args.get("q", "").strip()
    if not query_str:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", Config.DEFAULT_PAGE_SIZE, type=int)

    from scrapers.base_scraper import BaseScraper
    normalized = BaseScraper.normalize_name(query_str)
    words = normalized.split()

    q = Product.query
    for word in words:
        q = q.filter(Product.normalized_name.contains(word))

    # Apply same filters as /products
    store = request.args.get("store")
    if store:
        q = q.filter(Product.store == store)
    category = request.args.get("category")
    if category:
        q = q.filter(Product.category == category)
    min_price = request.args.get("min_price", type=float)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    max_price = request.args.get("max_price", type=float)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    min_rating = request.args.get("min_rating", type=float)
    if min_rating is not None:
        q = q.filter(Product.rating >= min_rating)
    min_discount = request.args.get("min_discount", type=float)
    if min_discount is not None:
        q = q.filter(Product.discount >= min_discount)

    sort_by = request.args.get("sort_by", "updated")
    sort_map = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
        "discount": Product.discount.desc(),
        "updated": Product.last_updated.desc(),
    }
    q = q.order_by(sort_map.get(sort_by, Product.last_updated.desc()))

    return jsonify(_paginate_query(q, page, per_page))


@api_bp.route("/suggestions", methods=["GET"])
def search_suggestions():
    """Return search autocomplete suggestions."""
    query_str = request.args.get("q", "").strip()
    if len(query_str) < 2:
        return jsonify([])

    from scrapers.base_scraper import BaseScraper
    normalized = BaseScraper.normalize_name(query_str)

    products = (
        Product.query
        .filter(Product.normalized_name.contains(normalized))
        .with_entities(Product.name)
        .distinct()
        .limit(10)
        .all()
    )
    return jsonify([p.name for p in products])


# ── Compare ────────────────────────────────────────────────────────────

@api_bp.route("/compare", methods=["GET"])
def compare_products():
    """Find similar products across different stores for comparison."""
    query_str = request.args.get("q", "").strip()
    if not query_str:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    from scrapers.base_scraper import BaseScraper
    normalized = BaseScraper.normalize_name(query_str)
    words = normalized.split()

    q = Product.query
    for word in words:
        q = q.filter(Product.normalized_name.contains(word))

    products = q.order_by(Product.price.asc()).all()

    # Group by store
    stores = {}
    for p in products:
        if p.store not in stores:
            stores[p.store] = []
        stores[p.store].append(p.to_dict())

    cheapest = products[0].to_dict() if products else None

    return jsonify({
        "query": query_str,
        "total": len(products),
        "cheapest": cheapest,
        "by_store": stores,
        "all": [p.to_dict() for p in products],
    })


# ── Price History ──────────────────────────────────────────────────────

@api_bp.route("/history/<int:product_id>", methods=["GET"])
def get_price_history(product_id: int):
    """Get price history for a product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    history = (
        PriceHistory.query
        .filter_by(product_id=product_id)
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )

    prices = [h.price for h in history] if history else [product.price]

    return jsonify({
        "product": product.to_dict(),
        "history": [h.to_dict() for h in history],
        "stats": {
            "lowest": min(prices),
            "highest": max(prices),
            "average": round(sum(prices) / len(prices), 2),
            "current": product.price,
            "data_points": len(history),
        },
    })


# ── Categories & Stores ───────────────────────────────────────────────

@api_bp.route("/categories", methods=["GET"])
def get_categories():
    """List all categories with product counts."""
    results = (
        db.session.query(Product.category, db.func.count(Product.id))
        .group_by(Product.category)
        .order_by(db.func.count(Product.id).desc())
        .all()
    )
    return jsonify([{"name": r[0] or "Uncategorized", "count": r[1]} for r in results])


@api_bp.route("/stores", methods=["GET"])
def get_stores():
    """List all stores with product counts."""
    results = (
        db.session.query(Product.store, db.func.count(Product.id))
        .group_by(Product.store)
        .order_by(db.func.count(Product.id).desc())
        .all()
    )
    return jsonify([{"name": r[0], "count": r[1]} for r in results])


@api_bp.route("/stats", methods=["GET"])
def get_stats():
    """Dashboard statistics."""
    total_products = Product.query.count()
    total_stores = db.session.query(Product.store).distinct().count()
    total_categories = db.session.query(Product.category).distinct().count()
    avg_discount = db.session.query(db.func.avg(Product.discount)).scalar() or 0

    last_log = db.session.query(ScrapingLog).order_by(ScrapingLog.created_at.desc()).first()

    return jsonify({
        "total_products": total_products,
        "total_stores": total_stores,
        "total_categories": total_categories,
        "avg_discount": round(avg_discount, 1),
        "last_scrape": last_log.to_dict() if last_log else None,
    })


# ── Scraping (Admin) ──────────────────────────────────────────────────

@api_bp.route("/scrape", methods=["POST"])
def trigger_scrape():
    """Trigger a manual scrape. Runs in background thread."""
    data = request.get_json(silent=True) or {}
    store_name = data.get("store")  # None = all stores
    query = data.get("query", "laptop")

    def run_scrape(app, store_name, query):
        with app.app_context():
            from scrapers import get_scraper, get_all_scrapers
            scrapers = [get_scraper(store_name)] if store_name else get_all_scrapers()

            for scraper in scrapers:
                log = ScrapingLog(
                    store=scraper.store_name,
                    query=query,
                    status="running",
                )
                db.session.add(log)
                db.session.commit()

                start = time.time()
                try:
                    products = scraper.search_products(query)
                    stats = scraper.save_to_database(products, db.session)
                    log.status = "success"
                    log.products_found = stats["total"]
                    log.products_new = stats["new"]
                    log.products_updated = stats["updated"]
                except Exception as e:
                    log.status = "failed"
                    log.error_message = str(e)[:500]
                    logger.error(f"Scrape failed for {scraper.store_name}: {e}")
                finally:
                    log.duration_seconds = round(time.time() - start, 2)
                    db.session.commit()

    from flask import current_app
    app = current_app._get_current_object()
    thread = Thread(target=run_scrape, args=(app, store_name, query))
    thread.daemon = True
    thread.start()

    return jsonify({"message": "Scraping started", "store": store_name or "all", "query": query})


@api_bp.route("/scrape/logs", methods=["GET"])
def get_scraping_logs():
    """Get recent scraping logs."""
    limit = request.args.get("limit", 50, type=int)
    logs = (
        db.session.query(ScrapingLog)
        .order_by(ScrapingLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([log.to_dict() for log in logs])


# ── Export ─────────────────────────────────────────────────────────────

@api_bp.route("/export/csv", methods=["GET"])
def export_csv():
    """Export all products as CSV."""
    products = Product.query.order_by(Product.store, Product.name).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Name", "Price", "Original Price", "Discount %",
        "Store", "Category", "Rating", "Reviews", "Availability",
        "Product URL", "Image URL", "Last Updated",
    ])
    for p in products:
        writer.writerow([
            p.id, p.name, p.price, p.original_price, p.discount,
            p.store, p.category, p.rating, p.reviews, p.availability,
            p.product_url, p.image_url, p.last_updated,
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=nepcompare_products.csv"},
    )
