# qr_auth/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from qr_auth.models import Room

@api_view(['GET'])
@permission_classes([AllowAny])
def qr_login(request, room_number):
    room, created = Room.objects.get_or_create(number=room_number)
    return Response({
        'status': 'success',
        'room': room.number,
        'token': room.token,
        'link': room.get_absolute_url()
    })