import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from tqdm import tqdm
import re
import random
import json

def get_top_50_sp500():
    """
    Get the top 50 companies from S&P 500 by market cap
    Returns a list of ticker symbols
    """
    print("Fetching S&P 500 companies list...")
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    
    # Get market cap data for each company
    tickers = sp500['Symbol'].tolist()
    market_caps = []
    
    print("Getting market cap information for companies...")
    for ticker in tqdm(tickers):
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            if 'marketCap' in info:
                market_caps.append((ticker, info['marketCap']))
            time.sleep(0.1)  # Avoid rate limiting
        except Exception as e:
            print(f"\nError getting market cap for {ticker}: {str(e)}")
            continue
    
    # Sort by market cap and get top 50
    market_caps.sort(key=lambda x: x[1], reverse=True)
    top_50 = [ticker for ticker, _ in market_caps[:50]]
    
    print(f"\nSuccessfully identified top 50 companies by market cap")
    return top_50

def get_random_user_agent():
    """
    Return a random user agent to avoid detection
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    return random.choice(user_agents)

def parse_date(date_str):
    """
    Parse various date formats from Yahoo Finance
    """
    try:
        # Handle different date formats
        if 'ago' in date_str.lower():
            # Handle relative dates like "2 hours ago", "3 days ago"
            number = int(re.findall(r'\d+', date_str)[0])
            if 'hour' in date_str.lower():
                return datetime.now() - timedelta(hours=number)
            elif 'day' in date_str.lower():
                return datetime.now() - timedelta(days=number)
            elif 'week' in date_str.lower():
                return datetime.now() - timedelta(weeks=number)
            elif 'month' in date_str.lower():
                return datetime.now() - timedelta(days=number*30)
            elif 'year' in date_str.lower():
                return datetime.now() - timedelta(days=number*365)
        else:
            # Try to parse absolute dates
            for fmt in ['%b %d, %Y', '%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
    except:
        pass
    
    # Return None if parsing fails
    return None

def scrape_yahoo_finance_news(ticker, max_articles=50):
    """
    Scrape news headlines from Yahoo Finance for a given ticker
    """
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    articles = []
    
    try:
        # Try multiple approaches to get news
        
        # Approach 1: Main quote page
        main_url = f'https://finance.yahoo.com/quote/{ticker}'
        response = requests.get(main_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for news sections with more specific selectors
        news_selectors = [
            'div[data-test-id="news-item"] h3 a',
            'div[class*="news"] h3 a',
            'div[class*="News"] h3 a',
            'li[class*="news-item"] h3 a',
            'div[class*="story"] h3 a',
            'div[class*="article"] h3 a',
            'h3 a[href*="/news/"]',
            'a[data-test-id="news-headline"]'
        ]
        
        for selector in news_selectors:
            article_links = soup.select(selector)
            if article_links:
                for link in article_links[:max_articles//2]:
                    headline = link.get_text(strip=True)
                    if headline and len(headline) > 10 and not headline.startswith('Today\'s news'):
                        # Try to find date
                        date_str = None
                        parent = link.parent
                        for _ in range(3):
                            if parent:
                                date_elements = parent.find_all(text=re.compile(r'\d{1,2}:\d{2}|ago|yesterday|today|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'))
                                if date_elements:
                                    date_str = date_elements[0].strip()
                                    break
                                parent = parent.parent
                            else:
                                break
                        
                        parsed_date = parse_date(date_str) if date_str else None
                        
                        if parsed_date and 2019 <= parsed_date.year <= 2024:
                            articles.append({
                                'Ticker': ticker,
                                'Headline': headline,
                                'Date': parsed_date.strftime('%Y-%m-%d')
                            })
                break
        
        # Approach 2: News tab
        if len(articles) < max_articles//2:
            news_url = f'https://finance.yahoo.com/quote/{ticker}/news'
            news_response = requests.get(news_url, headers=headers, timeout=30)
            news_response.raise_for_status()
            
            news_soup = BeautifulSoup(news_response.content, 'html.parser')
            
            for selector in news_selectors:
                article_links = news_soup.select(selector)
                if article_links:
                    for link in article_links[:max_articles//2]:
                        headline = link.get_text(strip=True)
                        if headline and len(headline) > 10 and not headline.startswith('Today\'s news'):
                            # Try to find date
                            date_str = None
                            parent = link.parent
                            for _ in range(3):
                                if parent:
                                    date_elements = parent.find_all(text=re.compile(r'\d{1,2}:\d{2}|ago|yesterday|today|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'))
                                    if date_elements:
                                        date_str = date_elements[0].strip()
                                        break
                                    parent = parent.parent
                                else:
                                    break
                            
                            parsed_date = parse_date(date_str) if date_str else None
                            
                            if parsed_date and 2019 <= parsed_date.year <= 2024:
                                articles.append({
                                    'Ticker': ticker,
                                    'Headline': headline,
                                    'Date': parsed_date.strftime('%Y-%m-%d')
                                })
                    break
        
        # Approach 3: Search for company-specific news
        if len(articles) < 5:  # If we found very few articles, try a broader search
            # Look for any text that might be news headlines
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if (len(line) > 20 and len(line) < 200 and 
                    any(word in line.lower() for word in ['earnings', 'revenue', 'profit', 'stock', 'shares', 'market', 'business', 'company'])):
                    
                    # This might be a news headline
                    articles.append({
                        'Ticker': ticker,
                        'Headline': line,
                        'Date': 'Unknown'
                    })
                    
                    if len(articles) >= max_articles:
                        break
        
        return articles
        
    except Exception as e:
        print(f"\nError scraping news for {ticker}: {str(e)}")
        return []

def scrape_all_news(tickers):
    """
    Scrape news for all tickers and save to CSV
    """
    all_news = []
    
    print(f"\nScraping news headlines for {len(tickers)} companies...")
    print("This may take a while due to rate limiting...")
    
    for i, ticker in enumerate(tqdm(tickers)):
        print(f"\nScraping news for {ticker} ({i+1}/{len(tickers)})")
        
        articles = scrape_yahoo_finance_news(ticker)
        all_news.extend(articles)
        
        print(f"Found {len(articles)} articles for {ticker}")
        
        # Random delay between requests to avoid being blocked
        delay = random.uniform(2, 5)
        time.sleep(delay)
        
        # Additional delay every 10 requests
        if (i + 1) % 10 == 0:
            print(f"Taking a longer break after {i+1} requests...")
            time.sleep(random.uniform(10, 15))
    
    return all_news

def save_news_to_csv(news_data, filename='yahoo_finance_headlines.csv'):
    """
    Save news data to CSV file
    """
    if not news_data:
        print("No news data to save!")
        return
    
    df = pd.DataFrame(news_data)
    
    # Remove duplicates based on headline and ticker
    df = df.drop_duplicates(subset=['Ticker', 'Headline'])
    
    # Filter out articles with unknown dates for final dataset
    df_with_dates = df[df['Date'] != 'Unknown'].copy()
    
    if not df_with_dates.empty:
        # Sort by date (newest first)
        df_with_dates['Date'] = pd.to_datetime(df_with_dates['Date'])
        df_with_dates = df_with_dates.sort_values('Date', ascending=False)
        
        # Save to CSV
        df_with_dates.to_csv(filename, index=False)
        
        print(f"\nNews data saved to {filename}")
        print(f"Total articles with dates: {len(df_with_dates)}")
        print(f"Date range: {df_with_dates['Date'].min().strftime('%Y-%m-%d')} to {df_with_dates['Date'].max().strftime('%Y-%m-%d')}")
        
        # Show summary by ticker
        print("\nArticles per ticker:")
        ticker_counts = df_with_dates['Ticker'].value_counts()
        for ticker, count in ticker_counts.head(10).items():
            print(f"{ticker}: {count} articles")
    else:
        print("No articles with valid dates found!")
        
        # Save all articles including those without dates
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} articles (including those without dates) to {filename}")

def main():
    """
    Main function to orchestrate the news scraping process
    """
    print("Yahoo Finance News Scraper")
    print("=" * 50)
    
    # Get top 50 companies
    top_50 = get_top_50_sp500()
    
    # Scrape news for all companies
    all_news = scrape_all_news(top_50)
    
    # Save to CSV
    save_news_to_csv(all_news)
    
    print("\nNews scraping completed!")

if __name__ == "__main__":
    main() 