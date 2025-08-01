import time
import json
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")  # Headless mode for new Chrome versions
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_car_data(element):
    car = {
        "title": "",
        "price": "",
        "location": "",
        "link": "",
        "image_url": "",
        "brand": "",
        "year": "",
        "condition": "",
        "posted_time": "",
        "seller": ""
    }

    try:
        car['title'] = element.find_element(By.CSS_SELECTOR, "h3, h2, h4").text.strip()
    except:
        pass

    try:
        price_elem = element.find_element(By.CSS_SELECTOR, "span.price, div.price, span.product-price, div.product-price")
        car['price'] = price_elem.text.strip()
    except:
        try:
            spans = element.find_elements(By.TAG_NAME, "span")
            for sp in spans:
                if "रु" in sp.text or "Rs" in sp.text:
                    car['price'] = sp.text.strip()
                    break
        except:
            pass

    try:
        car['location'] = element.find_element(By.CSS_SELECTOR, "span.location, div.location").text.strip()
    except:
        pass

    try:
        car['link'] = element.find_element(By.TAG_NAME, "a").get_attribute("href")
    except:
        pass

    try:
        car['image_url'] = element.find_element(By.TAG_NAME, "img").get_attribute("src")
    except:
        pass

    # Seller info: based on typical HTML pattern from earlier data
    try:
        seller_elem = element.find_element(By.CSS_SELECTOR, ".seller-name, .seller, span.seller-name, div.seller-name, div.seller-info span, .seller-name")
        car['seller'] = seller_elem.text.strip()
    except:
        car['seller'] = ""  # If not found, leave empty
    try:
        car['condition'] = element.element.find_element(By.CSS_SELECTOR, "div.condition")
    except:
        pass

    text = car['title'].lower()
    brands = ['toyota', 'honda', 'hyundai', 'maruti', 'suzuki', 'nissan', 'ford', 'bmw', 'mercedes', 'audi', 'volkswagen', 'kia', 'mazda']
    for brand in brands:
        if brand in text:
            car['brand'] = brand.title()
            break

    match = re.search(r'(19|20)\d{2}', car['title'])
    if match:
        car['year'] = match.group()

    for cond in ['like new', 'excellent', 'good', 'used', 'fair']:
        if cond in text:
            car['condition'] = cond.title()
            break

    if 'ago' in element.text.lower():
        lines = element.text.split('\n')
        for line in lines:
            if 'ago' in line.lower():
                car['posted_time'] = line.strip()
                break

    return car

def scrape_hamrobazaar(max_cars=50):
    url = "https://hamrobazaar.com/category/cars/EB9C8147-07C0-4951-A962-381CDB400E37/F93D355F-CC20-4FFE-9CB7-6C7CDFF1DC50"
    driver = setup_driver(headless=True)
    driver.get(url)
    time.sleep(5)

    scraped = []
    seen_links = set()
    scroll_pause = 3
    retries = 0

    while len(scraped) < max_cars and retries < 25:
        car_elements = driver.find_elements(By.CSS_SELECTOR, ".card-product-linear")
        for el in car_elements:
            try:
                link = el.find_element(By.TAG_NAME, "a").get_attribute("href")
                if link and link not in seen_links:
                    car = extract_car_data(el)
                    if car['title']:
                        scraped.append(car)
                        seen_links.add(link)
                        print(f"Scraped: {car['title']} - Price: {car['price']} - Seller: {car['seller']}")
                        if len(scraped) >= max_cars:
                            break
            except:
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        retries += 1

    driver.quit()
    return scraped

def save_data(cars):
    if not cars:
        print("No cars scraped.")
        return
    with open("hamrobazaar_cars.json", "w", encoding="utf-8") as f:
        json.dump(cars, f, indent=2, ensure_ascii=False)
    pd.DataFrame(cars).to_csv("hamrobazaar_cars.csv", index=False)
    print("Data saved to hamrobazaar_cars.json and hamrobazaar_cars.csv")

if __name__ == "__main__":
    try:
        max_count = input("Enter number of cars to scrape (or press Enter for 50): ").strip()
        max_count = int(max_count) if max_count else 50
    except:
        max_count = 50

    results = scrape_hamrobazaar(max_cars=max_count)
    save_data(results)
