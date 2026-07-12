"""
NepCompare — FatafatSewa Scraper
Scrapes product listings from fatafatsewa.com using Selenium.
"""
import logging
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FatafatSewaScraper(BaseScraper):
    store_name = "FatafatSewa"
    base_url = "https://fatafatsewa.com"
    search_url_template = "https://fatafatsewa.com/search?q={query}"

    def _needs_selenium(self) -> bool:
        return True

    def _fetch_with_selenium(self, url: str) -> str:
        """Override to ensure FatafatSewa product links render by scrolling and waiting if needed."""
        driver = self._get_driver()
        try:
            self._random_delay()
            driver.get(url)
            
            import time
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # 1. Wait for body
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 2. Scroll and check loop (up to 3 attempts, waiting for product links to render)
            for attempt in range(3):
                # Scroll down half way
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1.5)
                # Scroll down all the way
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                page_source = driver.page_source
                if page_source and "/product/" in page_source:
                    self.logger.info(f"Product links rendered successfully on attempt {attempt + 1}")
                    return page_source
                
                self.logger.info(f"Product links not visible yet (attempt {attempt + 1}/3). Waiting...")
                time.sleep(2.0)
                
            self.logger.warning("Reached max rendering attempts. Returning current page source.")
            return driver.page_source or ""
            
        except Exception as e:
            self.logger.error(f"Selenium fetch error for {url}: {e}")
            return ""

    def _extract_products_from_page(self, page_source: str, query: str) -> list[dict]:
        soup = BeautifulSoup(page_source, "lxml")
        products = []

        # Find the product grid/cards - try multiple selectors
        cards = (soup.select("div.bg-white.rounded-xl.border.border-gray-100.overflow-hidden") or
                 soup.select(".product-card, .product-item") or
                 soup.select("[data-product-id]") or
                 soup.select("div[class*='product']"))

        for card in cards:
            try:
                # Find anchor element
                a_el = card.select_one("a")
                if not a_el:
                    continue

                product_url = a_el.get("href", "")
                if product_url:
                    product_url = self._make_absolute_url(product_url)
                else:
                    continue

                # Check if it is a skeleton loader (has bg-gray-100 animate-pulse or similar)
                if card.select_one(".animate-pulse"):
                    continue

                # Name - try multiple selectors
                name_el = card.select_one("h3, h2, .product-name, [data-product-name]")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3:
                    continue

                # Price - try multiple selectors
                price_el = card.select_one("span.text-base.font-bold, .text-gray-900, .product-price, [data-price]")
                if not price_el:
                    # Fallback: find any span with bold or price-like content
                    for span in card.find_all(["span", "div"]):
                        text = span.get_text(strip=True)
                        if any(c.isdigit() for c in text) and ("Rs" in text or "NPR" in text or any(ord(c) > 127 for c in text)):
                            price_el = span
                            break
                
                price = self.parse_price(price_el.get_text(strip=True) if price_el else "")

                # Original Price
                orig_el = card.select_one("del, .original-price, .mrp")
                orig = self.parse_price(orig_el.get_text(strip=True) if orig_el else "")
                
                # Discount
                discount = self.calculate_discount(price, orig)

                # Image
                img_el = card.select_one("img")
                img = img_el.get("src", "") or img_el.get("data-src", "") if img_el else ""
                if img:
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
                self.logger.debug(f"FatafatSewa card error: {e}")

        return products

    @staticmethod
    def _infer_category(name: str, query: str) -> str:
        n = name.lower()
        cats = {
            "Mobile Phones": ["phone", "mobile", "iphone", "samsung", "redmi", "realme", "oneplus", "vivo", "oppo"],
            "Laptops": ["laptop", "notebook", "macbook", "chromebook"],
            "Tablets": ["tablet", "ipad"],
            "Headphones & Earbuds": ["headphone", "earphone", "earbuds", "earbud", "airpod", "headset"],
            "Smartwatches": ["smartwatch", "smart watch", "watch"],
            "Speakers": ["speaker", "soundbar"],
            "Cameras": ["camera", "dslr", "gopro"],
            "Power Banks": ["power bank", "powerbank"],
            "Television": ["tv", "television"],
        }
        for cat, kws in cats.items():
            for kw in kws:
                if kw in n or kw in query.lower():
                    return cat
        return "Electronics"
