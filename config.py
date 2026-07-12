"""
NepCompare — Application Configuration
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # ── Flask ──────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nepcompare-dev-secret-key-change-me")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))

    # ── Database ───────────────────────────────────────────────────────
    # SQLite for development; set DATABASE_URL for PostgreSQL in production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///nepcompare.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ── Scraper Settings ───────────────────────────────────────────────
    SCRAPER_HEADLESS: bool = os.getenv("SCRAPER_HEADLESS", "1") == "1"
    SCRAPER_MIN_DELAY: float = float(os.getenv("SCRAPER_MIN_DELAY", "2.0"))
    SCRAPER_MAX_DELAY: float = float(os.getenv("SCRAPER_MAX_DELAY", "5.0"))
    SCRAPER_MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    SCRAPER_PAGE_LOAD_TIMEOUT: int = int(os.getenv("SCRAPER_PAGE_LOAD_TIMEOUT", "30"))
    SCRAPER_MAX_PRODUCTS_PER_SEARCH: int = int(
        os.getenv("SCRAPER_MAX_PRODUCTS_PER_SEARCH", "50")
    )

    # ── Scheduler ──────────────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "0") == "1"
    SCHEDULER_INTERVAL_HOURS: int = int(
        os.getenv("SCHEDULER_INTERVAL_HOURS", "6")
    )

    # ── Admin ──────────────────────────────────────────────────────────
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "nepcompare2024")

    # ── Logging ────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # ── Pagination ─────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ── Search ─────────────────────────────────────────────────────────
    # Default search queries used during scheduled scraping
    DEFAULT_SCRAPE_QUERIES: list[str] = [
        "laptop",
        "mobile phone",
        "headphones",
        "smartwatch",
        "earbuds",
        "tablet",
        "camera",
        "speaker",
        "power bank",
        "smart tv",
    ]
