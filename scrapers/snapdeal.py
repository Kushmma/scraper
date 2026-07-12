"""
NepCompare — Snapdeal Scraper
Scrapes product listings from snapdeal.com using Selenium.
"""
import logging
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SnapdealScraper(BaseScraper):
    store_name = "Snapdeal"
    base_url = "https://www.snapdeal.com"
    search_url_template = "https://www.snapdeal.com/search?keyword={query}"

    def _needs_selenium(self) -> bool:
        return True

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        """Extract products from Snapdeal search results."""
        soup = BeautifulSoup(page_source, "lxml")
        products = []

        # Try multiple selectors for product cards
        cards = (soup.select("div.productCardImg") or
                 soup.select("div.product-card") or
                 soup.select("[data-id]") or
                 soup.select("div[class*='product']"))

        for card in cards:
            try:
                # Get product name
                name_el = card.select_one("p.productCardImg__title, .productTitle, h2")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3:
                    continue

                # Get product URL
                link_el = card.select_one("a")
                product_url = link_el.get("href", "") if link_el else ""
                if not product_url:
                    continue
                if not product_url.startswith("http"):
                    product_url = self._make_absolute_url(product_url)

                # Get price
                price_el = card.select_one(".productCardPrice__discountedPrice, .productPrice")
                if not price_el:
                    for el in card.find_all(["span", "div"]):
                        text = el.get_text(strip=True)
                        if text.startswith("₹") or "Rs" in text:
                            price_el = el
                            break
                
                price = self.parse_price(price_el.get_text(strip=True) if price_el else "")
                if not price:
                    continue

                # Get original price
                orig_el = card.select_one("del, .productCardPrice__originalPrice")
                orig = self.parse_price(orig_el.get_text(strip=True) if orig_el else "")
                
                # Calculate discount
                discount = self.calculate_discount(price, orig)

                # Get image
                img_el = card.select_one("img")
                img = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
                if img and not img.startswith("http"):
                    img = self._make_absolute_url(img)

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
                self.logger.debug(f"Snapdeal card error: {e}")

        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        """Infer product category."""
        n = name.lower()
        return "Electronics"
