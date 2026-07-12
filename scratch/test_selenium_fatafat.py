from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

print("Setting up headless Chrome...")
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_page_load_timeout(30)

try:
    url = "https://fatafatsewa.com/search?q=samsung"
    print(f"Fetching URL: {url} ...")
    driver.get(url)
    time.sleep(5) # Wait for JS to execute and fetch results

    # Scroll down slightly
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
    time.sleep(3)

    print("Page Title:", driver.title)
    
    # Get page source and parse
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find grid
    grid = soup.find('div', class_=lambda x: x and 'grid-cols-2' in x and 'gap-4' in x)
    if grid:
        print("Found grid in Selenium!")
        children = grid.find_all(recursive=False)
        print(f"Direct children count in Selenium: {len(children)}")
        for idx, child in enumerate(children[:5]):
            print(f"\nChild {idx+1} outer HTML snippet:")
            print(str(child)[:1500])
    else:
        print("Could not find grid matching grid-cols-2 and gap-4 in Selenium")
        
        # Save HTML to see what's loaded
        with open("selenium_fatafat.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("Prettified HTML saved to selenium_fatafat.html")
        
finally:
    driver.quit()
    print("Driver closed.")
