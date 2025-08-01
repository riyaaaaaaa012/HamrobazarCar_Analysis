import time
import json
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class EnhancedCarScraper:
    def __init__(self, headless=True):
        self.driver = self.setup_browser(headless)

    def setup_browser(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        return webdriver.Chrome(options=options)

    def extract_car_info(self, element):
        try:
            lines = element.text.split('\n')
            car = {
                'title': lines[0] if lines else '',
                'price': '', 'location': '', 'year': '', 'brand': '',
                'condition': '', 'posted': '', 'link': '', 'image': '',
                'seller_name': '', 'seller_type': '', 'seller_phone': '',
                'contact_info': '', 'ad_id': ''
            }

            # Extract basic information
            for line in lines:
                if 'रू' in line or 'Rs' in line:
                    car['price'] = line
                if any(city in line.lower() for city in ['kathmandu', 'pokhara', 'bhaktapur', 'lalitpur']):
                    car['location'] = line
                if 'ago' in line.lower():
                    car['posted'] = line
                if any(cond in line.lower() for cond in ['new', 'used', 'excellent']):
                    car['condition'] = line

            # Extract year from title
            match = re.search(r'(19|20)\d{2}', car['title'])
            if match:
                car['year'] = match.group()

            # Extract brand
            brands = [
                'toyota', 'honda', 'hyundai', 'suzuki', 'nissan', 'ford',
                'tata', 'kia', 'mahindra', 'mitsubishi', 'volkswagen', 'chevrolet',
                'renault', 'subaru', 'mazda', 'jeep', 'datsun', 'isuzu', 'lexus',
                'bmw', 'mercedes', 'audi', 'land rover', 'skoda', 'maruti'
            ]
            for brand in brands:
                if brand in car['title'].lower():
                    car['brand'] = brand.title()
                    break

            # Extract link and image
            try:
                car['link'] = element.find_element(By.TAG_NAME, "a").get_attribute("href")
                if car['link']:
                    # Extract ad ID from URL
                    match = re.search(r'/([a-f0-9]+)$', car['link'])
                    if match:
                        car['ad_id'] = match.group(1)
            except:
                pass
            
            try:
                car['image'] = element.find_element(By.TAG_NAME, "img").get_attribute("src")
            except:
                pass

            # Try to extract phone number from title or text
            phone_pattern = r'\b(?:\+?977[-\s]?)?(?:98|97|96)\d{8}\b'
            full_text = element.text
            phone_match = re.search(phone_pattern, full_text)
            if phone_match:
                car['seller_phone'] = phone_match.group()

            # Look for seller information in the element text
            for line in lines:
                # Check for business names (usually contain "Pvt", "Ltd", "Motors", etc.)
                if any(keyword in line for keyword in ['Pvt', 'Ltd', 'Motors', 'Auto', 'Automobiles', 'Traders']):
                    car['seller_name'] = line.strip()
                    car['seller_type'] = 'Business/Dealer'
                    break

            # If no business found, look for individual indicators
            if not car['seller_name']:
                car['seller_type'] = 'Individual'
                # Try to extract name from contact or other patterns
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['contact', 'call', 'owner']):
                        car['contact_info'] = line.strip()

            return car
        except Exception as e:
            print(f"Error extracting car info: {e}")
            return None

    def extract_detailed_seller_info(self, car_url):
        """Extract detailed seller information from individual car listing page"""
        try:
            # Save current window handle
            main_window = self.driver.current_window_handle
            
            # Open new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Navigate to the car listing
            self.driver.get(car_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            seller_info = {
                'seller_name': '',
                'seller_type': '',
                'seller_location': '',
                'seller_joined': '',
                'seller_rating': '',
                'seller_total_ads': '',
                'seller_contact': '',
                'seller_verified': False
            }
            
            # Get page source to search for seller information
            page_source = self.driver.page_source
            
            # Look for seller information in various patterns
            selectors_to_try = [
                # Common seller selectors
                ".seller-info", ".user-info", ".posted-by", ".seller-name",
                ".user-name", ".seller-details", ".advertiser-info",
                "[data-testid*='seller']", "[class*='seller']", "[class*='user']",
                ".contact-info", ".owner-info", ".dealer-info"
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for elem in elements:
                            text = elem.text.strip()
                            if text and len(text) > 2:
                                if not seller_info['seller_name']:
                                    seller_info['seller_name'] = text
                                break
                except:
                    continue
            
            # Look for business indicators
            business_keywords = ['pvt', 'ltd', 'motors', 'auto', 'automobiles', 'traders', 'showroom', 'garage']
            if any(keyword in seller_info['seller_name'].lower() for keyword in business_keywords):
                seller_info['seller_type'] = 'Business/Dealer'
            else:
                seller_info['seller_type'] = 'Individual'
            
            # Try to find contact information
            contact_selectors = [".contact", ".phone", ".mobile", "[class*='contact']", "[class*='phone']"]
            for selector in contact_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        contact_text = elements[0].text.strip()
                        phone_match = re.search(r'\b(?:\+?977[-\s]?)?(?:98|97|96)\d{8}\b', contact_text)
                        if phone_match:
                            seller_info['seller_contact'] = phone_match.group()
                            break
                except:
                    continue
            
            # Look for verification badges
            verification_selectors = [".verified", ".badge", "[class*='verified']", "[class*='badge']"]
            for selector in verification_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and any('verif' in elem.text.lower() for elem in elements):
                        seller_info['seller_verified'] = True
                        break
                except:
                    continue
            
            # Parse page text for additional information
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Look for "Member since" or "Joined" information
            date_patterns = [
                r'member since\s*:?\s*([^\n]+)',
                r'joined\s*:?\s*([^\n]+)',
                r'since\s*:?\s*(\d{4})'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    seller_info['seller_joined'] = match.group(1).strip()
                    break
            
            # Look for total ads information
            ads_patterns = [
                r'(\d+)\s*ads?',
                r'total\s*ads?\s*:?\s*(\d+)',
                r'listings?\s*:?\s*(\d+)'
            ]
            for pattern in ads_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    seller_info['seller_total_ads'] = match.group(1)
                    break
            
            # Close tab and return to main window
            self.driver.close()
            self.driver.switch_to.window(main_window)
            
            return seller_info
            
        except Exception as e:
            print(f"Error extracting detailed seller info: {e}")
            # Ensure we return to main window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(main_window)
            except:
                pass
            
            return {
                'seller_name': '',
                'seller_type': '',
                'seller_location': '',
                'seller_joined': '',
                'seller_rating': '',
                'seller_total_ads': '',
                'seller_contact': '',
                'seller_verified': False
            }

    def scrape_page(self, url, max_cars=300, detailed_seller_info=False):
        print(f" Navigating to: {url}")
        self.driver.get(url)
        time.sleep(5)
        cars = []
        seen_ad_ids = set()

        scroll_attempts = 0
        while len(cars) < max_cars and scroll_attempts < 30:
            elements = self.driver.find_elements(By.CSS_SELECTOR, '.card-product-linear')
            print(f"Found {len(elements)} car elements on page")

            for el in elements:
                car = self.extract_car_info(el)
                if car and car['ad_id'] and car['ad_id'] not in seen_ad_ids:
                    seen_ad_ids.add(car['ad_id'])

                    if detailed_seller_info and car['link']:
                        detailed_seller = self.extract_detailed_seller_info(car['link'])
                        car.update({k: v for k, v in detailed_seller.items() if v})

                    cars.append(car)
                    print(f" Scraped: {car['title'][:40]} | Seller: {car['seller_name']}")

                    if len(cars) >= max_cars:
                        break

        # Scroll and wait
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                print("No more content. Exiting scroll.")
                break

            scroll_attempts += 1

        return cars


    def save_data(self, cars, filename='hamrobazaar_cars'):
        df = pd.DataFrame(cars)
        df.to_csv(f"{filename}.csv", index=False)
        with open(f"{filename}.json", "w", encoding="utf-8") as f:
            json.dump(cars, f, indent=2, ensure_ascii=False)
        print(f" Saved {len(cars)} cars to {filename}.csv and .json")
        
        # Print summary of seller information found
        sellers_found = sum(1 for car in cars if car['seller_name'])
        phones_found = sum(1 for car in cars if car['seller_phone'])
        businesses_found = sum(1 for car in cars if car['seller_type'] == 'Business/Dealer')
        
        print(f"\n Seller Information Summary:")
        print(f"  • Cars with seller names: {sellers_found}/{len(cars)}")
        print(f"  • Cars with phone numbers: {phones_found}/{len(cars)}")
        print(f"  • Business/Dealer listings: {businesses_found}/{len(cars)}")

    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    url = "https://hamrobazaar.com/category/cars/EB9C8147-07C0-4951-A962-381CDB400E37/F93D355F-CC20-4FFE-9CB7-6C7CDFF1DC50"
    
    print(" Enhanced HamroBazar Car Scraper with Seller Information")
    print("=" * 60)
    
    max_cars = input("Enter number of cars to scrape (default 10): ").strip()
    max_cars = int(max_cars) if max_cars.isdigit() else 10
    
    detailed_info = input("Extract detailed seller info from individual pages? (slower) [y/N]: ").strip().lower()
    detailed_seller_info = detailed_info in ['y', 'yes']
    
    if detailed_seller_info:
        print("  Detailed mode: This will take longer as it visits each listing page")
    
    scraper = EnhancedCarScraper(headless=True)
    try:
        cars = scraper.scrape_page(url, max_cars=max_cars, detailed_seller_info=detailed_seller_info)
        scraper.save_data(cars)
        
        # Print additional statistics
        print("\n Additional Statistics:")
        unique_sellers = len(set(car['seller_name'] for car in cars if car['seller_name']))
        print(f"  • Unique sellers identified: {unique_sellers}")
        
        if unique_sellers > 0:
            from collections import Counter
            seller_counts = Counter(car['seller_name'] for car in cars if car['seller_name'])
            print(f"  • Most active seller: {seller_counts.most_common(1)[0][0]} ({seller_counts.most_common(1)[0][1]} ads)")
        
    except Exception as e:
        print(f" Error during scraping: {e}")
    finally:
        scraper.close()


main()
