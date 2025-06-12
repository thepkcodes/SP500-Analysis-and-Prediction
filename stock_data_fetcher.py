import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from tqdm import tqdm

def get_top_50_sp500():
    """
    Get the top 50 companies from S&P 500 by market cap
    Returns a list of ticker symbols and their market caps
    """
    print("Fetching S&P 500 companies list...")
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    
    # Get market cap data for each company
    tickers = sp500['Symbol'].tolist()
    market_caps = []
    
    print("Getting market cap information for companies...")
    for ticker in tqdm(tickers):
        try:
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

def fetch_and_save_historical_data(tickers, years=5):
    """
    Fetch historical data for given tickers and save individual CSV files
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    # Create data/raw directory if it doesn't exist
    os.makedirs('data/raw', exist_ok=True)
    
    successful_downloads = 0
    failed_downloads = []
    
    print(f"\nFetching {years} years of historical data for each company...")
    for ticker in tqdm(tickers):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if not hist.empty:
                # Reset index to make Date a column
                hist = hist.reset_index()
                
                # Add company name and sector information
                try:
                    info = stock.info
                    hist['Company_Name'] = info.get('longName', ticker)
                    hist['Sector'] = info.get('sector', 'Unknown')
                except:
                    hist['Company_Name'] = ticker
                    hist['Sector'] = 'Unknown'
                
                # Save to CSV
                filename = f'data/raw/{ticker}_historical_data.csv'
                hist.to_csv(filename, index=False)
                successful_downloads += 1
            
            time.sleep(0.1)  # Avoid rate limiting
        except Exception as e:
            print(f"\nError fetching data for {ticker}: {str(e)}")
            failed_downloads.append(ticker)
            continue
    
    # Print summary
    print("\nData Collection Summary:")
    print(f"Successfully downloaded data for {successful_downloads} companies")
    if failed_downloads:
        print(f"Failed to download data for {len(failed_downloads)} companies:")
        for ticker in failed_downloads:
            print(f"- {ticker}")

def main():
    # Get top 50 companies
    top_50 = get_top_50_sp500()
    
    # Fetch and save historical data
    fetch_and_save_historical_data(top_50)
    
    print("\nData collection completed!")
    print(f"CSV files have been saved in the 'data/raw' directory")

if __name__ == "__main__":
    main() 