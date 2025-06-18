import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
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

def test_yahoo_finance_scraping():
    """
    Test scraping with a few popular tickers
    """
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        
        # Try main page
        main_url = f'https://finance.yahoo.com/quote/{ticker}'
        try:
            response = requests.get(main_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for news headlines
            news_selectors = [
                'h3[class*="Mb"] a',
                'a[data-test-id="news-headline"]',
                'h3 a[href*="/news/"]',
                'div[data-test-id="news-item"] h3 a',
                'li[class*="news-item"] h3 a',
                'div[class*="news"] h3 a',
                'a[href*="/news/"]'
            ]
            
            articles_found = 0
            for selector in news_selectors:
                article_links = soup.select(selector)
                if article_links:
                    print(f"Found {len(article_links)} articles with selector: {selector}")
                    articles_found = len(article_links)
                    
                    # Show first few headlines
                    for i, link in enumerate(article_links[:3]):
                        headline = link.get_text(strip=True)
                        print(f"  {i+1}. {headline[:100]}...")
                    break
            
            if articles_found == 0:
                print("No articles found on main page, trying news tab...")
                
                # Try news tab
                news_url = f'https://finance.yahoo.com/quote/{ticker}/news'
                news_response = requests.get(news_url, headers=headers, timeout=30)
                news_response.raise_for_status()
                
                news_soup = BeautifulSoup(news_response.content, 'html.parser')
                
                for selector in news_selectors:
                    article_links = news_soup.select(selector)
                    if article_links:
                        print(f"Found {len(article_links)} articles on news tab with selector: {selector}")
                        articles_found = len(article_links)
                        
                        # Show first few headlines
                        for i, link in enumerate(article_links[:3]):
                            headline = link.get_text(strip=True)
                            print(f"  {i+1}. {headline[:100]}...")
                        break
                
                if articles_found == 0:
                    print("No articles found on news tab either")
            
            time.sleep(2)  # Be nice to the server
            
        except Exception as e:
            print(f"Error testing {ticker}: {str(e)}")

if __name__ == "__main__":
    print("Testing Yahoo Finance News Scraper")
    print("=" * 40)
    test_yahoo_finance_scraping() 