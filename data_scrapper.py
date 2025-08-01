import time
import json
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class CarScraper:
    def __init__(self, headless=True):
        self.driver = self.setup_browser(headless)

    def setup_browser(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)

    def extract_car_info(self, element):
        try:
            lines = element.text.split('\n')
            car = {
                'title': lines[0] if lines else '',
                'price': '', 'location': '', 'year': '', 'brand': '',
                'condition': '', 'posted': '', 'link': '', 'image': ''
            }

            for line in lines:
                if 'रू' in line or 'Rs' in line:
                    car['price'] = line
                if any(city in line.lower() for city in ['kathmandu', 'pokhara', 'bhaktapur', 'lalitpur']):
                    car['location'] = line
                if 'ago' in line.lower():
                    car['posted'] = line
                if any(cond in line.lower() for cond in ['new', 'used', 'excellent']):
                    car['condition'] = line

            match = re.search(r'(19|20)\d{2}', car['title'])
            if match:
                car['year'] = match.group()

            #brands = ['toyota', 'honda', 'hyundai', 'suzuki', 'nissan', 'ford']
            brands = [
            'toyota', 'honda', 'hyundai', 'suzuki', 'nissan', 'ford',
            'tata', 'kia', 'mahindra', 'mitsubishi', 'volkswagen', 'chevrolet',
            'renault', 'subaru', 'mazda', 'jeep', 'datsun', 'isuzu', 'lexus',
            'bmw', 'mercedes', 'audi', 'land rover', 'skoda'
]
            for brand in brands:
                if brand in car['title'].lower():
                    car['brand'] = brand.title()
                    break

            try:
                car['link'] = element.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                pass
            try:
                car['image'] = element.find_element(By.TAG_NAME, "img").get_attribute("src")
            except:
                pass

            return car
        except:
            return None

    def scrape_page(self, url, max_cars=20):
        self.driver.get(url)
        time.sleep(5)
        cars = []

        while len(cars) < max_cars:
            elements = self.driver.find_elements(By.CSS_SELECTOR, '.card-product-linear')
            for el in elements:
                if len(cars) >= max_cars:
                    break
                car = self.extract_car_info(el)
                if car and car['title'] not in [c['title'] for c in cars]:
                    cars.append(car)
                    print(f"Scraped: {car['title'][:40]}...")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        return cars

    def save_data(self, cars, filename='hamrobazaar_cars'):
        pd.DataFrame(cars).to_csv(f"{filename}.csv", index=False)
        with open(f"{filename}.json", "w", encoding="utf-8") as f:
            json.dump(cars, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(cars)} cars to {filename}.csv and .json")

    def close(self):
        if self.driver:
            self.driver.quit()


def main():
    url = "https://hamrobazaar.com/category/cars/EB9C8147-07C0-4951-A962-381CDB400E37/F93D355F-CC20-4FFE-9CB7-6C7CDFF1DC50"
    max_cars = input("Enter number of cars to scrape (default 20): ").strip()
    max_cars = int(max_cars) if max_cars.isdigit() else 20

    scraper = CarScraper(headless=True)
    try:
        cars = scraper.scrape_page(url, max_cars=max_cars)
        scraper.save_data(cars)
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
