import requests
from bs4 import BeautifulSoup
import re

url = "https://fatafatsewa.com/search?q=samsung"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("Searching for product container divs...")

# Let's search for divs that have class names matching typical patterns
patterns = ['product', 'card', 'item', 'grid', 'price']
matched_divs = []
for div in soup.find_all('div'):
    classes = div.get('class', [])
    classes_str = ' '.join(classes)
    for p in patterns:
        if p in classes_str:
            matched_divs.append((classes_str, len(div.find_all('div'))))
            break

print(f"Total divs containing key patterns: {len(matched_divs)}")
# Print some of them
for cls, child_divs in list(set(matched_divs))[:30]:
    print(f"Class: {cls} | Child divs count: {child_divs}")

# Let's find all images with src containing /storage/ or products
print("\nProduct-related image sources:")
for img in soup.find_all('img'):
    src = img.get('src', '')
    data_src = img.get('data-src', '')
    alt = img.get('alt', '')
    if '/storage/' in src or '/storage/' in data_src or 'product' in src.lower() or 'product' in data_src.lower():
        print(f"Alt: {alt} | Src: {src} | Data-Src: {data_src}")

# Let's find all anchor tags and look for product links
print("\nLinks containing product-like slugs:")
prod_links = []
for a in soup.find_all('a'):
    href = a.get('href', '')
    text = a.get_text(strip=True)
    # Most e-commerce stores have product links. In WordPress it might be e.g. /product/name-here/ or /mobile/name-here
    # Let's print any link that is not /blog, /, /about, etc. and has a text content
    if href and not any(x in href for x in ['blog', 'category', 'brand', 'cart', 'checkout', 'my-account', 'contact', 'about', 'login', 'register', 'terms', 'privacy']) and len(text) > 10:
        prod_links.append((text, href))

print(f"Found {len(prod_links)} potential product links:")
for text, href in prod_links[:20]:
    print(f"Text: {text} | Link: {href}")
