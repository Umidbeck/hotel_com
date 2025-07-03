from django.test import TestCase
from django.urls import reverse
from .models import Room
from datetime import date


class QrAuthTest(TestCase):
    def setUp(self):
        Room.objects.create(
            number="101",
            check_in=date(2024, 1, 1),
            check_out=date(2024, 1, 10)
        )

    def test_qr_login(self):
        response = self.client.get(reverse('qr_login', args=["101"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'success')
        self.assertEqual(response.json()['room'], "101")