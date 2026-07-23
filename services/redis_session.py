import json
import redis


# ==========================================
# REDIS CONFIGURATION
# ==========================================
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Session expires after 1 hour
SESSION_TTL = 3600

# Keep only last 5 conversation turns
MAX_HISTORY = 5


# ==========================================
# CREATE REDIS CLIENT
# ==========================================
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


def get_session_key(session_id: str) -> str:
    return f"mini_nabl:session:{session_id}"


def get_session_history(session_id: str) -> list:
    key = get_session_key(session_id)

    data = redis_client.get(key)

    if data:
        session_data = json.loads(data)
        return session_data.get("history", [])

    return []


def add_to_history(
    session_id: str,
    user_message: str,
    assistant_message: str
):
    # Get existing history
    history = get_session_history(session_id)

    # Add new conversation
    history.append({
        "user": user_message,
        "assistant": assistant_message
    })

    # Keep only last 5 conversations
    history = history[-MAX_HISTORY:]

    session_data = {
        "history": history
    }

    key = get_session_key(session_id)

    # Save in Redis with 1-hour expiry
    redis_client.setex(
        key,
        SESSION_TTL,
        json.dumps(session_data)
    )


def clear_session(session_id: str):
    key = get_session_key(session_id)
    redis_client.delete(key)