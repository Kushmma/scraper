import requests

def check_site(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
        print(f"URL: {url} -> Status: {r.status_code}, Length: {len(r.text)}")
        return r.text[:500]
    except Exception as e:
        print(f"Error {url}: {e}")
        return None

print("Checking Gyapu...")
check_site("https://www.gyapu.com/search?keyword=samsung")

print("\nChecking FatafatSewa HTML...")
check_site("https://fatafatsewa.com/?s=samsung")

print("\nChecking FatafatSewa API...")
check_site("https://api.fatafatsewa.com/api/v1/products")
