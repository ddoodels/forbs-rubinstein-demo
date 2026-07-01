import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as forbs_app  # noqa: E402


class BookingApiTest(unittest.TestCase):
    def setUp(self):
        os.environ["FORBS_PREVIEW_MODE"] = "1"
        forbs_app.rate_limiter._hits.clear()
        self.app = forbs_app.create_app()
        self.client = self.app.test_client()

    def test_successful_booking_uses_telegram_sender(self):
        payload = {
            "name": "Алексей",
            "phone": "+7 (911) 111-66-80",
            "date": "01.07.2026",
            "time": "19:30",
            "guests": "4",
            "source": "2ГИС",
            "comment": "Стол у окна",
            "occasion": "Коктейли",
            "zone": "Красный зал",
            "contact_method": "Позвонить",
            "booking_context": "booking-page",
            "consent": True,
            "company": "",
        }
        with patch.object(forbs_app, "send_telegram_message", return_value={"ok": True, "preview": True}) as sender:
            response = self.client.post("/api/booking", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        message = sender.call_args.args[0]
        self.assertIn("Новая бронь FORBS", message)
        self.assertIn("Алексей", message)
        self.assertIn("Дата: 01.07.2026", message)
        self.assertIn("Гостей: 4", message)
        self.assertIn("Источник: 2ГИС", message)
        self.assertIn("Повод: Коктейли", message)
        self.assertIn("Зона/настроение: Красный зал", message)
        self.assertIn("Связь: Позвонить", message)
        self.assertIn("Контекст: booking-page", message)

    def test_required_fields_are_validated(self):
        response = self.client.post("/api/booking", json={"name": "", "phone": "", "consent": False})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

    def test_honeypot_is_rejected(self):
        response = self.client.post(
            "/api/booking",
            json={
                "name": "Бот",
                "phone": "+7 911 111 66 80",
                "consent": True,
                "company": "spam",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_date_and_guests_are_rejected(self):
        response = self.client.post(
            "/api/booking",
            json={
                "name": "Мария",
                "phone": "+7 911 111 66 80",
                "date": "01.07.2026",
                "guests": "50",
                "consent": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Количество гостей", response.get_json()["error"])

    def test_telegram_failure_returns_fallback_error(self):
        with patch.object(forbs_app, "send_telegram_message", side_effect=RuntimeError("network")):
            response = self.client.post(
                "/api/booking",
                json={
                    "name": "Ира",
                    "phone": "+7 911 111 66 80",
                    "date": "2026-07-01",
                    "time": "21:00",
                    "guests": "2",
                    "consent": True,
                },
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("Telegram", response.get_json()["error"])

    def test_booking_page_renders_new_reservation_console(self):
        response = self.client.get("/booking")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("booking-title-line", html)
        self.assertIn("Забронировать</span>", html)
        self.assertIn("стол в FORBS</span>", html)
        self.assertIn("Заполните поля, мы подтвердим стол", html)
        self.assertIn("Откуда вы узнали о нас?", html)
        self.assertIn("https://t.me/forbsbarspb", html)
        self.assertNotIn("https://t.me/forbsbar\"", html)
        self.assertNotIn("data-booking-summary", html)
        self.assertNotIn("booking-chips", html)
        self.assertNotIn("Быстрый выбор", html)
        self.assertIn("кальян за 1500", html)
        self.assertIn("Политика", html)
        self.assertIn("Согласие", html)

    def test_rendered_page_does_not_expose_telegram_secret(self):
        os.environ["FORBS_TELEGRAM_BOT_TOKEN"] = "123456:super-secret-token"
        for path in ("/", "/booking"):
            response = self.client.get(path)
            html = response.get_data(as_text=True)
            self.assertNotIn("super-secret-token", html)
            self.assertNotIn("FORBS_TELEGRAM_BOT_TOKEN", html)

    def test_seo_meta_routes_and_canonical_urls_render(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<link rel="canonical" href="https://forbsbar.ru/">', html)
        self.assertIn('property="og:image" content="https://forbsbar.ru/static/assets/images/meta/og-forbs.jpg"', html)
        self.assertIn('name="twitter:card" content="summary_large_image"', html)
        self.assertIn('"@type": "BarOrPub"', html)
        self.assertIn("Кальян 1500", html)
        self.assertIn("коктейли", html)
        self.assertIn("Документы", html)
        self.assertNotIn('"makesOffer"', html)

        booking_response = self.client.get("/booking")
        booking_html = booking_response.get_data(as_text=True)
        self.assertIn('<link rel="canonical" href="https://forbsbar.ru/booking">', booking_html)
        self.assertIn('"@type": "ReserveAction"', booking_html)
        self.assertIn("/legal#consent", booking_html)

        menu_response = self.client.get("/menu")
        menu_html = menu_response.get_data(as_text=True)
        self.assertEqual(menu_response.status_code, 200)
        self.assertIn("Меню кухни и бара", menu_html)
        self.assertIn("Барное меню", menu_html)
        self.assertIn("Безалкогольное", menu_html)
        self.assertIn("Алкогольное", menu_html)
        self.assertNotIn("menu-kitchen-1.webp", menu_html)
        self.assertIn("menu-kitchen-2.webp", menu_html)
        self.assertIn("menu-bar-1.webp", menu_html)
        self.assertIn("menu-bar-2.webp", menu_html)
        self.assertIn("menu-bar.pdf", menu_html)
        self.assertNotIn("Sunset Sour 1000", menu_html)

        legal_response = self.client.get("/legal")
        legal_html = legal_response.get_data(as_text=True)
        self.assertEqual(legal_response.status_code, 200)
        self.assertIn("Документы FORBS", legal_html)
        self.assertIn("Политика обработки персональных данных", legal_html)
        self.assertIn("Согласие на обработку персональных данных", legal_html)

        privacy_response = self.client.get("/privacy")
        self.assertEqual(privacy_response.status_code, 301)
        self.assertIn("/legal#privacy", privacy_response.headers["Location"])

        consent_response = self.client.get("/personal-data-consent")
        self.assertEqual(consent_response.status_code, 301)
        self.assertIn("/legal#consent", consent_response.headers["Location"])

        robots = self.client.get("/robots.txt")
        self.assertEqual(robots.status_code, 200)
        self.assertIn("Sitemap: https://forbsbar.ru/sitemap.xml", robots.get_data(as_text=True))

        sitemap = self.client.get("/sitemap.xml")
        sitemap_xml = sitemap.get_data(as_text=True)
        self.assertEqual(sitemap.status_code, 200)
        self.assertIn("<loc>https://forbsbar.ru/</loc>", sitemap_xml)
        self.assertIn("<loc>https://forbsbar.ru/booking</loc>", sitemap_xml)
        self.assertIn("<loc>https://forbsbar.ru/menu</loc>", sitemap_xml)
        self.assertIn("<loc>https://forbsbar.ru/legal</loc>", sitemap_xml)


if __name__ == "__main__":
    unittest.main()
