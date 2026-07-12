"""
NepCompare — Scraper Package
Auto-discovers and registers all scraper classes.
"""

from scrapers.base_scraper import BaseScraper
from scrapers.daraz import DarazScraper
from scrapers.brothermart import BrotherMartScraper
from scrapers.priceoye import PriceOyeScraper

# Registry of all available scrapers
# Kept only proven working scrapers:
# - Daraz: Direct JSON API (very reliable)
# - Brother Mart: Shopify JSON API (very reliable)
# - PriceOye: HTML-based but stable
# Removed: Gyapu, 91Mobiles, Flipkart, Snapdeal, Amazon, FatafatSewa (require Selenium or blocked by anti-bot)
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "daraz": DarazScraper,
    "brothermart": BrotherMartScraper,
    "priceoye": PriceOyeScraper,
}


def get_scraper(name: str) -> BaseScraper:
    """Get an instantiated scraper by name."""
    name_lower = name.lower()
    scraper_class = SCRAPER_REGISTRY.get(name_lower)
    if scraper_class is None:
        raise ValueError(
            f"Unknown scraper: {name}. Available: {list(SCRAPER_REGISTRY.keys())}"
        )
    return scraper_class()


def get_all_scrapers() -> list[BaseScraper]:
    """Get instances of all registered scrapers."""
    return [cls() for cls in SCRAPER_REGISTRY.values()]


def get_all_scrapers() -> list[BaseScraper]:
    """Get instances of all registered scrapers."""
    return [cls() for cls in SCRAPER_REGISTRY.values()]


def list_scraper_names() -> list[str]:
    """List all registered scraper names."""
    return list(SCRAPER_REGISTRY.keys())


__all__ = [
    "BaseScraper",
    "DarazScraper",
    "GyapuScraper",
    "BrotherMartScraper",
    "FatafatSewaScraper",
    "PriceOyeScraper",
    "SCRAPER_REGISTRY",
    "get_scraper",
    "get_all_scrapers",
    "list_scraper_names",
]
