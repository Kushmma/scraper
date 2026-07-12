"""
NepCompare — Base Scraper
Abstract base class that all site-specific scrapers inherit from.
Provides Selenium driver management, retry logic, delay, normalization, and DB persistence.
"""

import logging
import random
import re
import time
import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import Config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all e-commerce scrapers.

    Subclasses must define:
        - store_name (str)
        - base_url (str)
        - search_url_template (str) — with {query} placeholder
        - _extract_products_from_page(page_source, query) -> list[dict]

    Optionally override:
        - _get_search_url(query) for custom URL building
        - _needs_selenium() to indicate JS rendering is required
    """

    store_name: str = ""
    base_url: str = ""
    search_url_template: str = ""

    def __init__(self):
        self.config = Config()
        self.driver: Optional[webdriver.Chrome] = None
        self.logger = logging.getLogger(f"scraper.{self.store_name}")

    # ── Selenium Driver ────────────────────────────────────────────────

    def _get_driver(self) -> webdriver.Chrome:
        """Create and return a headless Chrome WebDriver."""
        if self.driver is not None:
            return self.driver

        options = Options()
        if self.config.SCRAPER_HEADLESS:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.page_load_strategy = "eager"

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.config.SCRAPER_PAGE_LOAD_TIMEOUT)
            self.logger.info("Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

        return self.driver

    def _close_driver(self):
        """Close the Selenium driver gracefully."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

    # ── Delay & Retry ──────────────────────────────────────────────────

    def _random_delay(self, min_s: float = None, max_s: float = None):
        """Sleep for a random duration to mimic human behavior."""
        lo = min_s or self.config.SCRAPER_MIN_DELAY
        hi = max_s or self.config.SCRAPER_MAX_DELAY
        delay = random.uniform(lo, hi)
        time.sleep(delay)

    def _retry(self, func, *args, max_retries: int = None, **kwargs):
        """
        Retry a callable with exponential backoff.
        Returns the function result or None on total failure.
        """
        retries = max_retries or self.config.SCRAPER_MAX_RETRIES
        for attempt in range(1, retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                wait = 2**attempt + random.random()
                self.logger.warning(
                    f"Attempt {attempt}/{retries} failed: {e}. "
                    f"Retrying in {wait:.1f}s..."
                )
                if attempt < retries:
                    time.sleep(wait)
                else:
                    self.logger.error(
                        f"All {retries} attempts failed for {func.__name__}"
                    )
                    return None

    # ── Element Helpers ────────────────────────────────────────────────

    def _safe_find_text(
        self,
        element,
        css: str,
        xpath: str = None,
        default: str = "",
    ) -> str:
        """
        Find element text using CSS selector with XPath fallback.
        Returns default if not found.
        """
        try:
            el = element.select_one(css)
            if el:
                return el.get_text(strip=True)
        except Exception:
            pass

        if xpath:
            try:
                from lxml import etree

                tree = etree.HTML(str(element))
                result = tree.xpath(xpath)
                if result:
                    text = result[0] if isinstance(result[0], str) else result[0].text
                    return (text or "").strip()
            except Exception:
                pass

        return default

    def _safe_find_attr(
        self,
        element,
        css: str,
        attr: str,
        xpath: str = None,
        default: str = "",
    ) -> str:
        """
        Find element attribute using CSS selector with XPath fallback.
        """
        try:
            el = element.select_one(css)
            if el and el.get(attr):
                return el.get(attr, default)
        except Exception:
            pass

        if xpath:
            try:
                from lxml import etree

                tree = etree.HTML(str(element))
                result = tree.xpath(xpath)
                if result:
                    return str(result[0]).strip()
            except Exception:
                pass

        return default

    # ── Price Parsing ──────────────────────────────────────────────────

    @staticmethod
    def parse_price(price_str: str) -> Optional[float]:
        """
        Parse a price string to float.
        Handles formats like 'Rs. 1,299', 'NPR 1299', 'रु 1,299.00'
        """
        if not price_str:
            return None
        # Remove currency symbols, letters, and whitespace
        cleaned = re.sub(r"[^\d.,]", "", price_str)
        # Remove thousands separators (commas)
        cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_discount(
        price: Optional[float], original_price: Optional[float]
    ) -> float:
        """Calculate discount percentage."""
        if price and original_price and original_price > price:
            return round(((original_price - price) / original_price) * 100, 1)
        return 0.0

    @staticmethod
    def is_valid_price(price: Optional[float]) -> bool:
        """
        Validate that a price is realistic for electronics in Nepal.
        Range: 100 NPR to 10,000,000 NPR (to filter out fake/scraped data)
        """
        if price is None or price <= 0:
            return False
        # Min: 100 NPR (basic items), Max: 10M NPR (expensive electronics)
        return 100 <= price <= 10_000_000

    # ── Name Normalization ─────────────────────────────────────────────

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize a product name for deduplication.
        Lowercase, strip extra whitespace, remove special chars.
        """
        if not name:
            return ""
        # Normalize unicode
        name = unicodedata.normalize("NFKD", name)
        # Lowercase
        name = name.lower().strip()
        # Replace multiple whitespace with single space
        name = re.sub(r"\s+", " ", name)
        # Remove special characters except alphanumeric and spaces
        name = re.sub(r"[^\w\s]", "", name)
        return name.strip()

    # ── URL Helpers ────────────────────────────────────────────────────

    def _get_search_url(self, query: str) -> str:
        """Build search URL from template. Override for custom logic."""
        from urllib.parse import quote_plus

        return self.search_url_template.format(query=quote_plus(query))

    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute."""
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.base_url.rstrip("/") + url
        return self.base_url.rstrip("/") + "/" + url

    # ── Core Scraping ──────────────────────────────────────────────────

    def _needs_selenium(self) -> bool:
        """Override to return True if the site needs JS rendering."""
        return False

    def search_products(self, query: str) -> list[dict]:
        """
        Search for products on this store.
        Returns a list of product dicts with validated prices.
        """
        self.logger.info(f"Searching '{query}' on {self.store_name}...")
        url = self._get_search_url(query)

        try:
            if self._needs_selenium():
                page_source = self._fetch_with_selenium(url)
            else:
                page_source = self._fetch_with_requests(url)

            if not page_source:
                self.logger.warning(f"Empty page source from {url}")
                return []

            products = self._extract_products_from_page(page_source, query)
            
            # Filter out products with invalid prices
            valid_products = []
            invalid_count = 0
            for product in products:
                if self.is_valid_price(product.get("price")):
                    valid_products.append(product)
                else:
                    invalid_count += 1
            
            if invalid_count > 0:
                self.logger.warning(
                    f"Filtered out {invalid_count} products with invalid prices on {self.store_name}"
                )
            
            self.logger.info(
                f"Found {len(valid_products)} valid products for '{query}' on {self.store_name}"
            )
            return valid_products[: self.config.SCRAPER_MAX_PRODUCTS_PER_SEARCH]

        except Exception as e:
            self.logger.error(f"Error searching '{query}' on {self.store_name}: {e}")
            return []
        finally:
            if self._needs_selenium():
                self._close_driver()

    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """Fetch page using requests (faster, for server-rendered pages)."""
        import requests

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            self._random_delay(0.5, 1.5)
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            self.logger.warning(f"requests fetch failed for {url}: {e}")
            # Fall back to Selenium
            self.logger.info("Falling back to Selenium...")
            return self._fetch_with_selenium(url)

    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Fetch page using Selenium (for JS-rendered pages)."""
        driver = self._get_driver()
        try:
            self._random_delay()
            driver.get(url)
            # Wait for body to be present
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self._random_delay(1, 3)
            # Scroll down to trigger lazy loading
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight / 2);"
            )
            time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            return driver.page_source
        except TimeoutException:
            self.logger.error(f"Timeout loading {url}")
            return None
        except WebDriverException as e:
            self.logger.error(f"WebDriver error for {url}: {e}")
            return None

    # ── Abstract Methods ───────────────────────────────────────────────

    @abstractmethod
    def _extract_products_from_page(
        self, page_source: str, query: str
    ) -> list[dict]:
        """
        Parse the page HTML and extract product data.
        Must return a list of dicts with keys:
            name, price, original_price, discount, image_url,
            product_url, store, category, rating, reviews, availability
        """
        ...

    # ── Database Persistence ───────────────────────────────────────────

    def save_to_database(self, products: list[dict], db_session) -> dict:
        """
        Save scraped products to the database.
        Updates existing products (matched by product_url) and inserts new ones.
        Also records price history.

        Returns: {"new": int, "updated": int, "total": int}
        """
        from models import PriceHistory, Product

        stats = {"new": 0, "updated": 0, "total": len(products)}

        for item in products:
            if not item.get("name") or not item.get("product_url"):
                continue

            try:
                existing = (
                    db_session.query(Product)
                    .filter_by(product_url=item["product_url"])
                    .first()
                )

                if existing:
                    # Update existing product
                    price_changed = existing.price != item.get("price")
                    existing.name = item.get("name", existing.name)
                    existing.price = item.get("price", existing.price)
                    existing.original_price = item.get(
                        "original_price", existing.original_price
                    )
                    existing.discount = item.get("discount", existing.discount)
                    existing.image_url = item.get("image_url", existing.image_url)
                    existing.rating = item.get("rating", existing.rating)
                    existing.reviews = item.get("reviews", existing.reviews)
                    existing.availability = item.get(
                        "availability", existing.availability
                    )
                    existing.category = item.get("category", existing.category)
                    existing.last_updated = datetime.now(timezone.utc)

                    # Record price history only when price changes
                    if price_changed and item.get("price"):
                        history = PriceHistory(
                            product_id=existing.id,
                            price=item["price"],
                            recorded_at=datetime.now(timezone.utc),
                        )
                        db_session.add(history)

                    stats["updated"] += 1
                else:
                    # Insert new product
                    product = Product(
                        name=item.get("name", ""),
                        normalized_name=self.normalize_name(item.get("name", "")),
                        price=item.get("price", 0),
                        original_price=item.get("original_price"),
                        discount=item.get("discount", 0),
                        image_url=item.get("image_url"),
                        product_url=item["product_url"],
                        store=item.get("store", self.store_name),
                        category=item.get("category"),
                        rating=item.get("rating", 0),
                        reviews=item.get("reviews", 0),
                        availability=item.get("availability", "In Stock"),
                        last_updated=datetime.now(timezone.utc),
                        created_at=datetime.now(timezone.utc),
                    )
                    db_session.add(product)
                    db_session.flush()  # Get the ID

                    # Initial price history entry
                    if item.get("price"):
                        history = PriceHistory(
                            product_id=product.id,
                            price=item["price"],
                            recorded_at=datetime.now(timezone.utc),
                        )
                        db_session.add(history)

                    stats["new"] += 1

            except Exception as e:
                self.logger.error(f"Error saving product: {e}")
                continue

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Database commit error: {e}")

        self.logger.info(
            f"Saved {stats['new']} new, {stats['updated']} updated "
            f"out of {stats['total']} products"
        )
        return stats
