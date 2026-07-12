"""
NepCompare — Database Seeding Script
Populates the database with high-quality, realistic mock products and price histories
across multiple stores to showcase the platform's price comparison and charting features.
"""

import sys
from datetime import datetime, timedelta, timezone
from database import db
from models import Product, PriceHistory, ScrapingLog
from app import create_app

# ── Mock Data Definitions ─────────────────────────────────────────────

MOCK_PRODUCTS = [
    # ── Category: Laptops ──
    {
        "name": "Apple MacBook Air 13 M3 Chip (8GB RAM, 256GB SSD)",
        "price_options": {
            "Daraz": {"price": 145000.0, "orig": 155000.0, "rating": 4.8, "reviews": 24},
            "PriceOye": {"price": 142000.0, "orig": 149000.0, "rating": 4.9, "reviews": 12},
            "Neo Store": {"price": 144500.0, "orig": 152000.0, "rating": 4.7, "reviews": 8},
            "Brother Mart": {"price": 143000.0, "orig": 150000.0, "rating": 4.6, "reviews": 5},
            "SmartDoko": {"price": 146000.0, "orig": 155000.0, "rating": 4.5, "reviews": 3},
        },
        "category": "Laptops",
        "image_url": "https://img.lazcdn.com/g/p/a12a52efc4ca15f8a02c89fbf0209c1f.jpg",
    },
    {
        "name": "Dell Inspiron 15 3520 Intel Core i5-1235U (8GB, 512GB SSD)",
        "price_options": {
            "Daraz": {"price": 68000.0, "orig": 75000.0, "rating": 4.2, "reviews": 15},
            "PriceOye": {"price": 65500.0, "orig": 72000.0, "rating": 4.5, "reviews": 9},
            "Neo Store": {"price": 66000.0, "orig": 74000.0, "rating": 4.4, "reviews": 14},
            "Brother Mart": {"price": 67000.0, "orig": 73000.0, "rating": 4.0, "reviews": 2},
        },
        "category": "Laptops",
        "image_url": "https://img.lazcdn.com/g/p/b9c8112c3f8e5f2e8ab56877df34a2e2.jpg",
    },
    {
        "name": "HP Victus 15-fa1093dx Gaming Intel i5-13420H RTX 3050",
        "price_options": {
            "Daraz": {"price": 105000.0, "orig": 115000.0, "rating": 4.6, "reviews": 18},
            "PriceOye": {"price": 99999.0, "orig": 108000.0, "rating": 4.8, "reviews": 31},
            "Neo Store": {"price": 102500.0, "orig": 112000.0, "rating": 4.5, "reviews": 6},
            "SmartDoko": {"price": 106000.0, "orig": 118000.0, "rating": 4.2, "reviews": 4},
        },
        "category": "Laptops",
        "image_url": "https://img.lazcdn.com/g/p/de9b7b9f3fe2b4a1df9b1a5127ef67ff.jpg",
    },

    # ── Category: Mobile Phones ──
    {
        "name": "Apple iPhone 15 Pro Max 256GB Natural Titanium",
        "price_options": {
            "Daraz": {"price": 195000.0, "orig": 210000.0, "rating": 4.9, "reviews": 42},
            "PriceOye": {"price": 189000.0, "orig": 199000.0, "rating": 5.0, "reviews": 28},
            "Neo Store": {"price": 192000.0, "orig": 205000.0, "rating": 4.8, "reviews": 15},
            "Brother Mart": {"price": 191500.0, "orig": 200000.0, "rating": 4.7, "reviews": 9},
            "SmartDoko": {"price": 196000.0, "orig": 212000.0, "rating": 4.6, "reviews": 11},
        },
        "category": "Mobile Phones",
        "image_url": "https://img.lazcdn.com/g/p/df32c86f7b1dfca8a0a8f9a2db1237a3.jpg",
    },
    {
        "name": "Samsung Galaxy S24 Ultra 12GB RAM, 512GB Storage",
        "price_options": {
            "Daraz": {"price": 178000.0, "orig": 185000.0, "rating": 4.8, "reviews": 33},
            "PriceOye": {"price": 174000.0, "orig": 180000.0, "rating": 4.9, "reviews": 21},
            "Neo Store": {"price": 176500.0, "orig": 183999.0, "rating": 4.7, "reviews": 11},
            "Brother Mart": {"price": 175000.0, "orig": 182000.0, "rating": 4.6, "reviews": 7},
        },
        "category": "Mobile Phones",
        "image_url": "https://img.lazcdn.com/g/p/ff39e1bc81b34e12abf892837ff29c8e.jpg",
    },
    {
        "name": "Redmi Note 13 Pro 4G (8GB RAM, 256GB Storage)",
        "price_options": {
            "Daraz": {"price": 32999.0, "orig": 34999.0, "rating": 4.4, "reviews": 85},
            "PriceOye": {"price": 31500.0, "orig": 33999.0, "rating": 4.6, "reviews": 40},
            "Brother Mart": {"price": 31999.0, "orig": 34500.0, "rating": 4.5, "reviews": 25},
            "SmartDoko": {"price": 32500.0, "orig": 35000.0, "rating": 4.3, "reviews": 12},
        },
        "category": "Mobile Phones",
        "image_url": "https://img.lazcdn.com/g/p/cd8f8ef1d2fae6ca3a0a38f38ff29c8e.jpg",
    },

    # ── Category: Headphones & Earbuds ──
    {
        "name": "Ultima Atom 192 Bluetooth Wireless Earbuds with ANC",
        "price_options": {
            "Daraz": {"price": 2499.0, "orig": 3999.0, "rating": 4.3, "reviews": 120},
            "PriceOye": {"price": 2299.0, "orig": 3799.0, "rating": 4.5, "reviews": 45},
            "Brother Mart": {"price": 2350.0, "orig": 3800.0, "rating": 4.4, "reviews": 33},
            "SmartDoko": {"price": 2450.0, "orig": 4000.0, "rating": 4.1, "reviews": 15},
        },
        "category": "Headphones & Earbuds",
        "image_url": "https://img.lazcdn.com/g/p/aa99c86f7b1dfca8a0a8f9a2db1237a3.jpg",
    },
    {
        "name": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
        "price_options": {
            "Daraz": {"price": 48500.0, "orig": 52000.0, "rating": 4.8, "reviews": 14},
            "PriceOye": {"price": 46000.0, "orig": 49999.0, "rating": 4.9, "reviews": 22},
            "Neo Store": {"price": 47500.0, "orig": 51000.0, "rating": 4.7, "reviews": 6},
        },
        "category": "Headphones & Earbuds",
        "image_url": "https://img.lazcdn.com/g/p/5a9112c3f8e5f2e8ab56877df34a2e2.jpg",
    },

    # ── Category: Smartwatches ──
    {
        "name": "Redmi Watch 4 GPS Smart Watch (1.97-inch AMOLED)",
        "price_options": {
            "Daraz": {"price": 9999.0, "orig": 11999.0, "rating": 4.5, "reviews": 28},
            "PriceOye": {"price": 9499.0, "orig": 10999.0, "rating": 4.7, "reviews": 19},
            "Brother Mart": {"price": 9599.0, "orig": 11500.0, "rating": 4.6, "reviews": 11},
            "SmartDoko": {"price": 9800.0, "orig": 12000.0, "rating": 4.2, "reviews": 5},
        },
        "category": "Smartwatches",
        "image_url": "https://img.lazcdn.com/g/p/f232c86f7b1dfca8a0a8f9a2db1237a3.jpg",
    },
]


def seed_database():
    """Seed the database with mock products, price history, and scraping logs."""
    print("Initializing Database...")
    app = create_app()

    with app.app_context():
        # Clear existing tables to ensure clean seed
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()

        print("Seeding products & histories...")
        now = datetime.now(timezone.utc)

        # Import normalize helper
        from scrapers.base_scraper import BaseScraper
        normalize = BaseScraper.normalize_name

        product_count = 0
        history_count = 0

        for item in MOCK_PRODUCTS:
            name = item["name"]
            norm_name = normalize(name)

            for store, detail in item["price_options"].items():
                price = detail["price"]
                orig = detail["orig"]
                discount = round(((orig - price) / orig) * 100, 1) if orig else 0.0

                # Formulate distinct URLs to satisfy unique constraint
                url_name_part = norm_name.replace(" ", "-")[:30]
                product_url = f"https://www.{store.lower().replace(' ', '')}.com.np/products/{url_name_part}"

                # Create Product
                product = Product(
                    name=name,
                    normalized_name=norm_name,
                    price=price,
                    original_price=orig,
                    discount=discount,
                    image_url=item["image_url"],
                    product_url=product_url,
                    store=store,
                    category=item["category"],
                    rating=detail["rating"],
                    reviews=detail["reviews"],
                    availability="In Stock",
                    last_updated=now,
                    created_at=now - timedelta(days=30),
                )
                db.session.add(product)
                db.session.flush()  # Obtain ID
                product_count += 1

                # Generate Price History (fluctuating prices over last 30 days)
                days_history = [30, 20, 10, 5, 0]
                price_modifiers = [1.08, 1.05, 1.02, 0.98, 1.00]  # Fluctuations

                for days_ago, modifier in zip(days_history, price_modifiers):
                    historical_price = round(price * modifier, 2)
                    recorded_time = now - timedelta(days=days_ago)

                    history = PriceHistory(
                        product_id=product.id,
                        price=historical_price,
                        recorded_at=recorded_time,
                    )
                    db.session.add(history)
                    history_count += 1

        # Seed realistic Scraping Logs
        print("Seeding scraping logs...")
        stores = ["Daraz", "PriceOye", "Neo Store", "Brother Mart", "SmartDoko"]
        queries = ["laptop", "iphone", "earbuds"]

        for i, store in enumerate(stores):
            for query in queries:
                log = ScrapingLog(
                    store=store,
                    query=query,
                    status="success",
                    products_found=15,
                    products_new=2,
                    products_updated=13,
                    duration_seconds=round(4.5 + i * 1.2, 2),
                    created_at=now - timedelta(hours=i * 6 + 2),
                )
                db.session.add(log)

        db.session.commit()
        print(f"Successfully seeded {product_count} products and {history_count} price history points.")


if __name__ == "__main__":
    seed_database()
