"""
NepCompare — Flipkart Scraper
Scrapes product listings from flipkart.com using Selenium.
"""
import logging
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    store_name = "Flipkart"
    base_url = "https://www.flipkart.com"
    search_url_template = "https://www.flipkart.com/search?q={query}"

    def _needs_selenium(self) -> bool:
        return True

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        """Extract products from Flipkart search results."""
        soup = BeautifulSoup(page_source, "lxml")
        products = []

        # Try multiple selectors for product cards
        cards = (soup.select("div._1AtVbE") or
                 soup.select("div._2kHmtP") or
                 soup.select("[data-id]") or
                 soup.select("div[class*='productContainer']"))

        for card in cards:
            try:
                # Get product name
                name_el = card.select_one("a.s1Q9rs, h2, .productTitle, [data-product-title]")
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
                price_el = card.select_one("div._30jeq3, .productPrice, [data-price]")
                if not price_el:
                    for el in card.find_all(["div", "span"]):
                        text = el.get_text(strip=True)
                        if text.startswith("₹") or "Rs" in text:
                            price_el = el
                            break
                
                price = self.parse_price(price_el.get_text(strip=True) if price_el else "")
                if not price:
                    continue

                # Get original price (strikethrough price)
                orig_el = card.select_one("del, ._3I9_wc")
                orig = self.parse_price(orig_el.get_text(strip=True) if orig_el else "")
                
                # Calculate discount
                discount = self.calculate_discount(price, orig)

                # Get image
                img_el = card.select_one("img")
                img = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
                if img and not img.startswith("http"):
                    img = self._make_absolute_url(img)

                # Get rating
                rating_el = card.select_one(".gUuXX_, .productRating")
                rating = 0.0
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    rating = self.parse_price(rating_text)  # Reuse price parser for numbers

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
                self.logger.debug(f"Flipkart card error: {e}")

        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        """Infer product category."""
        n = name.lower()
        q = query.lower()
        cats = {
            "Mobile Phones": ["phone", "mobile", "iphone", "samsung"],
            "Laptops": ["laptop", "notebook"],
            "Electronics": ["tv", "camera"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in q:
                    return cat
        return "Electronics"
