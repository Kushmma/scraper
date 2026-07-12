"""
NepCompare — PriceOye Scraper
Scrapes product listings from priceoye.pk and converts PKR to NPR.
"""
import logging
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class PriceOyeScraper(BaseScraper):
    store_name = "PriceOye"
    base_url = "https://priceoye.pk"
    search_url_template = "https://priceoye.pk/search?q={query}"
    
    # Current exchange rate PKR to NPR (updated: 0.30 instead of old 0.48)
    PKR_TO_NPR = 0.30 

    def _needs_selenium(self) -> bool:
        return False

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        soup = BeautifulSoup(page_source, "lxml")
        products = []
        
        # Try multiple selectors for product cards
        cards = soup.select("div.productBox") or soup.select("div.product-card") or soup.select("[data-product-id]")
        
        for card in cards:
            try:
                # Get product name - try multiple selectors
                name_el = card.select_one("h2, h3, .product-name, [data-product-name]")
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
                
                # Get price - try multiple patterns
                price_text = ""
                price_el = card.select_one(".price, .product-price, .current-price, [data-price]")
                if price_el:
                    price_text = price_el.get_text(strip=True)
                else:
                    # Fallback: look for any element with PKR or price-like content
                    for el in card.find_all(["span", "div"]):
                        text = el.get_text(strip=True)
                        if "Rs" in text or "PKR" in text or any(c.isdigit() for c in text):
                            price_text = text
                            break
                
                price_pkr = self.parse_price(price_text)
                if not price_pkr:
                    continue
                
                # Get original price
                orig_text = ""
                orig_el = card.select_one(".original-price, .mrp, del, .strikethrough")
                if orig_el:
                    orig_text = orig_el.get_text(strip=True)
                orig_pkr = self.parse_price(orig_text) if orig_text else None
                
                # Get image
                img_el = card.select_one("img")
                img = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
                if img and not img.startswith("http"):
                    img = self._make_absolute_url(img)
                
                # Convert to NPR
                price = round(price_pkr * self.PKR_TO_NPR, 2)
                orig = round(orig_pkr * self.PKR_TO_NPR, 2) if orig_pkr else None
                discount = self.calculate_discount(price, orig)
                
                if self.is_valid_price(price):
                    products.append({
                        "name": name.strip(), "price": price, "original_price": orig,
                        "discount": discount, "image_url": img, "product_url": product_url,
                        "store": self.store_name, "category": self._infer_category(name, query),
                        "rating": 0.0, "reviews": 0, "availability": "In Stock",
                    })
            except Exception as e:
                self.logger.debug(f"PriceOye card error: {e}")
                
        return products
    
    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        """Infer product category from name."""
        n = name.lower()
        q = query.lower()
        cats = {
            "Mobile Phones": ["phone", "mobile", "iphone", "samsung", "xiaomi", "oneplus"],
            "Laptops": ["laptop", "notebook"],
            "Tablets": ["tablet", "ipad"],
            "Headphones": ["headphone", "earphone", "earbuds"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in q:
                    return cat
        return "Electronics"
