# reddit_no_auth.py
import requests
import json
from datetime import datetime
import time

def collect_reddit_no_auth():
    """
    Collect Reddit data WITHOUT API credentials
    Uses direct JSON requests - NO AUTHENTICATION REQUIRED!
    """
    print("=" * 60)
    print("REDDIT COLLECTION (NO AUTH REQUIRED)")
    print("=" * 60)
    print()
    
    # ============================================
    # KEY PART: No credentials needed for JSON!
    # ============================================
    print("🔌 Connecting to Reddit via JSON API...")
    print("   (No API credentials needed!)")
    
    # User-Agent is required to avoid immediate blocking
    headers = {
        'User-Agent': 'finance_research_bot/1.0'
    }
    
    print("✓ Ready to collect!\n")
    
    # ============================================
    # Configure what to collect
    # ============================================
    
    # Subreddits grouped by collection volume
    high_volume_subreddits = [
        'stocks', 'investing', 'CryptoCurrency', 'wallstreetbets', 'Bitcoin',
        'stockmarket', 'financialindependence', 'FIRE', 
        'ETFs', 'options', 'dividends', 'valueinvesting', 'personalfinance'
    ]  # collect up to 1000 posts each

    standard_subreddits = [
        'MSFT', 'teslainvestorsclub', 'AppleInvestors', 'AMD_Stock', 'AlphabetStock'
        'nvidia', 'google', 'meta', 'microsoft', 'Intel', 'SoFiStock'
    ]  # collect up to 200 posts each

    subreddit_configs = (
        # [(sub, 1000) for sub in high_volume_subreddits] +
        [(sub, 200) for sub in standard_subreddits]
    )
    
    # Quality filters
    MIN_TEXT_LENGTH = 100    # Minimum character count
    MAX_TEXT_LENGTH = 2000   # Maximum to keep manageable
    MIN_SCORE = 5            # Minimum upvotes
    
    # ============================================
    # Start collecting
    # ============================================
    
    all_entries = []
    total_collected = 0
    
    for subreddit_name, posts_per_subreddit in subreddit_configs:
        print(f"📊 Collecting from r/{subreddit_name}...")
        
        sub_count = 0
        after = None
        
        try:
            while sub_count < posts_per_subreddit:
                # Construct URL for JSON endpoint
                # limit=100 is the max for the JSON API
                url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit=100"
                if after:
                    url += f"&after={after}"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    print(f"  ⚠️  Error accessing r/{subreddit_name}: {response.status_code}")
                    if response.status_code == 429:
                        print("      Rate limited! Waiting 5 seconds...")
                        time.sleep(5)
                        continue
                    break
                
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                if not posts:
                    break
                
                for post_data in posts:
                    if sub_count >= posts_per_subreddit:
                        break
                        
                    post = post_data['data']
                    
                    # Skip low-quality posts
                    if post.get('score', 0) < MIN_SCORE:
                        continue
                    
                    # Combine title and body text
                    title = post.get('title', '')
                    selftext = post.get('selftext', '')
                    full_text = f"{title}. {selftext}".strip()
                    
                    # Skip if too short (just title, no content)
                    if len(full_text) < MIN_TEXT_LENGTH:
                        continue
                    
                    # Trim if too long
                    if len(full_text) > MAX_TEXT_LENGTH:
                        full_text = full_text[:MAX_TEXT_LENGTH]
                    
                    # Create data entry
                    entry = {
                        'id': f"reddit_{subreddit_name}_{post.get('id')}",
                        'text': full_text,
                        'metadata': {
                            'source': 'Reddit',
                            'subreddit': subreddit_name,
                            'date': datetime.fromtimestamp(post.get('created_utc', 0)).strftime('%Y-%m-%d'),
                            'score': post.get('score', 0),
                            'num_comments': post.get('num_comments', 0),
                            'url': f"https://reddit.com{post.get('permalink', '')}",
                            'type': 'discussion',
                            'author': str(post.get('author', 'deleted'))
                        }
                    }
                    
                    all_entries.append(entry)
                    sub_count += 1
                
                # Get the 'after' token for the next page
                after = data.get('data', {}).get('after')
                if not after:
                    break
                    
                # Small delay to be respectful
                time.sleep(2.0)  # Longer delay for JSON API
            
            print(f"  ✓ Collected {sub_count} posts from r/{subreddit_name}")
            total_collected += sub_count
            
        except Exception as e:
            print(f"  ✗ Error with r/{subreddit_name}: {e}")
            continue
        
        print()  # Blank line between subreddits
    
    # ============================================
    # Save results
    # ============================================
    
    if len(all_entries) > 0:
        output_file = 'reddit_data.jsonl'
        
        with open(output_file, 'a', encoding='utf-8') as f:
            for entry in all_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print("=" * 60)
        print(f"✅ SUCCESS!")
        print(f"   Collected: {len(all_entries)} posts")
        print(f"   Saved to: {output_file}")
        print("=" * 60)
        
        # Show breakdown by subreddit
        print("\n📊 Breakdown by subreddit:")
        subreddit_counts = {}
        for entry in all_entries:
            sub = entry['metadata']['subreddit']
            subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
        
        for sub, count in sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   r/{sub}: {count} posts")
        
    else:
        print("⚠️  No data collected. Check your internet connection.")

if __name__ == "__main__":
    collect_reddit_no_auth()
