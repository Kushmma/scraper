"""
NepCompare — 91Mobiles Scraper
Scrapes product listings from 91mobiles.com using JSON API.
"""
import logging
import json
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NineOneMobilesScraper(BaseScraper):
    store_name = "91Mobiles"
    base_url = "https://www.91mobiles.com"
    search_url_template = "https://www.91mobiles.com/api/search?q={query}&v=1&cat=mobile"

    def _needs_selenium(self) -> bool:
        return False

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        """Extract products from 91Mobiles JSON API response."""
        products = []
        try:
            data = json.loads(page_source)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse 91Mobiles JSON response")
            return products

        # Navigate through API response structure
        items = data.get("devices", []) or data.get("results", []) or data.get("data", [])

        for item in items:
            try:
                # Get product name
                name = item.get("name") or item.get("device_name") or item.get("title", "")
                if not name or len(name) < 3:
                    continue

                # Get product URL
                product_url = item.get("link") or item.get("url") or item.get("device_url", "")
                if not product_url:
                    continue
                if not product_url.startswith("http"):
                    product_url = self._make_absolute_url(product_url)

                # Get price
                price = None
                if "price" in item:
                    price = self.parse_price(str(item.get("price", "")))
                elif "min_price" in item:
                    price = self.parse_price(str(item.get("min_price", "")))
                elif "current_price" in item:
                    price = self.parse_price(str(item.get("current_price", "")))
                
                if not price:
                    continue

                # Get original price
                orig = None
                if "original_price" in item:
                    orig = self.parse_price(str(item.get("original_price", "")))
                elif "max_price" in item:
                    orig = self.parse_price(str(item.get("max_price", "")))
                
                # Calculate discount
                discount = self.calculate_discount(price, orig)

                # Get image
                img = item.get("image_url") or item.get("img_url") or item.get("image", "")
                if img and not img.startswith("http"):
                    img = self._make_absolute_url(img)

                # Get rating and reviews
                rating = float(item.get("rating", 0)) if "rating" in item else 0.0
                reviews = int(item.get("reviews", 0)) if "reviews" in item else 0

                if self.is_valid_price(price):
                    products.append({
                        "name": name.strip(),
                        "price": price,
                        "original_price": orig,
                        "discount": discount,
                        "image_url": img,
                        "product_url": product_url,
                        "store": self.store_name,
                        "category": self._infer_category(name, query),
                        "rating": rating,
                        "reviews": reviews,
                        "availability": "In Stock" if item.get("available", True) else "Out of Stock",
                    })
            except Exception as e:
                self.logger.debug(f"91Mobiles item error: {e}")

        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        """Infer product category from name."""
        n = name.lower()
        q = query.lower()
        cats = {
            "Mobile Phones": ["phone", "mobile", "iphone", "samsung", "xiaomi", "oneplus", "realme", "redmi"],
            "Accessories": ["case", "screen protector", "charger", "cable"],
            "Headphones": ["earphone", "airpod", "headphone"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in q:
                    return cat
        return "Mobile Phones"
