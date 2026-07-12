import requests
from bs4 import BeautifulSoup
import json

url = "https://fatafatsewa.com/?s=samsung"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("FatafatSewa HTML response status:", r.status_code)

# Let's search for some typical keywords or elements in the page
print("Title of page:", soup.title.string if soup.title else "No title")

# Check if there are any specific links or classes
# Let's search for "samsung" text in links or headers to see structure
samsung_links = []
for a in soup.find_all('a'):
    href = a.get('href', '')
    text = a.get_text(strip=True)
    if 'samsung' in href.lower() or 'samsung' in text.lower():
        samsung_links.append((text, href))

print(f"Found {len(samsung_links)} links containing 'samsung'")
for text, href in samsung_links[:20]:
    print(f"Text: {text} | Link: {href}")

# Let's look for product elements or price elements
# For example, tags containing 'Rs' or 'रु' or span classes
rs_spans = []
for span in soup.find_all(['span', 'div', 'p']):
    text = span.get_text(strip=True)
    if 'Rs.' in text or 'रु' in text:
        # Check if it has a class
        classes = span.get('class', [])
        rs_spans.append((span.name, classes, text[:50]))

print(f"\nFound {len(rs_spans)} elements containing price indicators")
for tag, classes, text in rs_spans[:20]:
    print(f"Tag: {tag} | Classes: {classes} | Text: {text}")
