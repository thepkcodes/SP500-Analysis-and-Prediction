import requests
from bs4 import BeautifulSoup
import time
import random
import re

def get_random_user_agent():
    """
    Return a random user agent to avoid detection
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    ]
    return random.choice(user_agents)

def test_simple_scraper():
    """
    Test the simple scraper with a few companies
    """
    test_tickers = ['AAPL', 'MSFT', 'TSLA']
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        
        try:
            # Try main page
            url = f'https://finance.yahoo.com/quote/{ticker}'
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for news headlines
            news_selectors = [
                'h3 a[href*="/news/"]',
                'div[data-test-id="news-item"] h3 a',
                'div[class*="news"] h3 a',
                'li[class*="news-item"] h3 a',
                'a[data-test-id="news-headline"]'
            ]
            
            articles_found = 0
            for selector in news_selectors:
                links = soup.select(selector)
                if links:
                    print(f"Found {len(links)} potential articles with selector: {selector}")
                    
                    # Show first few headlines
                    for i, link in enumerate(links[:5]):
                        headline = link.get_text(strip=True)
                        if headline and len(headline) > 10:
                            print(f"  {i+1}. {headline[:80]}...")
                            articles_found += 1
                    break
            
            if articles_found == 0:
                print("No articles found on main page")
            
            time.sleep(2)  # Be nice to the server
            
        except Exception as e:
            print(f"Error testing {ticker}: {str(e)}")

if __name__ == "__main__":
    print("Testing Simple Yahoo Finance News Scraper")
    print("=" * 45)
    test_simple_scraper() 