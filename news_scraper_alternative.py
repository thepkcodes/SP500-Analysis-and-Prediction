import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import re
import json

def get_top_50_sp500_tickers():
    """
    Return a predefined list of top 50 S&P 500 companies by market cap
    """
    top_50 = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'UNH', 'JNJ',
        'JPM', 'V', 'PG', 'HD', 'MA', 'BAC', 'ABBV', 'PFE', 'KO', 'AVGO',
        'PEP', 'TMO', 'COST', 'MRK', 'WMT', 'ABT', 'ACN', 'VZ', 'CRM', 'LLY',
        'DHR', 'NEE', 'TXN', 'NKE', 'PM', 'RTX', 'HON', 'QCOM', 'LOW', 'UNP',
        'IBM', 'CAT', 'GS', 'AMGN', 'SPGI', 'AXP', 'GE', 'MS', 'ISRG', 'PLD'
    ]
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
    Parse various date formats
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

def scrape_from_marketwatch(ticker, max_articles=20):
    """
    Scrape news from MarketWatch
    """
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    articles = []
    
    try:
        # MarketWatch news URL
        url = f'https://www.marketwatch.com/investing/stock/{ticker}'
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
                for link in links[:max_articles]:
                    headline = link.get_text(strip=True)
                    
                    if headline and len(headline) > 10:
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
                                'Date': parsed_date.strftime('%Y-%m-%d'),
                                'Source': 'MarketWatch'
                            })
                        elif not parsed_date:
                            articles.append({
                                'Ticker': ticker,
                                'Headline': headline,
                                'Date': 'Recent',
                                'Source': 'MarketWatch'
                            })
                break
        
        return articles
        
    except Exception as e:
        print(f"Error scraping MarketWatch for {ticker}: {str(e)}")
        return []

def scrape_from_seeking_alpha(ticker, max_articles=20):
    """
    Scrape news from Seeking Alpha
    """
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    articles = []
    
    try:
        # Seeking Alpha news URL
        url = f'https://seekingalpha.com/symbol/{ticker}/news'
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
                for link in links[:max_articles]:
                    headline = link.get_text(strip=True)
                    
                    if headline and len(headline) > 10:
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
                                'Date': parsed_date.strftime('%Y-%m-%d'),
                                'Source': 'Seeking Alpha'
                            })
                        elif not parsed_date:
                            articles.append({
                                'Ticker': ticker,
                                'Headline': headline,
                                'Date': 'Recent',
                                'Source': 'Seeking Alpha'
                            })
                break
        
        return articles
        
    except Exception as e:
        print(f"Error scraping Seeking Alpha for {ticker}: {str(e)}")
        return []

def scrape_company_news(ticker, max_articles=30):
    """
    Scrape news from multiple sources for a company
    """
    all_articles = []
    
    # Try MarketWatch
    print(f"  Trying MarketWatch...")
    mw_articles = scrape_from_marketwatch(ticker, max_articles//2)
    all_articles.extend(mw_articles)
    print(f"    Found {len(mw_articles)} articles from MarketWatch")
    
    # Try Seeking Alpha
    print(f"  Trying Seeking Alpha...")
    sa_articles = scrape_from_seeking_alpha(ticker, max_articles//2)
    all_articles.extend(sa_articles)
    print(f"    Found {len(sa_articles)} articles from Seeking Alpha")
    
    return all_articles

def scrape_all_companies():
    """
    Scrape news for all top 50 companies
    """
    tickers = get_top_50_sp500_tickers()
    all_news = []
    
    print(f"Scraping news for {len(tickers)} companies...")
    print("This will take some time due to rate limiting...")
    
    for i, ticker in enumerate(tickers):
        print(f"\nScraping {ticker} ({i+1}/{len(tickers)})")
        
        articles = scrape_company_news(ticker)
        all_news.extend(articles)
        
        print(f"Total found for {ticker}: {len(articles)} articles")
        
        # Random delay between requests
        delay = random.uniform(3, 6)
        time.sleep(delay)
        
        # Longer break every 10 requests
        if (i + 1) % 10 == 0:
            print(f"Taking a longer break after {i+1} requests...")
            time.sleep(random.uniform(15, 20))
    
    return all_news

def save_to_csv(news_data, filename='financial_news_headlines.csv'):
    """
    Save news data to CSV
    """
    if not news_data:
        print("No news data to save!")
        return
    
    df = pd.DataFrame(news_data)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['Ticker', 'Headline'])
    
    # Separate articles with dates from recent ones
    df_with_dates = df[df['Date'] != 'Recent'].copy()
    df_recent = df[df['Date'] == 'Recent'].copy()
    
    if not df_with_dates.empty:
        # Sort by date
        df_with_dates['Date'] = pd.to_datetime(df_with_dates['Date'])
        df_with_dates = df_with_dates.sort_values('Date', ascending=False)
        
        # Combine with recent articles
        final_df = pd.concat([df_with_dates, df_recent], ignore_index=True)
    else:
        final_df = df_recent
    
    # Save to CSV
    final_df.to_csv(filename, index=False)
    
    print(f"\nNews data saved to {filename}")
    print(f"Total articles: {len(final_df)}")
    
    if not df_with_dates.empty:
        print(f"Articles with dates: {len(df_with_dates)}")
        print(f"Date range: {df_with_dates['Date'].min().strftime('%Y-%m-%d')} to {df_with_dates['Date'].max().strftime('%Y-%m-%d')}")
    
    print(f"Recent articles (no date): {len(df_recent)}")
    
    # Show summary by ticker
    print("\nArticles per ticker:")
    ticker_counts = final_df['Ticker'].value_counts()
    for ticker, count in ticker_counts.head(10).items():
        print(f"{ticker}: {count} articles")
    
    # Show summary by source
    print("\nArticles per source:")
    source_counts = final_df['Source'].value_counts()
    for source, count in source_counts.items():
        print(f"{source}: {count} articles")

def main():
    """
    Main function
    """
    print("Financial News Scraper - Alternative Sources")
    print("=" * 50)
    
    # Scrape news for all companies
    all_news = scrape_all_companies()
    
    # Save to CSV
    save_to_csv(all_news)
    
    print("\nNews scraping completed!")

if __name__ == "__main__":
    main() 