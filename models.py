"""
NepCompare — Database Models
SQLAlchemy ORM models for products, price history, and scraping logs.
"""

from datetime import datetime, timezone
from database import db


class Product(db.Model):
    """Represents a product scraped from an e-commerce website."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(500), nullable=False)
    normalized_name = db.Column(db.String(500), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)
    discount = db.Column(db.Float, nullable=True, default=0.0)
    image_url = db.Column(db.String(1000), nullable=True)
    product_url = db.Column(db.String(1000), nullable=False, unique=True)
    store = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(200), nullable=True, index=True)
    rating = db.Column(db.Float, nullable=True, default=0.0)
    reviews = db.Column(db.Integer, nullable=True, default=0)
    availability = db.Column(db.String(50), nullable=True, default="In Stock")
    last_updated = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship to price history
    price_history = db.relationship(
        "PriceHistory",
        backref="product",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Composite index for efficient search/filter
    __table_args__ = (
        db.Index("idx_product_store_category", "store", "category"),
        db.Index("idx_product_price", "price"),
        db.Index("idx_product_discount", "discount"),
        db.Index("idx_product_rating", "rating"),
        db.Index("idx_product_updated", "last_updated"),
    )

    def to_dict(self) -> dict:
        """Serialize product to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "original_price": self.original_price,
            "discount": self.discount,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "store": self.store,
            "category": self.category,
            "rating": self.rating,
            "reviews": self.reviews,
            "availability": self.availability,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"<Product {self.id}: {self.name[:40]} @ Rs.{self.price} [{self.store}]>"


class PriceHistory(db.Model):
    """Tracks price changes for a product over time."""

    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.Index("idx_history_product_date", "product_id", "recorded_at"),
    )

    def to_dict(self) -> dict:
        """Serialize price history entry to dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "price": self.price,
            "recorded_at": (
                self.recorded_at.isoformat() if self.recorded_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"<PriceHistory product={self.product_id} price={self.price}>"


class ScrapingLog(db.Model):
    """Logs each scraping run for monitoring and debugging."""

    __tablename__ = "scraping_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    store = db.Column(db.String(100), nullable=False)
    query = db.Column(db.String(300), nullable=True)
    status = db.Column(
        db.String(20), nullable=False, default="pending"
    )  # pending, running, success, failed, partial
    products_found = db.Column(db.Integer, nullable=True, default=0)
    products_new = db.Column(db.Integer, nullable=True, default=0)
    products_updated = db.Column(db.Integer, nullable=True, default=0)
    duration_seconds = db.Column(db.Float, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Serialize scraping log to dictionary."""
        return {
            "id": self.id,
            "store": self.store,
            "query": self.query,
            "status": self.status,
            "products_found": self.products_found,
            "products_new": self.products_new,
            "products_updated": self.products_updated,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"<ScrapingLog {self.store} [{self.status}] +{self.products_found}>"
