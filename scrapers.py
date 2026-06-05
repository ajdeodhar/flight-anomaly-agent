import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random

DEBUG = True

def log_debug(msg):
    """Print debug message with timestamp."""
    if DEBUG:
        print(f"[DEBUG] {msg}")

def fetch_skyscanner_economy(origin="DEL", destination="JFK"):
    """
    Fetch economy price from Skyscanner for the given route.
    Returns price in INR or None if fetch fails.
    """
    log_debug(f"Attempting Skyscanner economy fetch for {origin}-{destination}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://www.skyscanner.co.in/transport/flights/{origin}/{destination}/?adults=1&children=0&infants=0&cabinclass=economy&rtn=0&prefOutbound=nextmonth"
        
        log_debug(f"URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        log_debug(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        log_debug(f"Parsed HTML, page size: {len(response.content)} bytes")
        
        price_text = None
        for script in soup.find_all('script', type='application/json'):
            if 'price' in script.string.lower():
                price_text = script.string
                log_debug("Found price in JSON script tag")
                break
        
        if not price_text:
            for price_elem in soup.find_all(class_='price'):
                price_text = price_elem.get_text()
                log_debug("Found price in HTML element with class 'price'")
                break
        
        if price_text:
            price_str = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
            log_debug(f"Extracted price string: {price_str}")
            if price_str:
                price = float(price_str)
                log_debug(f"Successfully parsed economy price: ₹{price}")
                return price
        
        log_debug("No price text found in Skyscanner response")
        return None
        
    except requests.exceptions.Timeout:
        log_debug("Skyscanner request timed out (10s)")
        return None
    except requests.exceptions.ConnectionError:
        log_debug("Skyscanner connection error - site may be blocked or offline")
        return None
    except Exception as e:
        log_debug(f"Skyscanner error: {type(e).__name__}: {str(e)[:100]}")
        return None

def fetch_airfrance_premium_economy(origin="DEL", destination="JFK"):
    """
    Fetch premium economy price from Air France website (primary).
    Returns price in INR or None if fetch fails.
    """
    log_debug(f"Attempting Air France premium economy fetch for {origin}-{destination}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = "https://www.airfrance.co.in"
        
        log_debug(f"URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        log_debug(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        log_debug(f"Parsed HTML, page size: {len(response.content)} bytes")
        
        price_text = None
        for script in soup.find_all('script', type='application/json'):
            if 'price' in script.string.lower() or 'premium' in script.string.lower():
                price_text = script.string
                log_debug("Found price/premium in JSON script tag")
                break
        
        if not price_text:
            for price_elem in soup.find_all(class_='price'):
                price_text = price_elem.get_text()
                if 'premium' in price_text.lower():
                    log_debug("Found premium price in HTML element")
                    break
        
        if price_text:
            price_str = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
            log_debug(f"Extracted price string: {price_str}")
            if price_str:
                price = float(price_str)
                log_debug(f"Successfully parsed Air France premium price: ₹{price}")
                return price
        
        log_debug("No premium price found in Air France response")
        return None
        
    except requests.exceptions.Timeout:
        log_debug("Air France request timed out (10s)")
        return None
    except requests.exceptions.ConnectionError:
        log_debug("Air France connection error - site may be blocked or offline")
        return None
    except Exception as e:
        log_debug(f"Air France error: {type(e).__name__}: {str(e)[:100]}")
        return None

def fetch_kayak_premium_economy(origin="DEL", destination="JFK"):
    """
    Fetch premium economy price from Kayak (fallback to Air France).
    Returns price in INR or None if fetch fails.
    """
    log_debug(f"Attempting Kayak premium economy fetch for {origin}-{destination} (FALLBACK)")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"https://www.kayak.co.in/flights/{origin}-{destination}?fs=cabin=p"
        
        log_debug(f"URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        log_debug(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        log_debug(f"Parsed HTML, page size: {len(response.content)} bytes")
        
        price_text = None
        for price_elem in soup.find_all(class_='price'):
            price_text = price_elem.get_text()
            log_debug("Found price in Kayak HTML element")
            break
        
        if not price_text:
            for span in soup.find_all('span'):
                text = span.get_text()
                if '₹' in text or 'Rs' in text:
                    price_text = text
                    log_debug("Found rupee symbol in Kayak span")
                    break
        
        if price_text:
            price_str = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
            log_debug(f"Extracted price string: {price_str}")
            if price_str:
                price = float(price_str)
                log_debug(f"Successfully parsed Kayak premium price: ₹{price}")
                return price
        
        log_debug("No premium price found in Kayak response")
        return None
        
    except requests.exceptions.Timeout:
        log_debug("Kayak request timed out (10s)")
        return None
    except requests.exceptions.ConnectionError:
        log_debug("Kayak connection error - site may be blocked or offline")
        return None
    except Exception as e:
        log_debug(f"Kayak error: {type(e).__name__}: {str(e)[:100]}")
        return None

def fetch_premium_with_fallback(origin="DEL", destination="JFK"):
    """
    Try to fetch premium economy price.
    Primary: Air France direct
    Fallback: Kayak
    Returns price in INR or None if all sources fail.
    """
    log_debug("=== PREMIUM ECONOMY FETCH STRATEGY ===")
    
    # Try Air France first
    price = fetch_airfrance_premium_economy(origin, destination)
    if price is not None:
        log_debug("SUCCESS: Got price from Air France (primary source)")
        return price
    
    log_debug("Air France failed, trying Kayak fallback...")
    time.sleep(random.uniform(1, 2))
    
    # Try Kayak as fallback
    price = fetch_kayak_premium_economy(origin, destination)
    if price is not None:
        log_debug("SUCCESS: Got price from Kayak (fallback source)")
        return price
    
    log_debug("FAILURE: All premium sources exhausted")
    return None

def fetch_both_prices(origin="DEL", destination="JFK"):
    """
    Fetch both economy and premium economy prices.
    Returns tuple (economy_price, premium_price) or (None, None) if either fails.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===== FETCHING PRICES FOR {origin}-{destination} =====")
    
    log_debug("Starting dual fetch: economy from Skyscanner, premium from Air France/Kayak")
    
    economy = fetch_skyscanner_economy(origin, destination)
    time.sleep(random.uniform(1, 2))
    
    premium = fetch_premium_with_fallback(origin, destination)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetch complete: Economy={economy}, Premium={premium}")
    
    return economy, premium

def validate_prices(economy, premium):
    """Check if both prices are valid numbers."""
    log_debug(f"Validating prices: Economy={economy}, Premium={premium}")
    
    if economy is None or premium is None:
        log_debug("INVALID: One or both prices are None")
        return False
    if economy <= 0 or premium <= 0:
        log_debug(f"INVALID: Negative or zero prices")
        return False
    
    log_debug("VALID: Both prices are positive numbers")
    return True
