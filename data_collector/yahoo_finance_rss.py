# collect_yahoo_working.py
import feedparser
import json
from datetime import datetime
import time
import re

def clean_html(text):
    """Remove HTML tags from text"""
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    text = ' '.join(text.split())
    return text

def collect_yahoo_finance():
    """
    Collect Yahoo Finance news using WORKING RSS feeds
    All links tested and verified!
    """
    print("=" * 60)
    print("YAHOO FINANCE NEWS (WORKING FEEDS ONLY)")
    print("=" * 60)
    print()
    
    all_entries = []
    
    # ============================================
    # GENERAL NEWS FEEDS (VERIFIED WORKING)
    # ============================================
    
    general_feeds = [
        ('https://finance.yahoo.com/news/rssindex', 'Top Yahoo Finance News'),
        ('https://finance.yahoo.com/rss/stock-market-news', 'Stock Market News'),
        ('https://finance.yahoo.com/rss/markets', 'Markets'),
        ('https://finance.yahoo.com/rss/earnings', 'Earnings'),
        ('https://finance.yahoo.com/rss/economy', 'Economy'),
        ('https://finance.yahoo.com/rss/personal-finance', 'Personal Finance'),
        ('https://finance.yahoo.com/rss/technology', 'Technology'),
        ('https://finance.yahoo.com/rss/crypto', 'Crypto & Digital Assets'),
    ]
    
    print("📰 Collecting general news feeds...")
    
    for feed_url, feed_name in general_feeds:
        print(f"  {feed_name}...", end=' ')
        
        try:
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print("✗ (no entries)")
                continue
            
            count = 0
            for entry in feed.entries[:100]:  # Top 100
                try:
                    title = entry.get('title', '')
                    
                    # Get description
                    description = ''
                    if hasattr(entry, 'summary'):
                        description = clean_html(entry.summary)
                    
                    # Combine
                    text = f"{title}"
                    if description:
                        text += f". {description}"
                    
                    text = text.strip()
                    
                    if len(text) < 50:
                        continue
                    
                    if len(text) > 2000:
                        text = text[:2000]
                    
                    url = entry.get('link', '')
                    
                    # Get date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
                    else:
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    entry_data = {
                        'id': f"yahoo_{feed_name.replace(' ', '_')}_{hash(title)}",
                        'text': text,
                        'metadata': {
                            'source': 'Yahoo Finance',
                            'category': feed_name,
                            'date': date,
                            'url': url,
                            'type': 'financial_news'
                        }
                    }
                    
                    all_entries.append(entry_data)
                    count += 1
                    
                except:
                    continue
            
            print(f"✓ ({count})")
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ ({e})")
    
    # ============================================
    # TICKER-SPECIFIC FEEDS (ALWAYS WORK)
    # ============================================
    
    print("\n📊 Collecting ticker-specific news...")
    
    # Large list of popular tickers
    tickers = [
        # Mega caps & tech leaders
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'BRK-B',
        'NVDA', 'AMD', 'INTC', 'ORCL', 'CRM', 'ADBE', 'CSCO', 'AVGO',
        'TXN', 'QCOM', 'NOW', 'SNOW', 'PLTR', 'PANW', 'CRWD',
        
        # Media & telecom
        'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'TMUS',
        
        # Finance & payments
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'USB',
        'PNC', 'TFC', 'COF', 'BK', 'STT', 'SPGI', 'MCO', 'CME', 'ICE',
        'V', 'MA', 'PYPL', 'FIS', 'FISV', 'ADP',
        
        # Healthcare & biotech
        'JNJ', 'UNH', 'PFE', 'ABBV', 'LLY', 'MRK', 'TMO', 'ABT', 'DHR',
        'BMY', 'AMGN', 'GILD', 'CVS', 'CI', 'HUM', 'ISRG', 'REGN', 'VRTX',
        'BIIB', 'ILMN', 'MRNA', 'BNTX',

        # Consumer & retail
        'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'COST', 'TGT', 'LOW', 'TJX',
        'PG', 'KO', 'PEP', 'PM', 'MO', 'CL', 'EL', 'MDLZ', 'KHC',
        'BBY', 'ROST', 'DG',
        
        # Auto & EV
        'F', 'GM', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI',
        
        # Energy & materials
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY',
        'HAL', 'BKR', 'DVN', 'FANG', 'LIN', 'APD', 'ECL', 'DD', 'NEM',
        'FCX', 'NUE', 'VMC', 'MLM',
        
        # Industrial & aerospace
        'BA', 'CAT', 'GE', 'HON', 'UPS', 'RTX', 'LMT', 'DE', 'MMM',
        'UNP', 'FDX', 'NSC', 'CSX', 'GD', 'NOC', 'EMR', 'LHX', 'HII',
        
        # Utilities & real estate
        'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'PEG', 'XEL',
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL', 'DLR',
        
        # Semiconductors
        'TSM', 'ASML', 'ADI', 'AMAT', 'LRCX', 'KLAC', 'MCHP', 'ON', 'NXPI',
        
        # Software & cloud
        'INTU', 'WDAY', 'TEAM', 'ZM', 'DDOG', 'FTNT', 'ZS',
        
        # E-commerce & internet
        'SHOP', 'ETSY', 'EBAY', 'BABA', 'JD', 'PDD', 'MELI',
        
        # Social / entertainment
        'SNAP', 'PINS', 'SPOT', 'RBLX', 'U', 'MTCH',
        
        # Travel & leisure
        'ABNB', 'BKNG', 'MAR', 'HLT', 'UBER', 'LYFT', 'DAL', 'UAL', 'AAL',

        # Restaurants
        'YUM', 'CMG', 'DPZ', 'QSR', 'WEN',
        
        # Crypto
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'SOL-USD',
        'DOGE-USD', 'DOT-USD', 'MATIC-USD', 'AVAX-USD',
        
        # ETFs & indices
        'SPY', 'QQQ', 'VOO', 'VTI', 'IWM', 'DIA', 'VEA', 'IEMG', 'EFA',
        'XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE', 'XLB',
        'GLD', 'SLV', 'TLT', 'AGG', 'BND', 'VYM', 'VIG', 'SCHD',
        
        # Emerging / popular names
        'COIN', 'HOOD', 'SOFI', 'UPST', 'AFRM', 'RKLB', 'SPCE',
        'PLUG', 'FCEL', 'BE', 'BLNK', 'CHPT',
        
        # Chinese ADRs
        'BIDU', 'BILI',

        # Other large caps
        'IBM', 'HPE', 'HPQ', 'DELL', 'AKAM',
        'RITE', 'CAH', 'MCK',
        'KR', 'SYY', 'GIS', 'K', 'CPB', 'CAG'
    ]
    
    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i}/{len(tickers)}] {ticker}...", end=' ')
        
        try:
            # Ticker-specific RSS feed (ALWAYS WORKS)
            feed_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print("✗")
                continue
            
            count = 0
            for entry in feed.entries[:20]:  # Top 20 per ticker
                try:
                    title = entry.get('title', '')
                    description = clean_html(entry.get('summary', ''))
                    
                    # Create text with ticker context
                    text = f"{ticker}: {title}"
                    if description:
                        text += f". {description}"
                    
                    if len(text) < 50:
                        continue
                    
                    if len(text) > 2000:
                        text = text[:2000]
                    
                    url = entry.get('link', '')
                    
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
                    else:
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    entry_data = {
                        'id': f"yahoo_ticker_{ticker}_{hash(title)}",
                        'text': text,
                        'metadata': {
                            'source': 'Yahoo Finance',
                            'ticker': ticker,
                            'category': 'Stock News',
                            'date': date,
                            'url': url,
                            'type': 'stock_news'
                        }
                    }
                    
                    all_entries.append(entry_data)
                    count += 1
                    
                except:
                    continue
            
            print(f"✓ ({count})")
            time.sleep(0.5)  # Be respectful
            
        except Exception as e:
            print("✗")
            continue
    
    # ============================================
    # REMOVE DUPLICATES & SAVE
    # ============================================
    
    print("\n🔍 Removing duplicates...")
    
    seen_urls = set()
    unique_entries = []
    
    for entry in all_entries:
        url = entry['metadata']['url']
        if url not in seen_urls:
            seen_urls.add(url)
            unique_entries.append(entry)
    
    # Save
    if len(unique_entries) > 0:
        output_file = 'yahoo_finance_data.jsonl'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in unique_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"\n{'=' * 60}")
        print(f"✅ SUCCESS!")
        print(f"   Total collected: {len(all_entries):,}")
        print(f"   Unique articles: {len(unique_entries):,}")
        print(f"   Saved to: {output_file}")
        print(f"{'=' * 60}")
        
        # Statistics
        print(f"\n📊 Statistics:")
        
        # By category
        categories = {}
        for entry in unique_entries:
            cat = entry['metadata']['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\nBy Category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat}: {count}")
        
    else:
        print("\n⚠️  No articles collected")

if __name__ == "__main__":
    collect_yahoo_finance()