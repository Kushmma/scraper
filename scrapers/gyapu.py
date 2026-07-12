"""
NepCompare — Gyapu Scraper
Scrapes product listings from gyapu.com using Selenium.
"""
import logging
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GyapuScraper(BaseScraper):
    store_name = "Gyapu"
    base_url = "https://www.gyapu.com"
    search_url_template = "https://www.gyapu.com/search?keyword={query}"

    def _needs_selenium(self) -> bool:
        return True

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        """Extract products from Gyapu search results page."""
        soup = BeautifulSoup(page_source, "lxml")
        products = []

        # Try multiple selectors for product cards
        cards = (soup.select("div.product-item") or
                 soup.select(".product-card") or
                 soup.select("[data-product-id]") or
                 soup.select("div[class*='product']"))

        for card in cards:
            try:
                # Get product name
                name_el = card.select_one("h3, h2, .product-name, [data-product-name]")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3:
                    continue

                # Get product URL
                link_el = card.select_one("a")
                product_url = link_el.get("href", "") if link_el else ""
                if not product_url:
                    continue
                product_url = self._make_absolute_url(product_url)

                # Get price
                price_el = card.select_one(".price, .product-price, [data-price]")
                if not price_el:
                    for el in card.find_all(["span", "div"]):
                        text = el.get_text(strip=True)
                        if any(c.isdigit() for c in text) and ("Rs" in text or "NPR" in text):
                            price_el = el
                            break
                
                price = self.parse_price(price_el.get_text(strip=True) if price_el else "")
                if not price:
                    continue

                # Get original price
                orig_el = card.select_one("del, .original-price, .mrp")
                orig = self.parse_price(orig_el.get_text(strip=True) if orig_el else "")
                
                # Calculate discount
                discount = self.calculate_discount(price, orig)

                # Get image
                img_el = card.select_one("img")
                img = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
                if img and not img.startswith("http"):
                    img = self._make_absolute_url(img)

                # Only add if price is valid
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
                        "rating": 0.0,
                        "reviews": 0,
                        "availability": "In Stock",
                    })
            except Exception as e:
                self.logger.debug(f"Gyapu card error: {e}")

        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        """Infer product category from name."""
        n = name.lower()
        q = query.lower()
        cats = {
            "Mobile Phones": ["phone", "mobile", "iphone", "samsung", "xiaomi"],
            "Laptops": ["laptop", "notebook"],
            "Tablets": ["tablet", "ipad"],
            "Headphones": ["headphone", "earphone"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in q:
                    return cat
        return "Electronics"
