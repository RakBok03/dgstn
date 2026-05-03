from django.test import SimpleTestCase


class YandexVerificationTests(SimpleTestCase):
    def test_yandex_verification_file_is_served_from_site_root(self):
        response = self.client.get("/yandex_7f3ca55e413f31a8.html")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=UTF-8")
        self.assertContains(response, "Verification: 7f3ca55e413f31a8")


class SiteIconTests(SimpleTestCase):
    def test_favicon_ico_is_served_from_site_root(self):
        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/x-icon")

    def test_favicon_png_is_served_from_site_root(self):
        response = self.client.get("/favicon.png")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
