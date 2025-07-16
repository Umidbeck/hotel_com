# qr_auth/views.py
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from qr_auth.models import Room
from qr_auth.utils import generate_qr_code

def qr_redirect(request, qr_code):
    """Doimiy QR → hozirgi token asosida redirect"""
    room = get_object_or_404(Room, qr_code=qr_code)
    return redirect(room.get_absolute_url())

def qr_image(request, qr_code):
    """Doimiy QR-kod rasm (PNG) olish"""
    short_url = request.build_absolute_uri(f"/qr/{qr_code}/")
    buf = generate_qr_code(short_url)
    return HttpResponse(buf, content_type="image/png")