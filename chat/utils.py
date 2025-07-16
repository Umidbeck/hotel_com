# chat/utils.py
import json
import redis
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Redis bilan aloqa
r = redis.Redis(host='127.0.0.1', port=6379, db=1, decode_responses=True)

def enqueue_if_offline(room_number: str, text: str, uuid: str, sender: str = 'bot'):
    """Agar foydalanuvchi ulangan bo‘lmasa, xabarni Redis’ga yozamiz."""
    key = f"pending:{room_number}"
    payload = {
        "text": text,
        "uuid": uuid,
        "sender": sender,
        "time": "pending"  # vaqtni WS qayta ulanganida qo‘yib beramiz
    }
    r.lpush(key, json.dumps(payload))
    r.expire(key, 3600)  # 1 soatda o‘chadi

def flush_pending(room_number: str):
    """Brauzer qayta ulanishi bilan Redis’dagi pending xabarlarni yuborish."""
    key = f"pending:{room_number}"
    channel_layer = get_channel_layer()
    while True:
        raw = r.rpop(key)
        if not raw:
            break
        payload = json.loads(raw)
        payload["time"] = __get_now_time()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room_number}",
            {
                "type": "chat_message",
                "message": payload["text"],
                "sender": payload.get("sender", "bot"),
                "uuid": payload["uuid"],
                "time": payload["time"],
            }
        )

def __get_now_time():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")
