import requests
from bs4 import BeautifulSoup

def test_url(url, description):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
        print(f"\n--- {description} ---")
        print(f"URL: {url} -> Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200:
            if "json" in r.headers.get("Content-Type", "") or r.text.strip().startswith("{"):
                try:
                    data = r.json()
                    print("JSON keys:", data.keys() if isinstance(data, dict) else "list length " + str(len(data)))
                    if isinstance(data, dict) and "data" in data:
                        print("Items count in data:", len(data["data"]))
                        if len(data["data"]) > 0:
                            print("First item keys:", data["data"][0].keys())
                            print("First item Name/Title/Price:", data["data"][0].get("name"), "/", data["data"][0].get("price"))
                except Exception as ex:
                    print("Error parsing JSON:", ex)
                    print("Snippet:", r.text[:200])
            else:
                soup = BeautifulSoup(r.text, 'html.parser')
                print("HTML title:", soup.title.string if soup.title else "None")
                # print elements that look like products
                # Let's search for "samsung" text inside text or tags
                products_found = 0
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    text = a.get_text(strip=True)
                    if samsung_in_words(text) and samsung_in_words(href):
                        products_found += 1
                print("Count of links containing 'samsung':", products_found)
    except Exception as e:
        print(f"Error {description}: {e}")

def samsung_in_words(txt):
    return 'samsung' in txt.lower()

test_url("https://fatafatsewa.com/search?q=samsung", "FatafatSewa /search?q=samsung")
test_url("https://fatafatsewa.com/search/samsung", "FatafatSewa /search/samsung")
test_url("https://fatafatsewa.com/catalogsearch/result/?q=samsung", "FatafatSewa /catalogsearch/result/?q=samsung")
test_url("https://api.fatafatsewa.com/api/v1/products?per_page=10&search=samsung", "FatafatSewa API with search=samsung")
test_url("https://api.fatafatsewa.com/api/v1/products?per_page=10&q=samsung", "FatafatSewa API with q=samsung")
test_url("https://api.fatafatsewa.com/api/v1/products?search=samsung", "FatafatSewa API with search=samsung and default per_page")
