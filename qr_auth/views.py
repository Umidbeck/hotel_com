#qr_auth/views.py
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from qr_auth.models import Room, User


@api_view(['GET'])
@permission_classes([AllowAny])
def qr_login(request, room_number, requester=None):
    try:
        room = Room.objects.get(number=room_number, is_active=True)
        user, _ = User.objects.get_or_create(username=room_number)
        token, _ = Token.objects.get_or_create(user=user)
        requester.session['room'] = room.number
        return Response({
            'status': 'success',
            'room': room.number,
            'token': token.key,
            'check_in': room.check_in.strftime('%Y-%m-%d') if room.check_in else None
        })
    except Room.DoesNotExist:
        return Response({'status': 'error'}, status=400)