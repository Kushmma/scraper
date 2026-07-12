import requests
from bs4 import BeautifulSoup

url = "https://fatafatsewa.com/search?q=samsung"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("Analyzing FatafatSewa search result elements:")
# Let's look for common tags or attributes
# Is there a div class like product-grid, category-product-card, product-card, product-item, or group relative?
# Let's count some class occurrences in the document
class_counts = {}
for el in soup.find_all(class_=True):
    for cls in el['class']:
        class_counts[cls] = class_counts.get(cls, 0) + 1

# Sort class counts and print top 30
sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
print("\nTop 30 CSS classes:")
for cls, count in sorted_classes[:30]:
    print(f"{cls}: {count}")

# Find any links under /product or /products or similar path
print("\nSome links in search results:")
all_links = [a.get('href', '') for a in soup.find_all('a')]
product_links = [l for l in all_links if '/product/' in l or 'fatafatsewa.com/' in l or not l.startswith('/')]
print("Unique link paths (first 30):")
print(list(set(all_links))[:30])

# Let's inspect elements that contain "Samsung" or "Rs." to see their exact surrounding tags and classes
print("\nDetails of some elements with 'Rs.':")
count = 0
for el in soup.find_all(text=True):
    if 'Rs.' in el:
        parent = el.parent
        print(f"Parent tag: {parent.name} | Classes: {parent.get('class', [])} | Content: {el.strip()}")
        # Let's go up 2 levels
        grandparent = parent.parent
        print(f"Grandparent tag: {grandparent.name} | Classes: {grandparent.get('class', [])}")
        count += 1
        if count >= 10:
            break
