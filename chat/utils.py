#chat/utils.py
import json
import redis
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Redis bilan to‘g‘ridan-to‘g‘ri aloqa
r = redis.Redis(host='127.0.0.1', port=6379, db=1, decode_responses=True)

def enqueue_if_offline(room_number: str, text: str, uuid: str):
    """WebSocket guruhda hech kim bo‘lmasa xabarni Redis-ga yozadi."""
    key = f"pending:{room_number}"
    payload = {"text": text, "uuid": uuid, "time": "pending"}
    r.lpush(key, json.dumps(payload))
    r.expire(key, 3600)

def flush_pending(room_number: str):
    """Brauzer qayta ulanishi bilan pending larni yuboradi."""
    key = f"pending:{room_number}"
    channel_layer = get_channel_layer()
    while True:
        raw = r.rpop(key)  # FIFO
        if not raw:
            break
        payload = json.loads(raw)
        async_to_sync(channel_layer.group_send)(
            f"chat_{room_number}",
            {
                "type": "chat_message",
                "message": payload["text"],
                "sender": "bot",
                "time": payload["time"],
                "uuid": payload["uuid"],
            }
        )

# def mark_delivered(room_number: str, msg_uuid: str):
#     cache.set(f"ack:{room_number}:{msg_uuid}", 1, CACHE_TTL)