"""
Social Media Simulator
Generates realistic social media data for Sri Lanka context
"""
import json
import redis
from datetime import datetime, timezone, timedelta
import random

REDIS_KEY = "collector:incoming"

# Initialize Redis
try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis")
except redis.ConnectionError:
    print("⚠️  Redis not available - data will be saved to files")
    r = None

# Realistic Sri Lankan social media topics
SL_TOPICS = [
    {"topic": "fuel prices", "sentiment": "concern", "urgency": "medium"},
    {"topic": "rupee exchange rate", "sentiment": "concern", "urgency": "high"},
    {"topic": "inflation", "sentiment": "negative", "urgency": "high"},
    {"topic": "power cut", "sentiment": "frustration", "urgency": "high"},
    {"topic": "road conditions", "sentiment": "negative", "urgency": "medium"},
    {"topic": "public transport", "sentiment": "mixed", "urgency": "medium"},
    {"topic": "water shortage", "sentiment": "concern", "urgency": "high"},
    {"topic": "government policy", "sentiment": "mixed", "urgency": "medium"},
    {"topic": "protest", "sentiment": "concern", "urgency": "high"},
    {"topic": "tourism boost", "sentiment": "positive", "urgency": "low"},
    {"topic": "tech startup", "sentiment": "positive", "urgency": "low"},
    {"topic": "cultural festival", "sentiment": "positive", "urgency": "low"},
    {"topic": "monsoon rain", "sentiment": "concern", "urgency": "medium"},
    {"topic": "flood warning", "sentiment": "alert", "urgency": "high"},
]

TWEET_TEMPLATES = {
    "fuel prices": [
        "Fuel prices going up again 😞 #SriLanka #Economy",
        "When will fuel prices stabilize? #LKA",
        "Long queues at petrol stations #Colombo"
    ],
    "power cut": [
        "Another power cut 💻🔌 #PowerCut #SriLanka",
        "5 hour power cut scheduled #LKA",
        "Power outages affecting businesses #SriLanka"
    ],
    "tourism boost": [
        "Great to see tourists returning! 🇱🇰 #Tourism",
        "Hotel bookings up this month #SriLanka",
        "Beaches bringing visitors back #LKA"
    ],
    "protest": [
        "Peaceful protest in Colombo #SriLanka",
        "Citizens voicing concerns #LKA",
        "Traffic disruption near Parliament #Colombo"
    ],
    "monsoon rain": [
        "Heavy rains expected ☔ #SriLanka #Weather",
        "Monsoon affecting commute #Colombo",
        "Flood warnings issued #LKA"
    ],
}

LOCATIONS = ["Colombo", "Kandy", "Galle", "Jaffna", "Negombo"]
USERNAMES = ["citizen_lk", "colombo_insider", "lka_news", "sl_observer", "local_voice"]

def generate_realistic_social_posts(count=30):
    """Generate realistic social media posts"""
    posts = []
    
    for _ in range(count):
        topic_data = random.choice(SL_TOPICS)
        topic = topic_data["topic"]
        
        if topic in TWEET_TEMPLATES:
            content = random.choice(TWEET_TEMPLATES[topic])
        else:
            content = f"Discussing {topic} in Sri Lanka #LKA"
        
        followers = random.randint(50, 50000)
        retweets = max(0, int(random.gauss(5, 10)))
        likes = max(0, int(random.gauss(10, 20)))
        
        if topic_data["urgency"] == "high":
            retweets = int(retweets * 2.5)
            likes = int(likes * 2.5)
        
        hours_ago = random.uniform(0, 24)
        timestamp = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        
        username = random.choice(USERNAMES) + str(random.randint(1, 999))
        post_id = random.randint(1000000000000000, 9999999999999999)
        
        post = {
            "source": "X (Twitter) [Simulated]",
            "source_type": "social",
            "url": f"https://x.com/{username}/status/{post_id}",
            "title": content[:120],
            "snippet": content,
            "published": timestamp.isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "language": "en",
            "collector": "social_simulator",
            "meta": {
                "username": username,
                "user_followers": followers,
                "retweet_count": retweets,
                "like_count": likes,
                "topic": topic,
                "sentiment": topic_data["sentiment"],
                "urgency": topic_data["urgency"],
                "location": random.choice(LOCATIONS),
                "simulated": True
            }
        }
        posts.append(post)
    
    return posts

def push_to_redis(item):
    """Push item to Redis"""
    if r:
        r.rpush(REDIS_KEY, json.dumps(item, ensure_ascii=False))
    else:
        save_to_file(item)

def save_to_file(item):
    """Save to file as fallback"""
    from pathlib import Path
    output_dir = Path("data_output/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"social_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

SNSCRAPE_AVAILABLE = True
SL_HASHTAGS = ["srilanka", "lka", "colombo"]

def fetch_by_hashtag(hashtag, max_tweets=50):
    """Simulate fetching tweets"""
    print(f"🔄 Generating simulated posts for #{hashtag}...")
    posts = generate_realistic_social_posts(count=max_tweets)
    print(f"✅ Generated {len(posts)} simulated posts")
    return posts

if __name__ == "__main__":
    print("\n🧪 Testing Social Simulator\n")
    posts = generate_realistic_social_posts(count=5)
    for i, post in enumerate(posts, 1):
        print(f"{i}. {post['snippet']}")
        print(f"   Topic: {post['meta']['topic']}, Urgency: {post['meta']['urgency']}\n")