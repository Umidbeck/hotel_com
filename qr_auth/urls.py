from django.urls import path
from .views import qr_redirect, qr_image

urlpatterns = [
    path("qr/<str:qr_code>/", qr_redirect, name="qr-redirect"),
    path("qr-img/<str:qr_code>.png", qr_image, name="qr-image"),
]