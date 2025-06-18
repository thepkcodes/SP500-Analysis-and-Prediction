import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def load_finbert_model():
    """
    Load the FinBERT model and tokenizer for sentiment analysis
    """
    print("Loading FinBERT model...")
    model_name = "yiyanghkust/finbert-tone"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # Move model to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    
    print(f"Model loaded on {device}")
    return tokenizer, model, device

def analyze_sentiment_batch(headlines, tokenizer, model, device, batch_size=32):
    """
    Analyze sentiment for a batch of headlines
    """
    sentiment_scores = []
    
    # Process headlines in batches
    for i in range(0, len(headlines), batch_size):
        batch_headlines = headlines[i:i + batch_size]
        
        # Tokenize the batch
        inputs = tokenizer(
            batch_headlines,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Move inputs to device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Get predictions
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.softmax(outputs.logits, dim=1)
        
        # Convert predictions to sentiment scores
        # FinBERT labels: ['negative', 'neutral', 'positive']
        # Map to: -1, 0, 1
        for pred in predictions:
            # Get the predicted class
            predicted_class = torch.argmax(pred).item()
            
            # Map class to sentiment score
            if predicted_class == 0:  # negative
                sentiment_scores.append(-1)
            elif predicted_class == 1:  # neutral
                sentiment_scores.append(0)
            else:  # positive
                sentiment_scores.append(1)
    
    return sentiment_scores

def process_headlines_sentiment(csv_file='gdelt_headlines.csv'):
    """
    Process headlines and analyze sentiment
    """
    print("Loading headlines data...")
    
    # Load the CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} headlines")
    except FileNotFoundError:
        print(f"Error: {csv_file} not found!")
        return None
    
    # Check required columns
    if 'date' not in df.columns or 'headline' not in df.columns:
        print("Error: CSV must contain 'date' and 'headline' columns!")
        return None
    
    # Clean the data
    print("Cleaning data...")
    
    # Remove rows with missing or blank headlines
    initial_count = len(df)
    df = df.dropna(subset=['headline'])
    df = df[df['headline'].str.strip() != '']
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter date range (2020-06-15 to 2025-06-11)
    start_date = pd.to_datetime('2020-06-15')
    end_date = pd.to_datetime('2025-06-11')
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    print(f"After cleaning: {len(df)} headlines (removed {initial_count - len(df)} invalid entries)")
    
    if len(df) == 0:
        print("No valid headlines found!")
        return None
    
    # Load FinBERT model
    tokenizer, model, device = load_finbert_model()
    
    # Analyze sentiment
    print("Analyzing sentiment...")
    headlines_list = df['headline'].tolist()
    
    sentiment_scores = analyze_sentiment_batch(
        headlines_list, 
        tokenizer, 
        model, 
        device, 
        batch_size=32
    )
    
    # Add sentiment scores to dataframe
    df['sentiment_score'] = sentiment_scores
    
    # Aggregate by date
    print("Aggregating daily sentiment...")
    daily_sentiment = df.groupby('date')['sentiment_score'].agg([
        'mean',  # Average sentiment
        'count',  # Number of headlines
        'std'     # Standard deviation
    ]).reset_index()
    
    # Rename columns
    daily_sentiment.columns = ['date', 'avg_sentiment', 'headline_count', 'sentiment_std']
    
    # Fill NaN values with 0 for days with no headlines
    daily_sentiment['avg_sentiment'] = daily_sentiment['avg_sentiment'].fillna(0)
    daily_sentiment['headline_count'] = daily_sentiment['headline_count'].fillna(0)
    daily_sentiment['sentiment_std'] = daily_sentiment['sentiment_std'].fillna(0)
    
    # Sort by date
    daily_sentiment = daily_sentiment.sort_values('date')
    
    return daily_sentiment, df

def save_results(daily_sentiment, output_file='daily_sentiment.csv'):
    """
    Save the results to CSV file
    """
    print(f"Saving results to {output_file}...")
    daily_sentiment.to_csv(output_file, index=False)
    print(f"Results saved successfully!")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Date range: {daily_sentiment['date'].min()} to {daily_sentiment['date'].max()}")
    print(f"Total days with headlines: {len(daily_sentiment)}")
    print(f"Average daily sentiment: {daily_sentiment['avg_sentiment'].mean():.3f}")
    print(f"Total headlines processed: {daily_sentiment['headline_count'].sum()}")
    print(f"Days with positive sentiment: {(daily_sentiment['avg_sentiment'] > 0).sum()}")
    print(f"Days with negative sentiment: {(daily_sentiment['avg_sentiment'] < 0).sum()}")
    print(f"Days with neutral sentiment: {(daily_sentiment['avg_sentiment'] == 0).sum()}")

def main():
    """
    Main function to run the sentiment analysis pipeline
    """
    print("=" * 60)
    print("FINANCIAL NEWS SENTIMENT ANALYSIS")
    print("=" * 60)
    
    # Process headlines and get sentiment
    results = process_headlines_sentiment('gdelt_headlines.csv')
    
    if results is None:
        print("Failed to process headlines. Exiting.")
        return
    
    daily_sentiment, full_df = results
    
    # Save results
    save_results(daily_sentiment, 'daily_sentiment.csv')
    
    # Optional: Save detailed results with individual headline sentiments
    print("\nSaving detailed results with individual sentiments...")
    full_df.to_csv('headlines_with_sentiment.csv', index=False)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Files created:")
    print("- daily_sentiment.csv: Daily aggregated sentiment scores")
    print("- headlines_with_sentiment.csv: Individual headlines with sentiment scores")

if __name__ == "__main__":
    main() 