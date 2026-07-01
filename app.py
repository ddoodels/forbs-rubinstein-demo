from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from flask import Flask, Response, jsonify, redirect, render_template, request, send_from_directory, url_for


def load_local_env(path: str = ".env") -> None:
    env_path = Path(__file__).resolve().parent / path
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()


def env_value(key: str, default: str = "") -> str:
    return os.environ.get(key) or default


SITE_NAME = "FORBS"
SITE_URL = env_value("FORBS_SITE_URL", "https://forbsbar.ru").rstrip("/")
PHONE_DISPLAY = "+7 (911) 111-66-80"
PHONE_HREF = "+79111116680"
TELEGRAM_URL = "https://t.me/forbsbarspb"
ADDRESS = "ул. Рубинштейна, 40 / Загородный проспект, 11"
HOURS = "Ежедневно 17:00-06:00"
LEGAL_NAME = env_value("FORBS_LEGAL_NAME", 'ООО "ЛИДЕР"')
LEGAL_ADDRESS = env_value(
    "FORBS_LEGAL_ADDRESS",
    "197341, г. Санкт-Петербург, вн. тер. г. муниципальный округ Комендантский аэродром, "
    "Аллея Поликарпова, д. 5, лит. А, кв. 393",
)
LEGAL_INN = env_value("FORBS_LEGAL_INN", "7807258280")
LEGAL_KPP = env_value("FORBS_LEGAL_KPP", "780701001")
LEGAL_OGRN = env_value("FORBS_LEGAL_OGRN", "1227800100835")
LEGAL_EMAIL = env_value("FORBS_LEGAL_EMAIL")
LEGAL_DIRECTOR = env_value("FORBS_LEGAL_DIRECTOR", "Григорян Гуж Каренович")
LEGAL_CONTACT_PHONE_DISPLAY = env_value("FORBS_LEGAL_CONTACT_PHONE_DISPLAY", "8 904 630 85 49")
LEGAL_CONTACT_PHONE_HREF = env_value("FORBS_LEGAL_CONTACT_PHONE_HREF", "+79046308549")
LEGAL_BANK_ACCOUNT = env_value("FORBS_LEGAL_BANK_ACCOUNT", "40702810755000088447")
LEGAL_BANK_NAME = env_value("FORBS_LEGAL_BANK_NAME", "СЕВЕРО-ЗАПАДНЫЙ БАНК ПАО СБЕРБАНК")
LEGAL_BANK_BIK = env_value("FORBS_LEGAL_BANK_BIK", "044030653")
LEGAL_BANK_CORR = env_value("FORBS_LEGAL_BANK_CORR", "30101810500000000653")
PD_OPERATOR = env_value("FORBS_PD_OPERATOR", LEGAL_NAME)
PD_OPERATOR_ADDRESS = env_value("FORBS_PD_OPERATOR_ADDRESS", LEGAL_ADDRESS)
PD_OPERATOR_EMAIL = env_value("FORBS_PD_OPERATOR_EMAIL", LEGAL_EMAIL)
PD_RETENTION = env_value("FORBS_PD_RETENTION", "до обработки заявки и последующих обращений по брони, если больший срок не требуется по закону")
POLICY_DATE = "27.06.2026"

FOOD_IMAGES = [
    ("food/044_dsc08207.webp", "Коктейль на светлом столе"),
    ("food/085_dsc08474.webp", "Красный коктейль FORBS"),
    ("food/024_dsc08111.webp", "Горячее блюдо с картофелем"),
    ("food/020_dsc08090.webp", "Тарталетки на черном столе"),
    ("food/052_dsc08256.webp", "Цитрусовый коктейль"),
    ("food/091_dsc08512.webp", "Десерт FORBS"),
]

NIGHT_IMAGES = [
    ("night/020_202602181709591486.webp", "Красный зал FORBS"),
    ("night/031_202602181710121751.webp", "Веранда FORBS вечером"),
    ("night/017_202602181709551159.webp", "Синяя лестница FORBS"),
    ("night/062_202602181710081357.webp", "Красная lounge-зона"),
    ("night/078_202602181710091324.webp", "Синий свет в зале"),
    ("night/104_202602181710161607.webp", "Вывеска FORBS ночью"),
    ("night/046_202602181710121999.webp", "Стол в красном зале"),
]

MENU_PAGES = [
    {
        "id": "kitchen",
        "label": "Кухня",
        "title": "Меню кухни",
        "pdf": "assets/menu/menu-kitchen.pdf",
        "sections": [
            {
                "title": "Меню кухни",
                "pages": [
                    ("assets/images/menu/menu-kitchen-2.webp", "Меню кухни FORBS"),
                ],
            },
        ],
    },
    {
        "id": "bar",
        "label": "Бар",
        "title": "Барное меню",
        "pdf": "assets/menu/menu-bar.pdf",
        "sections": [
            {
                "title": "Безалкогольное",
                "pages": [
                    ("assets/images/menu/menu-bar-1.webp", "Безалкогольное барное меню FORBS"),
                ],
            },
            {
                "title": "Алкогольное",
                "pages": [
                    ("assets/images/menu/menu-bar-2.webp", "Алкогольное барное меню FORBS"),
                ],
            },
        ],
    },
    {
        "id": "wine",
        "label": "Вино",
        "title": "Винная карта",
        "pdf": "assets/menu/menu-wine.pdf",
        "sections": [
            {
                "title": "Винная карта",
                "pages": [
                    ("assets/images/menu/menu-wine-1.webp", "Винная карта FORBS"),
                    ("assets/images/menu/menu-wine-2.webp", "Вина по бокалам и бутылкам FORBS"),
                ],
            },
        ],
    },
]


@dataclass
class BookingPayload:
    name: str
    phone: str
    date: str
    time: str
    guests: str
    source: str
    comment: str
    occasion: str
    zone: str
    contact_method: str
    booking_context: str
    consent: bool
    company: str


class RateLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        hits = [ts for ts in self._hits.get(key, []) if ts >= cutoff]
        if len(hits) >= self.limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True


rate_limiter = RateLimiter()


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def clean(value: Any, limit: int = 160) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return " ".join(text.split())[:limit]


def normalize_date(value: str) -> str:
    dotted = value.strip()
    try:
        return datetime.strptime(dotted, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return value


def display_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return value


def external_path(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{SITE_URL}{path}"


def parse_payload() -> BookingPayload:
    data = request.get_json(silent=True) if request.is_json else request.form
    data = data or {}
    consent_value = data.get("consent")
    return BookingPayload(
        name=clean(data.get("name"), 80),
        phone=clean(data.get("phone"), 40),
        date=normalize_date(clean(data.get("date"), 20)),
        time=clean(data.get("time"), 20),
        guests=clean(data.get("guests"), 10),
        source=clean(data.get("source"), 80),
        comment=clean(data.get("comment"), 500),
        occasion=clean(data.get("occasion"), 80),
        zone=clean(data.get("zone"), 80),
        contact_method=clean(data.get("contact_method"), 80),
        booking_context=clean(data.get("booking_context"), 120),
        consent=consent_value is True or truthy(str(consent_value)),
        company=clean(data.get("company"), 120),
    )


def validate_booking(payload: BookingPayload) -> list[str]:
    errors: list[str] = []
    if payload.company:
        errors.append("Бронь не прошла проверку.")
    if not payload.name:
        errors.append("Напишите имя.")
    digits = "".join(ch for ch in payload.phone if ch.isdigit())
    if len(digits) < 10:
        errors.append("Напишите корректный телефон.")
    if not payload.date:
        errors.append("Выберите дату.")
    else:
        try:
            datetime.strptime(payload.date, "%Y-%m-%d")
        except ValueError:
            errors.append("Укажите дату в корректном формате.")
    if not payload.time:
        errors.append("Выберите время.")
    else:
        try:
            datetime.strptime(payload.time, "%H:%M")
        except ValueError:
            errors.append("Укажите время в корректном формате.")
    if not payload.guests:
        errors.append("Укажите, на сколько гостей бронировать.")
    else:
        try:
            guests = int(payload.guests)
            if guests < 1 or guests > 30:
                errors.append("Количество гостей должно быть от 1 до 30.")
        except ValueError:
            errors.append("Количество гостей должно быть числом.")
    if len(payload.comment) > 500:
        errors.append("Пожелания слишком длинные.")
    if not payload.consent:
        errors.append("Подтвердите согласие на обработку брони.")
    return errors


def format_booking_message(payload: BookingPayload) -> str:
    lines = [
        "Новая бронь FORBS",
        f"Имя: {payload.name}",
        f"Телефон: {payload.phone}",
    ]
    if payload.date:
        lines.append(f"Дата: {display_date(payload.date)}")
    if payload.time:
        lines.append(f"Время: {payload.time}")
    if payload.guests:
        lines.append(f"Гостей: {payload.guests}")
    if payload.occasion:
        lines.append(f"Повод: {payload.occasion}")
    if payload.zone:
        lines.append(f"Зона/настроение: {payload.zone}")
    if payload.contact_method:
        lines.append(f"Связь: {payload.contact_method}")
    if payload.source:
        lines.append(f"Источник: {payload.source}")
    if payload.booking_context:
        lines.append(f"Контекст: {payload.booking_context}")
    if payload.comment:
        lines.append(f"Комментарий: {payload.comment}")
    lines.append(f"Страница: {SITE_URL}")
    lines.append(f"Время заявки: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)


def send_telegram_message(text: str) -> dict[str, Any]:
    token = os.environ.get("FORBS_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FORBS_TELEGRAM_CHAT_ID")
    thread_id = os.environ.get("FORBS_TELEGRAM_THREAD_ID")
    preview_mode = truthy(os.environ.get("FORBS_PREVIEW_MODE")) or not (token and chat_id)

    if preview_mode:
        return {"ok": True, "preview": True}

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if thread_id:
        payload["message_thread_id"] = thread_id

    body = json.dumps(payload).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        description = "Telegram request failed"
        try:
            error_body = json.loads(exc.read().decode("utf-8"))
            description = clean(error_body.get("description"), 220) or description
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        raise RuntimeError(description) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Telegram request failed") from exc

    if not result.get("ok"):
        description = clean(result.get("description"), 220) or "Telegram rejected the message"
        raise RuntimeError(description)
    return {"ok": True, "preview": False}


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    def site_context() -> dict[str, Any]:
        legal_complete = all([LEGAL_NAME, LEGAL_ADDRESS, LEGAL_INN, LEGAL_OGRN, PD_OPERATOR, PD_OPERATOR_ADDRESS])
        return dict(
            site_name=SITE_NAME,
            site_url=SITE_URL,
            og_image_url=external_path(url_for("static", filename="assets/images/meta/og-forbs.jpg")),
            hero_image_url=external_path(url_for("static", filename="assets/images/meta/hero-after-dark-clean.webp")),
            favicon_url=external_path(url_for("static", filename="favicon.svg")),
            manifest_url=external_path(url_for("static", filename="site.webmanifest")),
            phone_display=PHONE_DISPLAY,
            phone_href=PHONE_HREF,
            telegram_url=TELEGRAM_URL,
            address=ADDRESS,
            hours=HOURS,
            food_images=FOOD_IMAGES,
            night_images=NIGHT_IMAGES,
            legal_name=LEGAL_NAME,
            legal_address=LEGAL_ADDRESS,
            legal_inn=LEGAL_INN,
            legal_kpp=LEGAL_KPP,
            legal_ogrn=LEGAL_OGRN,
            legal_email=LEGAL_EMAIL,
            legal_director=LEGAL_DIRECTOR,
            legal_contact_phone_display=LEGAL_CONTACT_PHONE_DISPLAY,
            legal_contact_phone_href=LEGAL_CONTACT_PHONE_HREF,
            legal_bank_account=LEGAL_BANK_ACCOUNT,
            legal_bank_name=LEGAL_BANK_NAME,
            legal_bank_bik=LEGAL_BANK_BIK,
            legal_bank_corr=LEGAL_BANK_CORR,
            pd_operator=PD_OPERATOR or LEGAL_NAME or SITE_NAME,
            pd_operator_address=PD_OPERATOR_ADDRESS or LEGAL_ADDRESS,
            pd_operator_email=PD_OPERATOR_EMAIL or LEGAL_EMAIL,
            pd_retention=PD_RETENTION,
            policy_date=POLICY_DATE,
            legal_complete=legal_complete,
            menu_pages=MENU_PAGES,
        )

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            canonical_url=external_path("/"),
            **site_context(),
        )

    @app.get("/booking")
    def booking():
        return render_template(
            "booking.html",
            canonical_url=external_path("/booking"),
            **site_context(),
        )

    @app.get("/menu")
    def menu():
        return render_template(
            "menu.html",
            canonical_url=external_path("/menu"),
            **site_context(),
        )

    @app.get("/legal")
    def legal():
        return render_template(
            "legal.html",
            canonical_url=external_path("/legal"),
            **site_context(),
        )

    @app.get("/privacy")
    def privacy():
        return redirect(url_for("legal", _anchor="privacy"), code=301)

    @app.get("/personal-data-consent")
    def personal_data_consent():
        return redirect(url_for("legal", _anchor="consent"), code=301)

    @app.post("/api/booking")
    def api_booking():
        client_key = request.headers.get("X-Forwarded-For", request.remote_addr or "local")
        client_key = client_key.split(",")[0].strip()
        if not rate_limiter.allowed(client_key):
            return jsonify(ok=False, error="Слишком много броней. Попробуйте чуть позже."), 429

        payload = parse_payload()
        errors = validate_booking(payload)
        if errors:
            return jsonify(ok=False, error=" ".join(errors)), 400

        message = format_booking_message(payload)
        try:
            result = send_telegram_message(message)
        except RuntimeError:
            app.logger.exception("Booking Telegram delivery failed")
            return jsonify(ok=False, error="Не удалось отправить бронь. Напишите нам в Telegram."), 502

        return jsonify(ok=True, preview=result.get("preview", False))

    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True)

    @app.get("/favicon.ico")
    def favicon_ico():
        return send_from_directory(app.static_folder, "favicon.svg", mimetype="image/svg+xml")

    @app.get("/robots.txt")
    def robots_txt():
        body = "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                f"Sitemap: {external_path('/sitemap.xml')}",
                "",
            ]
        )
        return Response(body, mimetype="text/plain; charset=utf-8")

    @app.get("/sitemap.xml")
    def sitemap_xml():
        today = date.today().isoformat()
        urls = [
            (external_path("/"), "1.0"),
            (external_path("/booking"), "0.8"),
            (external_path("/menu"), "0.8"),
            (external_path("/legal"), "0.5"),
        ]
        url_nodes = "\n".join(
            "  <url>"
            f"<loc>{escape(loc)}</loc>"
            f"<lastmod>{today}</lastmod>"
            "<changefreq>weekly</changefreq>"
            f"<priority>{priority}</priority>"
            "</url>"
            for loc, priority in urls
        )
        body = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{url_nodes}\n</urlset>\n'
        return Response(body, mimetype="application/xml; charset=utf-8")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5055"))
    app.run(host="127.0.0.1", port=port, debug=truthy(os.environ.get("FLASK_DEBUG")))
