from app import create_app
from database import db
from scrapers.gyapu import GyapuScraper
from scrapers.fatafatsewa import FatafatSewaScraper

app = create_app()

with app.app_context():
    # Let's clean the DB or just run the search
    print("\n=== Testing Gyapu Scraper ===")
    gyapu = GyapuScraper()
    gyapu_products = gyapu.search_products("samsung")
    print(f"Gyapu Scraper found {len(gyapu_products)} products:")
    for p in gyapu_products:
        print(f"- {p['name']} | Price: {p['price']} | URL: {p['product_url']}")

    print("\n=== Testing FatafatSewa Scraper ===")
    fatafat = FatafatSewaScraper()
    # Let's search for "samsung" on FatafatSewa
    fatafat_products = fatafat.search_products("samsung")
    print(f"FatafatSewa Scraper found {len(fatafat_products)} products:")
    for p in fatafat_products[:5]:
        print(f"- {p['name']} | Price: {p['price']} | URL: {p['product_url']} | Image: {p['image_url']}")

    # Save to database to check if persistence works!
    if fatafat_products:
        print("\nSaving FatafatSewa products to database...")
        stats = fatafat.save_to_database(fatafat_products, db.session)
        print("Save stats:", stats)
