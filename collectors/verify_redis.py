"""
Verify Redis Queue - Check collected data
"""
import redis
import json

try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("Connected to Redis\n")
    
    # Get queue length
    queue_length = r.llen("collector:incoming")
    print(f"Queue length: {queue_length} messages\n")
    
    if queue_length > 0:
        # Pop one message (non-destructive peek would use LINDEX)
        msg = r.lindex("collector:incoming", 0)  # Peek at first item
        
        if msg:
            data = json.loads(msg)
            print("Sample message:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("No messages in queue")
    else:
        print("Queue is empty. Start collectors to add data.")
        
except redis.ConnectionError:
    print("Cannot connect to Redis")
    print("Start Redis with: cd infra && docker compose up -d")
except Exception as e:
    print(f"Error: {e}")