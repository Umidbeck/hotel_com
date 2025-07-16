# qr_auth/views.py
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from qr_auth.models import Room
from qr_auth.utils import generate_qr_code
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponseNotFound

def qr_redirect(request, qr_code):
    """Doimiy QR → hozirgi token asosida redirect"""
    room = get_object_or_404(Room, qr_code=qr_code)
    return redirect(room.get_absolute_url())

def qr_image(request, qr_code):
    """Doimiy QR-kod rasm (PNG) olish"""
    short_url = request.build_absolute_uri(f"/qr/{qr_code}/")
    buf = generate_qr_code(short_url)
    return HttpResponse(buf, content_type="image/png")

@api_view(['GET'])
def validate_token(request, room_number):
    token = request.query_params.get("token")
    if not token:
        return Response({"valid": False}, status=400)

    exists = Room.objects.filter(number=room_number, token=token).exists()
    return Response({"valid": exists})

@api_view(['POST'])
def set_language(request, room_number):
    lang = request.data.get('language')
    token = request.query_params.get('token')

    try:
        room = Room.objects.get(number=room_number, token=token)
        room.language = lang
        room.save()
        return Response({'success': True})
    except Room.DoesNotExist:
        return Response({'success': False}, status=404)

@api_view(['GET'])
def get_language(request, room_number):
    token = request.query_params.get('token')
    try:
        room = Room.objects.get(number=room_number, token=token)
        return Response({'language': room.language})
    except Room.DoesNotExist:
        return Response({'language': None}, status=404)

from django.http import JsonResponse
from qr_auth.models import Room


def room_info(request, room_number):  # ❗ NOMI MUHIM
    token = request.GET.get('token')
    try:
        room = Room.objects.get(number=room_number, token=token)
        return JsonResponse({'language': room.language})
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
