import requests
from bs4 import BeautifulSoup

url = "https://fatafatsewa.com/search?q=samsung"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

# Find the grid element
grid = soup.find('div', class_=lambda x: x and 'grid-cols-2' in x and 'gap-4' in x)
if grid:
    print("Found grid!")
    # Let's count direct children
    children = grid.find_all(recursive=False)
    print(f"Direct children count: {len(children)}")
    if len(children) > 0:
        first_child = children[0]
        print("\nFirst child tag name:", first_child.name)
        print("First child classes:", first_child.get('class', []))
        print("First child outer HTML snippet:")
        print(str(first_child)[:1500])
else:
    print("Could not find grid matching grid-cols-2 and gap-4")

    # Let's write the soup HTML to a temporary file so we can search it if needed
    with open("fatafat_search.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print("Prettified HTML saved to fatafat_search.html for inspection")
