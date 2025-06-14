import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from tqdm import tqdm
import os
import glob
import tweepy
import re
import nltk
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer

# FRED API key
FRED_API_KEY = "e8470914c1a9364070f4b054b16ceb81"  # FRED API key

# Download NLTK resources
nltk.download('stopwords')
nltk.download('vader_lexicon')
stop_words = set(stopwords.words('english'))
sia = SentimentIntensityAnalyzer()

# Twitter API credentials (replace with your own)
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAABbt2QEAAAAAUlWnaVpd0OGbmrqVUDbTFt7J9Ww%3DELB2cRzAgfZg5CSIaRa84ER9ToDC7QPxE4EPVIVb7RdZ8QZEcZ"

# Authenticate with Tweepy (v2 client)
client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)

def fetch_worldbank_indicators():
    """
    Fetch key macroeconomic indicators from World Bank API
    """
    # World Bank API base URL
    base_url = "http://api.worldbank.org/v2/country/US/indicator/"
    
    # Key indicators to fetch
    indicators = {
        'NY.GDP.MKTP.KD.ZG': 'GDP_Growth',  # GDP growth (annual %)
        'FP.CPI.TOTL.ZG': 'Inflation',      # Inflation, consumer prices (annual %)
        'FR.INR.RINR': 'Interest_Rate',     # Real interest rate (%)
        'NE.EXP.GNFS.ZS': 'Exports_GDP',    # Exports of goods and services (% of GDP)
        'NE.IMP.GNFS.ZS': 'Imports_GDP',    # Imports of goods and services (% of GDP)
        'NY.GNS.ICTR.ZS': 'Gross_Savings',  # Gross savings (% of GDP)
        'SL.UEM.TOTL.ZS': 'Unemployment'    # Unemployment, total (% of total labor force)
    }
    
    end_date = datetime.now().year
    start_date = end_date - 5
    
    all_data = []
    
    print("Fetching World Bank indicators...")
    for indicator_code, indicator_name in tqdm(indicators.items()):
        url = f"{base_url}{indicator_code}?format=json&date={start_date}:{end_date}&per_page=100"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if len(data) > 1 and 'data' in data[1]:
                for item in data[1]['data']:
                    if item['value'] is not None:
                        all_data.append({
                            'Date': f"{item['date']}-12-31",  # Using year-end date
                            'Indicator': indicator_name,
                            'Value': item['value']
                        })
        except Exception as e:
            print(f"\nError fetching {indicator_name}: {str(e)}")
            continue
    
    # Convert to DataFrame and pivot
    df = pd.DataFrame(all_data)
    if not df.empty:
        df = df.pivot(index='Date', columns='Indicator', values='Value')
        df.index = pd.to_datetime(df.index)
        return df
    return pd.DataFrame()

def fetch_fred_indicators():
    """
    Fetch key indicators from FRED (Federal Reserve Economic Data)
    """
    # FRED API base URL
    base_url = "https://api.stlouisfed.org/fred/series/observations"
    
    # Key indicators to fetch
    indicators = {
        'GDP': 'GDP_Current',           # GDP
        'CPIAUCSL': 'Inflation_CPI',    # Consumer Price Index
        'UNRATE': 'Unemployment_Rate',  # Unemployment Rate
        'FEDFUNDS': 'Fed_Funds_Rate',   # Federal Funds Rate
        'M2': 'Money_Supply'            # Money Supply
    }
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    all_data = []
    
    print("\nFetching FRED indicators...")
    for indicator_code, indicator_name in tqdm(indicators.items()):
        url = f"{base_url}?series_id={indicator_code}&api_key={FRED_API_KEY}&file_type=json&observation_start={start_date}&observation_end={end_date}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if 'observations' in data:
                for obs in data['observations']:
                    if obs['value'] != '.':
                        all_data.append({
                            'Date': obs['date'],
                            'Indicator': indicator_name,
                            'Value': float(obs['value'])
                        })
        except Exception as e:
            print(f"\nError fetching {indicator_name}: {str(e)}")
            continue
    
    # Convert to DataFrame and pivot
    df = pd.DataFrame(all_data)
    if not df.empty:
        df = df.pivot(index='Date', columns='Indicator', values='Value')
        df.index = pd.to_datetime(df.index)
        return df
    return pd.DataFrame()

def merge_macro_with_stocks():
    """
    Merge macroeconomic indicators with stock data
    """
    # Create output directory if it doesn't exist
    os.makedirs('data/processed', exist_ok=True)
    
    # Fetch macroeconomic indicators
    wb_data = fetch_worldbank_indicators()
    fred_data = fetch_fred_indicators()
    
    # Merge World Bank and FRED data
    macro_data = pd.concat([wb_data, fred_data], axis=1)
    
    # Ensure macro data index is datetime with UTC timezone
    macro_data.index = pd.to_datetime(macro_data.index, utc=True)
    
    # Get list of stock data files
    stock_files = glob.glob('data/raw/*_historical_data.csv')
    
    print("\nMerging macroeconomic indicators with stock data...")
    for stock_file in tqdm(stock_files):
        try:
            # Read stock data
            stock_data = pd.read_csv(stock_file)
            
            # Convert Date column to datetime with UTC timezone
            stock_data['Date'] = pd.to_datetime(stock_data['Date'], utc=True)
            
            # Merge with macro data
            merged_data = pd.merge_asof(
                stock_data.sort_values('Date'),
                macro_data.sort_index(),
                left_on='Date',
                right_index=True,
                direction='backward'
            )
            
            # Convert Date back to naive datetime for saving
            merged_data['Date'] = merged_data['Date'].dt.tz_localize(None)
            
            # Save merged data
            output_file = stock_file.replace('raw', 'processed')
            merged_data.to_csv(output_file, index=False)
            
        except Exception as e:
            print(f"\nError processing {stock_file}: {str(e)}")
            continue
    
    print("\nData merging completed!")
    print("Merged files have been saved in the 'data/processed' directory")

def clean_tweet(text):
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#','', text)
    text = re.sub(r'[^A-Za-z\s]', '', text)
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text

def get_sentiment(text):
    score = sia.polarity_scores(text)
    if score['compound'] >= 0.05:
        return 'positive'
    elif score['compound'] <= -0.05:
        return 'negative'
    else:
        return 'neutral'

def fetch_tweets():
    """
    Fetch tweets about S&P 500 stocks for the last 5 years
    """
    # List of S&P 500 stock tickers (example subset, use full list as needed)
    sp500_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

    # Date range: last 5 years
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=5*365)

    all_tweets = []

    for ticker in tqdm(sp500_tickers, desc='Tickers'):
        query = f'${ticker} -is:retweet lang:en'
        # Twitter Academic Research endpoint: search_all_tweets
        try:
            tweets = tweepy.Paginator(
                client.search_all_tweets,
                query=query,
                start_time=start_time.isoformat("T") + "Z",
                end_time=end_time.isoformat("T") + "Z",
                tweet_fields=['created_at', 'text', 'author_id'],
                max_results=100
            ).flatten(limit=1000)  # Adjust limit as needed (API rate limits apply)

            for tweet in tweets:
                cleaned = clean_tweet(tweet.text)
                sentiment = get_sentiment(cleaned)
                all_tweets.append({
                    'ticker': ticker,
                    'created_at': tweet.created_at,
                    'text': tweet.text,
                    'cleaned_text': cleaned,
                    'sentiment': sentiment,
                    'author_id': tweet.author_id
                })
        except Exception as e:
            print(f"Error fetching tweets for {ticker}: {e}")

    # Convert to DataFrame
    df = pd.DataFrame(all_tweets)
    print(df.head())

    # Save to CSV
    df.to_csv('sp500_tweets_sentiment_5years.csv', index=False)

if __name__ == "__main__":
    merge_macro_with_stocks()
    fetch_tweets() 