# qr_auth/urls.py
from django.urls import path
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("QR auth ishlayapti.")

urlpatterns = [
    path("test/", test_view),
]