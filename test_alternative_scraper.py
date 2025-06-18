import requests
from bs4 import BeautifulSoup
import time
import random

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

def test_marketwatch():
    """
    Test MarketWatch scraping
    """
    print("Testing MarketWatch...")
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        url = 'https://www.marketwatch.com/investing/stock/AAPL'
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for news headlines
        news_selectors = [
            'h3 a[href*="/story/"]',
            'div[class*="article"] h3 a',
            'a[href*="/story/"]',
            'h3 a[href*="/news/"]'
        ]
        
        for selector in news_selectors:
            links = soup.select(selector)
            if links:
                print(f"Found {len(links)} articles with selector: {selector}")
                
                # Show first few headlines
                for i, link in enumerate(links[:3]):
                    headline = link.get_text(strip=True)
                    if headline and len(headline) > 10:
                        print(f"  {i+1}. {headline[:80]}...")
                break
        else:
            print("No articles found on MarketWatch")
            
    except Exception as e:
        print(f"Error testing MarketWatch: {str(e)}")

def test_seeking_alpha():
    """
    Test Seeking Alpha scraping
    """
    print("\nTesting Seeking Alpha...")
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        url = 'https://seekingalpha.com/symbol/AAPL/news'
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for news headlines
        news_selectors = [
            'a[data-test-id="post-list-item-title"]',
            'h3 a[href*="/news/"]',
            'div[class*="article"] h3 a',
            'a[href*="/news/"]'
        ]
        
        for selector in news_selectors:
            links = soup.select(selector)
            if links:
                print(f"Found {len(links)} articles with selector: {selector}")
                
                # Show first few headlines
                for i, link in enumerate(links[:3]):
                    headline = link.get_text(strip=True)
                    if headline and len(headline) > 10:
                        print(f"  {i+1}. {headline[:80]}...")
                break
        else:
            print("No articles found on Seeking Alpha")
            
    except Exception as e:
        print(f"Error testing Seeking Alpha: {str(e)}")

if __name__ == "__main__":
    print("Testing Alternative News Sources")
    print("=" * 35)
    test_marketwatch()
    test_seeking_alpha() 