#qr_auth/utils.py
import qrcode
from io import BytesIO

def generate_qr_code(url: str) -> BytesIO:
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    return buf