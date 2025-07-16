from django.urls import path
from .views import qr_redirect, qr_image, validate_token, set_language, get_language, room_info

urlpatterns = [
    path("qr/<str:qr_code>/", qr_redirect, name="qr-redirect"),
    path("qr-img/<str:qr_code>.png", qr_image, name="qr-image"),
    path("validate/<str:room_number>/", validate_token),
    path("set-language/<str:room_number>/", set_language),
    path("get-language/<str:room_number>/", get_language),
    path("room-info/<str:room_number>/", room_info),  # ✅ to‘g‘ri
]