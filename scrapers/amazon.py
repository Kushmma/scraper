"""
NepCompare — Amazon India Scraper
Scrapes product listings from amazon.in using Selenium.
"""
import logging
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    store_name = "Amazon"
    base_url = "https://www.amazon.in"
    search_url_template = "https://www.amazon.in/s?k={query}"

    def _needs_selenium(self) -> bool:
        return True

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        """Extract products from Amazon search results."""
        soup = BeautifulSoup(page_source, "lxml")
        products = []

        # Try multiple selectors for product cards
        cards = (soup.select("div[data-component-type='s-search-result']") or
                 soup.select("div.s-result-item") or
                 soup.select("[data-asin]") or
                 soup.select("div[class*='product']"))

        for card in cards:
            try:
                # Get product name
                name_el = card.select_one("span.a-size-base-plus, h2, .productTitle")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3:
                    continue

                # Get product URL
                link_el = card.select_one("a.a-link-normal")
                product_url = link_el.get("href", "") if link_el else ""
                if not product_url:
                    continue
                if not product_url.startswith("http"):
                    product_url = self._make_absolute_url(product_url)

                # Get price
                price_el = card.select_one("span.a-price-whole, .productPrice")
                if not price_el:
                    for el in card.find_all(["span", "div"]):
                        text = el.get_text(strip=True)
                        if text.startswith("₹") or "Rs" in text:
                            price_el = el
                            break
                
                price = self.parse_price(price_el.get_text(strip=True) if price_el else "")
                if not price:
                    continue

                # Get original price (if available)
                orig_el = card.select_one("del, .a-price-strike")
                orig = self.parse_price(orig_el.get_text(strip=True) if orig_el else "")
                
                # Calculate discount
                discount = self.calculate_discount(price, orig)

                # Get image
                img_el = card.select_one("img")
                img = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
                if img and not img.startswith("http"):
                    img = self._make_absolute_url(img)

                # Get rating
                rating_el = card.select_one("span.a-icon-star-small span")
                rating = 0.0
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    rating = self.parse_price(rating_text)

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
                        "rating": rating if rating else 0.0,
                        "reviews": 0,
                        "availability": "In Stock",
                    })
            except Exception as e:
                self.logger.debug(f"Amazon card error: {e}")

        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        """Infer product category."""
        n = name.lower()
        q = query.lower()
        cats = {
            "Mobile Phones": ["phone", "mobile", "iphone", "samsung"],
            "Laptops": ["laptop", "notebook"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in q:
                    return cat
        return "Electronics"
