import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

def extract_price_from_text(text):
    """Extract numeric price from text with currency symbols."""
    if not text:
        return None
    # Match patterns like $19.99, 19.99, £19.99, €19.99, ₹19.99, etc.
    match = re.search(r'[\$£€¥₹₽]?\s*(\d+(?:[.,]\d+)?)\s*(?:USD|EUR|GBP|INR|BRL)?', text.strip())
    if match:
        try:
            price_str = match.group(1).replace(',', '.')
            return float(price_str)
        except ValueError:
            return None
    return None

def get_price_with_selenium(url):
    """Scrape using Selenium to handle JavaScript-rendered content."""
    if not SELENIUM_AVAILABLE:
        return None, None
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get(url)
        
        # Wait for page to load - up to 10 seconds
        wait = WebDriverWait(driver, 10)
        
        try:
            # Wait for common price elements to appear
            wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), '₹') or contains(text(), '$') or contains(text(), '€')]")))
        except:
            # If price elements don't appear, just continue with what we have
            time.sleep(3)
        
        # Get page title
        product = driver.title or "Unknown Product"
        if len(product) > 100:
            product = product[:100]
        
        # Comprehensive price selectors for different sites
        price_selectors = [
            # Amazon variants (US, India, international)
            'span.a-price-whole',
            'span[data-a-color="price"]',
            '.a-price.a-text-price.a-size-medium.a-text-bold',
            'span.a-price',
            
            # Amazon India specific
            'div._30jeq3._16Jk6d',  # Old Amazon India price
            'span._2k2we._3LrHMZ',  # Current Amazon India price
            'span.a-price-range span.a-price-whole',
            '[data-a-price]',
            
            # Flipkart
            '.mrp',
            '.sellingPrice',
            'span._3qQ9m',
            'div._25b18c',
            
            # Generic selectors
            '[data-price]',
            '.product-price',
            '.current-price',
            '[itemprop="price"]',
            '.sale-price',
            '.product-cost',
            'span[aria-label*="price" i]',
            '.price-tag',
            '.product-original-price',
            '._3I9_wc',  # Flipkart new format
            
            # Price in data attributes
            '[data-productprice]',
            '[data-selling-price]',
        ]
        
        price = None
        for selector in price_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text:
                        extracted = extract_price_from_text(text)
                        if extracted and extracted > 0:
                            price = extracted
                            print(f"Found price via selector '{selector}': {price}")
                            break
                if price:
                    break
            except Exception as e:
                continue
        
        # Fallback: Search for price patterns in all visible text
        if not price:
            try:
                body_text = driver.find_element(By.TAG_NAME, 'body').text
                # Find all numbers that look like prices (with currency symbols or between 10 and 999999)
                price_pattern = r'[\$£€¥₹₽]?\s*(\d{1,6}(?:[.,]\d{1,2})?)'
                matches = re.finditer(price_pattern, body_text)
                
                prices_found = []
                for match in matches:
                    try:
                        price_str = match.group(1).replace(',', '.')
                        p = float(price_str)
                        if 10 <= p <= 999999:  # Reasonable price range
                            prices_found.append(p)
                    except:
                        continue
                
                if prices_found:
                    # Get the first reasonable price found
                    price = prices_found[0]
                    print(f"Found price from text pattern: {price}")
            except Exception as e:
                print(f"Text pattern search error: {e}")
        
        driver.quit()
        
        if price:
            return product, price
        return product, None
    
    except Exception as e:
        print(f"Selenium error: {e}")
        try:
            driver.quit()
        except:
            pass
        return None, None

def get_price(url):
    """Scrape product name and price from a URL."""
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # perform request with SSL handling
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.exceptions.SSLError as ssl_e:
                # Provide a clear error message for SSL problems
                raise ValueError("SSL error when accessing URL. The certificate may be invalid or blocked by the environment.") from ssl_e
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Try to extract product title (more comprehensive)
            product = "Unknown Product"
            
            # Priority order for product names
            title_selectors = [
                soup.find('h1', {'class': lambda x: x and 'product' in x.lower()}),
                soup.find('h1'),
                soup.find('meta', {'property': 'og:title'}),
                soup.find('meta', {'name': 'title'}),
                soup.find('title'),
            ]
            
            for selector in title_selectors:
                if selector:
                    if selector.name == 'meta':
                        title_text = selector.get('content', '')
                    else:
                        title_text = selector.get_text(strip=True)
                    
                    if title_text and len(title_text) > 3:  # Avoid very short titles
                        product = title_text[:100]  # Limit length
                        break
            
            # Try to extract price (expanded patterns for more websites)
            price = None
            
            # Common price selectors
            price_selectors = [
                # Direct class/id matches
                soup.find('span', {'class': 'price'}),
                soup.find('div', {'class': 'price'}),
                soup.find('span', {'id': 'price'}),
                soup.find('div', {'id': 'price'}),
                
                # Amazon specific
                soup.find('span', {'id': 'priceblock_ourprice'}),
                soup.find('span', {'id': 'priceblock_dealprice'}),
                soup.find('span', {'class': 'a-price'}),
                soup.find('span', {'class': 'a-price-whole'}),
                soup.find('span', attrs={'data-a-color': 'price'}),
                
                # Amazon India specific
                soup.find('span', {'class': '_2k2we'}),
                soup.find('div', {'class': '_30jeq3'}),
                
                # Flipkart
                soup.find('div', {'class': '_25b18c'}),
                soup.find('span', {'class': 'mrp'}),
                soup.find('span', {'class': 'sellingPrice'}),
                soup.find('span', {'class': '_3I9_wc'}),
                
                # Generic patterns
                soup.find('span', class_=lambda x: x and 'price' in x.lower()),
                soup.find('div', class_=lambda x: x and 'price' in x.lower()),
                soup.find(attrs={'data-price': True}),
                soup.find(attrs={'data-productprice': True}),
                soup.find(attrs={'data-selling-price': True}),
                soup.find(attrs={'itemprop': 'price'}),
                
                # Meta tags
                soup.find('meta', {'property': 'og:price:amount'}),
                soup.find('meta', {'name': 'price'}),
            ]
            
            for selector in price_selectors:
                if selector:
                    if selector.name == 'meta':
                        price_text = selector.get('content', '')
                    else:
                        price_text = selector.get_text(strip=True)
                    
                    # Extract numeric value (handle various formats)
                    # Match patterns like $19.99, 19.99, £19.99, ₹19.99, etc.
                    match = re.search(r'[\$£€¥₹₽]?\s*(\d+(?:[.,]\d+)*)', price_text.replace(',', '').replace(' ', ''))
                    if match:
                        price_str = match.group(1).replace(',', '.')
                        try:
                            price = float(price_str)
                            break
                        except ValueError:
                            continue
            
            # Try JSON-LD structured data as fallback
            if not price:
                json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
                for script in json_scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            data = data[0]
                        if 'offers' in data:
                            offers = data['offers']
                            if isinstance(offers, list):
                                offers = offers[0]
                            if 'price' in offers:
                                price = float(offers['price'])
                                break
                    except:
                        continue
            
            if price:
                return product, price
            else:
                # BeautifulSoup didn't find price, try Selenium for JS-rendered content
                if SELENIUM_AVAILABLE:
                    print(f"Trying Selenium for {url}...")
                    product_sel, price_sel = get_price_with_selenium(url)
                    if price_sel:
                        return product_sel or product, price_sel
                
                # Detect if this looks like a homepage
                is_homepage = (
                    'amazon' in url.lower() and '/dp/' not in url and '/gp/' not in url or
                    url.rstrip('/').endswith(('amazon.com', 'amazon.in', 'flipkart.com', 'ebay.com', '.com', '.in')) or
                    len(url.split('/')) <= 4
                )
                
                if is_homepage:
                    raise ValueError(f"❌ This is a homepage/category page, not a product page. Please paste a direct product URL:\n   • Amazon: amazon.com/dp/BXXXXXXXXXX\n   • Flipkart: flipkart.com/p/XXXXXXXXX\n   • eBay: ebay.com/itm/XXXXXXXXX")
                else:
                    # More helpful error message
                    error_msg = f"❌ Cannot extract price from this page. Possible reasons:\n"
                    error_msg += f"   • The website structure is not the standard format\n"
                    error_msg += f"   • Price information is in a non-standard location\n"
                    error_msg += f"   • The page requires more JavaScript rendering time\n"
                    error_msg += f"\nTry these solutions:\n"
                    error_msg += f"   1. Copy the exact product URL from your browser\n"
                    error_msg += f"   2. Make sure it's a product page (not search/category)\n"
                    error_msg += f"   3. Check that the page displays price when you open it\n"
                    error_msg += f"   4. Try a different product or website"
                    raise ValueError(error_msg)
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying
                continue
            print(f"Timeout error for {url}")
            raise TimeoutError(f"Website took too long to respond. The site may be slow or not accessible.")
        
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            print(f"Connection error for {url}")
            raise ConnectionError(f"Could not connect to the website. Please check if the URL is correct and the website is accessible.")
        
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error for {url}: {e.response.status_code}")
            if e.response.status_code == 403:
                raise PermissionError(f"Access denied (403). The website is blocking automated requests.")
            elif e.response.status_code == 429:
                raise ConnectionError(f"Too many requests (429). Please try again later.")
            elif e.response.status_code == 404:
                raise ValueError(f"Page not found (404). Please check the URL.")
            else:
                raise ValueError(f"Website returned an error (HTTP {e.response.status_code}).")
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            raise ValueError(f"Error scraping the website: {str(e)}")
    
    return None, None
