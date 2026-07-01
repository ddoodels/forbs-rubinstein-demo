# FORBS Rubinstein Site

Flask prototype for FORBS on Rubinstein: atmospheric one-page main site, separate `/booking` reservation page, `/menu` menu page, and one combined `/legal` documents page.

## Run Locally

```bash
cd /Users/doodels/.openclaw/workspace/projects/forbs-site/site
python3 app.py
```

Open:

- http://127.0.0.1:5055/
- http://127.0.0.1:5055/booking
- http://127.0.0.1:5055/menu
- http://127.0.0.1:5055/legal

## Production

Set the public domain before launch so canonical links, Open Graph previews, robots, and sitemap point to the real site:

```bash
FORBS_SITE_URL=https://forbsbar.ru
gunicorn app:app --bind 127.0.0.1:5055
```

Public SEO endpoints:

- `/robots.txt`
- `/sitemap.xml`
- `/static/assets/images/meta/og-forbs.jpg`

Before DNS cutover, check the public URL with Telegram/WhatsApp preview and the Yandex/Google indexable page source.

## Deploy

This Flask app must be deployed as a Python web service, not GitHub Pages. GitHub Pages cannot run `/api/booking` or send Telegram booking requests.

### Render

The repo includes `render.yaml` for Render Blueprint deployment.

1. Create a new Blueprint/Web Service from this GitHub repo.
2. Use the default commands from `render.yaml`:
   - build: `pip install -r requirements.txt`
   - start: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. Fill secrets in Render Environment:
   - `FORBS_TELEGRAM_BOT_TOKEN`
   - `FORBS_TELEGRAM_CHAT_ID`
   - optional `FORBS_TELEGRAM_THREAD_ID`
   - legal/operator variables from the checklist below
4. Set `FORBS_SITE_URL` to the public Render/custom-domain URL.

### Vercel

Vercel can run this as a Python WSGI app. The repo includes `pyproject.toml` with:

```toml
[tool.vercel]
entrypoint = "app:app"
```

Set the same environment variables in Vercel Project Settings before using the booking form in production.

## Legal Launch Checklist

Before publishing, fill the legal environment variables so `/legal` shows the real operator/performer details:

```bash
FORBS_LEGAL_NAME=
FORBS_LEGAL_ADDRESS=
FORBS_LEGAL_INN=
FORBS_LEGAL_OGRN=
FORBS_LEGAL_EMAIL=
FORBS_PD_OPERATOR=
FORBS_PD_OPERATOR_ADDRESS=
FORBS_PD_OPERATOR_EMAIL=
```

The site currently contains the public "Кальян 1500" promo by business request. Review this copy with counsel before production publication.

## Telegram Booking

The app loads local `.env` automatically for development. For the server, set the same environment variables:

```bash
FORBS_PREVIEW_MODE=0
FORBS_TELEGRAM_BOT_TOKEN=...
FORBS_TELEGRAM_CHAT_ID=-5502097175
FORBS_TELEGRAM_THREAD_ID=...
```

`FORBS_TELEGRAM_THREAD_ID` is only needed if the chat is a forum topic.

If Telegram returns `chat not found`, open `@forbsbookingbot` and press Start for a personal chat, or add the bot to the target group and send one message there. Then run `getUpdates` to confirm the actual chat id.

## Tests

```bash
python3 -m unittest discover -s tests
```

## QA Screenshots

Local QA screenshots can be regenerated into `/tmp/forbs-qa`.
