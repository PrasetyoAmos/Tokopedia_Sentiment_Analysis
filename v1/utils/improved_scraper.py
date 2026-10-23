# improved_scraper.py - Versi yang terintegrasi dengan app.py

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import os
import re
import os

class ImprovedTokopediaScraper:
    """Improved scraper dengan selector yang tepat dari tes_scape2.py"""
    
    def __init__(self):
        self.data = []
        
    def bersihkan_teks(self, teks):
        """Membersihkan teks dari karakter whitespace tambahan dan mengganti koma"""
        if teks:
            teks_bersih = re.sub(r'\s+', ' ', teks.strip())  # Hilangkan karakter whitespace tambahan
            teks_bersih = teks_bersih.replace(',', '')  # Ganti koma dengan string kosong
            # Hilangkan simbol "/" dan "|"
            teks_bersih = teks_bersih.replace('/', '').replace('|', '')
            return teks_bersih
        return "Tidak tersedia"
    
    def setup_driver(self):
        """Setup Chrome driver dengan pengaturan standar"""
        options = Options()
        
        # Basic stability settings
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Standard window settings
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Untuk production, uncomment headless
        # options.add_argument("--headless")
        
        # Use chromedriver from tools folder
        chromedriver_path = os.path.join('tools', 'chromedriver.exe')
        driver = webdriver.Chrome(service=webdriver.chrome.service.Service(chromedriver_path), options=options)
        
        return driver
    
    def scrape_tokopedia(self, url, pages=5, progress_callback=None):
        """Main scraping function compatible dengan app.py"""
        # Import global scraping_status dari app.py
        try:
            from __main__ import scraping_status
            use_global_status = True
        except:
            use_global_status = False
            scraping_status = {"status": "idle", "progress": 0, "message": ""}
        
        driver = None
        
        try:
            print(f"[ImprovedScraper] Starting scrape for: {url}")
            
            if use_global_status:
                scraping_status["status"] = "running"
                scraping_status["progress"] = 0
                scraping_status["message"] = "Initializing Chrome driver..."
            
            driver = self.setup_driver()
            
            if use_global_status:
                scraping_status["progress"] = 10
                scraping_status["message"] = "Navigating to Tokopedia..."
            
            driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Check if page loaded correctly
            if "tokopedia.com" not in driver.current_url.lower():
                raise Exception("Not on Tokopedia page")
            
            self.data = []
            
            for i in range(pages):
                if use_global_status:
                    progress = 20 + (i * 60 / pages)
                    scraping_status["progress"] = int(progress)
                    scraping_status["message"] = f"Scraping page {i+1} of {pages}..."
                
                print(f"[ImprovedScraper] Processing page {i+1}")
                
                # Parse dengan BeautifulSoup (metode dari tes_scape2.py)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Gunakan selector yang tepat dari tes_scape2.py
                containers = soup.findAll('article', attrs={'class': 'css-ccpe8t'})
                
                if not containers:
                    print("[ImprovedScraper] Primary selector not found, trying alternatives...")
                    # Try alternative selectors
                    containers = soup.findAll('article', attrs={'class': re.compile(r'css-\w+')})
                
                print(f"[ImprovedScraper] Found {len(containers)} containers")
                
                for container in containers:
                    try:
                        # Ambil ulasan dengan selector yang tepat
                        review_element = container.find('span', attrs={'data-testid': 'lblItemUlasan'})
                        review = self.bersihkan_teks(review_element.text) if review_element else None
                        
                        # Skip jika tidak ada ulasan atau terlalu pendek
                        if not review or len(review) < 10:
                            continue
                        
                        # Ambil nama produk dengan selector yang tepat
                        nama_produk_element = container.find('a', attrs={'class': 'styProduct'})
                        if not nama_produk_element:
                            # Try alternative selectors
                            nama_produk_element = container.find('a', attrs={'href': re.compile(r'/product/')})
                        
                        nama_produk = self.bersihkan_teks(nama_produk_element.text) if nama_produk_element else "Tidak tersedia"
                        
                        # Ambil rating dengan selector yang tepat
                        rating_element = container.find('div', attrs={'data-testid': 'icnStarRating'})
                        if rating_element:
                            rating = self.bersihkan_teks(
                                rating_element.get('aria-label', '').replace('Rating ', '').replace('bintang', '')
                            )
                        else:
                            # Try alternative
                            rating_element = container.find('div', attrs={'aria-label': re.compile(r'Rating \d+ bintang')})
                            if rating_element:
                                rating_text = rating_element.get('aria-label', '')
                                numbers = re.findall(r'\d+', rating_text)
                                rating = numbers[0] if numbers else "5"
                            else:
                                rating = "5"  # Default
                        
                        # Tambahkan data
                        self.data.append({
                            'Ulasan': review,
                            'Nama_Produk': nama_produk,
                            'Rating': rating
                        })
                        
                    except Exception as e:
                        print(f"[ImprovedScraper] Error processing container: {e}")
                        continue
                
                print(f"[ImprovedScraper] Got {len(self.data)} reviews so far")
                
                # Rehat sejenak
                time.sleep(2)
                
                # Navigate ke halaman berikutnya
                if i < pages - 1:
                    try:
                        # Gunakan selector yang tepat dari tes_scape2.py
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label^='Laman berikutnya']"))
                        )
                        
                        # Scroll to button first
                        driver.execute_script("arguments[0].scrollIntoView();", next_button)
                        time.sleep(1)
                        
                        next_button.click()
                        time.sleep(3)
                        
                    except Exception as e:
                        print(f"[ImprovedScraper] Error navigating to next page: {e}")
                        # Try alternative selector
                        try:
                            next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='berikutnya']")
                            driver.execute_script("arguments[0].click();", next_button)
                            time.sleep(3)
                        except:
                            print("[ImprovedScraper] No more pages available")
                            break
            
            # Final processing
            if use_global_status:
                scraping_status["progress"] = 90
                scraping_status["message"] = f"Processing {len(self.data)} reviews..."
            
            if self.data:
                if use_global_status:
                    scraping_status["status"] = "completed"
                    scraping_status["progress"] = 100
                    scraping_status["message"] = f"Successfully scraped {len(self.data)} reviews!"
                
                print(f"[ImprovedScraper] Scraping completed with {len(self.data)} reviews")
                return True
            else:
                if use_global_status:
                    scraping_status["status"] = "error"
                    scraping_status["message"] = "No reviews found"
                
                print("[ImprovedScraper] No reviews found")
                return False
                
        except Exception as e:
            error_msg = f"Scraping error: {str(e)}"
            print(f"[ImprovedScraper] {error_msg}")
            
            if use_global_status:
                scraping_status["status"] = "error"
                scraping_status["message"] = error_msg
            
            return False
            
        finally:
            if driver:
                driver.quit()
                print("[ImprovedScraper] Browser closed")
    
    def save_to_csv(self, filename):
        """Save scraped data to CSV"""
        if not self.data:
            print("[ImprovedScraper] No data to save")
            return None
        
        try:
            df = pd.DataFrame(self.data)
            
            # Ensure proper encoding for Excel
            filepath = filename if filename.endswith('.csv') else f"{filename}.csv"
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            print(f"[ImprovedScraper] Saved {len(df)} reviews to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ImprovedScraper] Error saving CSV: {e}")
            return None


# Untuk testing standalone
if __name__ == "__main__":
    scraper = ImprovedTokopediaScraper()
    url = "https://www.tokopedia.com/samsung-official"
    
    if scraper.scrape_tokopedia(url, pages=2):
        scraper.save_to_csv("test_improved_scraping.csv")
        print("Testing completed!")