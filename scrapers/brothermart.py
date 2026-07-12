"""
NepCompare — Brother Mart Scraper
Scrapes product listings from brother-mart.com.
"""
import logging
import json
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BrotherMartScraper(BaseScraper):
    store_name = "Brother-mart"
    base_url = "https://brother-mart.com"
    search_url_template = "https://brother-mart.com/search/suggest.json?q={query}&resources[type]=product&resources[limit]=50"

    def _needs_selenium(self) -> bool:
        return False

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        products = []
        try:
            data = json.loads(page_source)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse Brother-mart JSON response")
            return products

        resources = data.get("resources", {}).get("results", {})
        items = resources.get("products", [])

        for item in items:
            try:
                name = item.get("title", "")
                if not name:
                    continue

                product_url = item.get("url", "")
                if product_url:
                    product_url = self._make_absolute_url(product_url)
                else:
                    continue

                price_str = item.get("price")
                price = float(price_str) if price_str else 0.0
                
                orig_str = item.get("compare_at_price_max")
                orig = float(orig_str) if orig_str and float(orig_str) > price else None
                
                discount = self.calculate_discount(price, orig)

                img = item.get("image", "")
                if img:
                    # some shopify images are missing https: protocol
                    if img.startswith("//"):
                        img = "https:" + img

                products.append({
                    "name": name.strip(), "price": price, "original_price": orig,
                    "discount": discount, "image_url": img, "product_url": product_url,
                    "store": self.store_name, "category": "Electronics",
                    "rating": 0.0, "reviews": 0, "availability": "In Stock" if item.get("available") else "Out of Stock",
                })
            except Exception as e:
                self.logger.debug(f"Brother-mart JSON item error: {e}")
        return products
