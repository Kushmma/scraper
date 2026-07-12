"""
NepCompare — Daraz Nepal Scraper
Scrapes product listings from daraz.com.np using Selenium (JS-heavy SPA).
"""

import logging
import json
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DarazScraper(BaseScraper):
    store_name = "Daraz"
    base_url = "https://www.daraz.com.np"
    search_url_template = "https://www.daraz.com.np/catalog/?q={query}&ajax=true"

    def _needs_selenium(self) -> bool:
        return False

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        products = []
        try:
            data = json.loads(page_source)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse Daraz JSON response")
            return products

        mods = data.get("mods", {})
        items = mods.get("listItems", [])

        for item in items:
            try:
                name = item.get("name", "")
                if not name:
                    continue

                product_url = item.get("itemUrl", "")
                if product_url:
                    product_url = self._make_absolute_url(product_url)
                else:
                    continue

                price = float(item.get("price", 0))
                orig_str = item.get("originalPriceShow")
                orig = self.parse_price(orig_str) if orig_str else None
                discount = self.calculate_discount(price, orig)

                img = item.get("image", "")
                if img:
                    img = self._make_absolute_url(img)

                rating = float(item.get("ratingScore", 0))
                reviews = int(item.get("review", 0))

                products.append({
                    "name": name.strip(), "price": price, "original_price": orig,
                    "discount": discount, "image_url": img, "product_url": product_url,
                    "store": self.store_name, "category": self._infer_category(name, query),
                    "rating": rating, "reviews": reviews, "availability": "In Stock",
                })
            except Exception as e:
                self.logger.debug(f"Daraz JSON item error: {e}")
        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        n = name.lower()
        cats = {
            "Mobile Phones": ["phone","mobile","iphone","samsung","redmi","realme","oneplus","vivo","oppo"],
            "Laptops": ["laptop","notebook","macbook","chromebook"],
            "Tablets": ["tablet","ipad"],
            "Headphones & Earbuds": ["headphone","earphone","earbuds","earbud","airpod","headset"],
            "Smartwatches": ["smartwatch","smart watch","watch"],
            "Speakers": ["speaker","soundbar"],
            "Cameras": ["camera","dslr","gopro"],
            "Power Banks": ["power bank","powerbank"],
            "Television": ["tv","television"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in query.lower():
                    return cat
        return "Electronics"
